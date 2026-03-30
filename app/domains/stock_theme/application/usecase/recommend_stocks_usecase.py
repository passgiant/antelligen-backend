import asyncio

from app.domains.stock_theme.application.port.out.stock_theme_repository_port import StockThemeRepositoryPort
from app.domains.stock_theme.application.request.recommend_stocks_request import RecommendStocksRequest
from app.domains.stock_theme.application.response.stock_recommendation_response import (
    StockRecommendationItem,
    StockRecommendationResponse,
)
from app.domains.stock_theme.domain.service.recommendation_prompt_builder import RecommendationPromptBuilder
from app.domains.stock_theme.domain.service.stock_recommender import StockRecommender
from app.infrastructure.external.llm_client_port import LlmClientPort


class RecommendStocksUseCase:
    def __init__(self, repository: StockThemeRepositoryPort, llm: LlmClientPort):
        self._repository = repository
        self._llm = llm

    async def execute(self, request: RecommendStocksRequest) -> StockRecommendationResponse:
        stock_themes = await self._repository.find_all()

        keyword_frequencies = {item.keyword: item.count for item in request.keywords}
        recommendations = StockRecommender.recommend(stock_themes, keyword_frequencies)

        async def build_item(rec) -> StockRecommendationItem:
            prompt = RecommendationPromptBuilder.build(
                stock_name=rec.stock.name,
                matched_keywords=rec.matched_keywords,
                themes=rec.stock.themes,
            )
            reason = await self._llm.generate(prompt)
            return StockRecommendationItem(
                name=rec.stock.name,
                code=rec.stock.code,
                themes=rec.stock.themes,
                matched_keywords=rec.matched_keywords,
                score=rec.score,
                reason=reason,
            )

        items = await asyncio.gather(*[build_item(rec) for rec in recommendations])
        return StockRecommendationResponse(total=len(items), items=list(items))
