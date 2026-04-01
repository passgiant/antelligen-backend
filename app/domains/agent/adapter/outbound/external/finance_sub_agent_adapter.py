import logging
import time

from app.common.exception.app_exception import AppException
from app.domains.agent.application.port.finance_agent_port import FinanceAgentPort
from app.domains.agent.application.request.finance_analysis_request import FinanceAnalysisRequest
from app.domains.agent.application.response.sub_agent_response import SubAgentResponse
from app.domains.agent.application.usecase.analyze_finance_agent_usecase import (
    AnalyzeFinanceAgentUseCase,
)
from app.domains.agent.adapter.outbound.external.langgraph_finance_agent_provider import (
    LangGraphFinanceAgentProvider,
)
from app.domains.stock.adapter.outbound.external.opendart_financial_data_provider import (
    OpenDartFinancialDataProvider,
)
from app.domains.stock.adapter.outbound.external.openai_stock_embedding_generator import (
    OpenAIStockEmbeddingGenerator,
)
from app.domains.stock.adapter.outbound.external.serp_stock_data_collector import (
    SerpStockDataCollector,
)
from app.domains.stock.adapter.outbound.persistence.corp_code_repository_impl import (
    CorpCodeRepositoryImpl,
)
from app.domains.stock.adapter.outbound.persistence.stock_repository_impl import (
    StockRepositoryImpl,
)
from app.domains.stock.adapter.outbound.persistence.stock_vector_repository_impl import (
    StockVectorRepositoryImpl,
)
from app.domains.stock.application.usecase.collect_stock_data_usecase import (
    CollectStockDataUseCase,
)
from app.domains.stock.application.usecase.fetch_dart_financial_ratios_usecase import (
    FetchDartFinancialRatiosUseCase,
)
from app.domains.stock.application.usecase.get_stored_stock_data_usecase import (
    GetStoredStockDataUseCase,
)
from app.domains.stock.infrastructure.mapper.serp_stock_data_standardizer import (
    SerpStockDataStandardizer,
)
from app.domains.stock.infrastructure.mapper.simple_stock_document_chunker import (
    SimpleStockDocumentChunker,
)
from app.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)


class FinanceSubAgentAdapter(FinanceAgentPort):
    """재무 분석 UseCase를 호출하는 아웃바운드 어댑터.

    벡터 DB에 데이터가 없으면 자동으로 수집 후 재시도한다.
    """

    async def analyze(self, ticker: str, query: str) -> SubAgentResponse:
        start = time.monotonic()
        try:
            settings = get_settings()
            stock_repository = StockRepositoryImpl()
            stock_vector_repository = StockVectorRepositoryImpl()

            get_stored_stock_data_usecase = GetStoredStockDataUseCase(
                stock_repository=stock_repository,
                stock_vector_repository=stock_vector_repository,
            )
            finance_provider = LangGraphFinanceAgentProvider(
                api_key=settings.openai_api_key,
                chat_model=settings.openai_finance_agent_model,
                embedding_model=settings.openai_embedding_model,
                top_k=settings.finance_rag_top_k,
                langsmith_tracing=settings.langsmith_tracing,
                langsmith_api_key=settings.langsmith_api_key,
                langsmith_project=settings.langsmith_project,
                langsmith_endpoint=settings.langsmith_endpoint,
            )
            usecase = AnalyzeFinanceAgentUseCase(
                stock_repository=stock_repository,
                get_stored_stock_data_usecase=get_stored_stock_data_usecase,
                finance_agent_provider=finance_provider,
            )

            request = FinanceAnalysisRequest(ticker=ticker, query=query)
            try:
                result = await usecase.execute(request)
            except AppException as e:
                if e.status_code != 404:
                    raise
                # 벡터 DB에 데이터 없음 → 자동 수집 후 재시도
                logger.info("[FinanceSubAgent] No stored data for %s — auto-collecting", ticker)
                await self._collect(ticker, settings)
                result = await usecase.execute(request)

            elapsed = int((time.monotonic() - start) * 1000)
            if result.agent_results:
                return result.agent_results[0]
            return SubAgentResponse.no_data("finance", elapsed)

        except Exception as exc:
            elapsed = int((time.monotonic() - start) * 1000)
            return SubAgentResponse.error("finance", str(exc), elapsed)

    @staticmethod
    async def _collect(ticker: str, settings) -> None:
        dart_financial_ratios_usecase = None
        if settings.open_dart_api_key:
            dart_financial_ratios_usecase = FetchDartFinancialRatiosUseCase(
                corp_code_repository=CorpCodeRepositoryImpl(),
                dart_financial_data_provider=OpenDartFinancialDataProvider(
                    api_key=settings.open_dart_api_key
                ),
            )
        collect_usecase = CollectStockDataUseCase(
            stock_repository=StockRepositoryImpl(),
            stock_data_collector=SerpStockDataCollector(api_key=settings.serp_api_key),
            stock_data_standardizer=SerpStockDataStandardizer(),
            stock_document_chunker=SimpleStockDocumentChunker(),
            stock_embedding_generator=OpenAIStockEmbeddingGenerator(
                api_key=settings.openai_api_key,
                model=settings.openai_embedding_model,
            ),
            stock_vector_repository=StockVectorRepositoryImpl(),
            dart_financial_ratios_usecase=dart_financial_ratios_usecase,
        )
        await collect_usecase.execute(ticker)
