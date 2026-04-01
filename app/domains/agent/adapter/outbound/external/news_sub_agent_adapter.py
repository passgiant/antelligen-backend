import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.agent.application.port.news_agent_port import NewsAgentPort
from app.domains.agent.application.response.sub_agent_response import AgentStatus, SubAgentResponse
from app.domains.news.adapter.outbound.external.naver_news_client import NaverNewsClient
from app.domains.news.adapter.outbound.external.openai_news_signal_adapter import OpenAINewsSignalAdapter
from app.domains.news.adapter.outbound.persistence.collected_news_repository_impl import CollectedNewsRepositoryImpl
from app.domains.news.application.usecase.analyze_news_signal_usecase import AnalyzeNewsSignalUseCase, TICKER_TO_KEYWORDS
from app.domains.news.application.usecase.collect_naver_news_usecase import CollectNaverNewsUseCase
from app.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)


class NewsSubAgentAdapter(NewsAgentPort):
    def __init__(self, db: AsyncSession, api_key: str):
        self._db = db
        self._api_key = api_key

    async def analyze(self, ticker: str, query: str) -> SubAgentResponse:
        repository = CollectedNewsRepositoryImpl(self._db)
        analysis_port = OpenAINewsSignalAdapter(api_key=self._api_key)
        usecase = AnalyzeNewsSignalUseCase(repository=repository, analysis_port=analysis_port)

        result = await usecase.execute(ticker)
        if result.status != AgentStatus.NO_DATA:
            return result

        # DB에 해당 종목 뉴스 없음 → 자동 수집 후 재시도
        keywords = TICKER_TO_KEYWORDS.get(ticker)
        if not keywords:
            return result

        logger.info("[NewsSubAgent] No news for %s — auto-collecting keywords: %s", ticker, keywords)
        await self._collect(keywords)
        return await usecase.execute(ticker)

    async def _collect(self, keywords: list[str]) -> None:
        settings = get_settings()
        collect_usecase = CollectNaverNewsUseCase(
            naver_news_port=NaverNewsClient(
                client_id=settings.naver_client_id,
                client_secret=settings.naver_client_secret,
            ),
            repository=CollectedNewsRepositoryImpl(self._db),
        )
        await collect_usecase.execute(keywords=keywords)
