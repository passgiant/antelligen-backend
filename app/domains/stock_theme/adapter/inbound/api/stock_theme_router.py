from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.stock_theme.adapter.outbound.persistence.stock_theme_repository_impl import StockThemeRepositoryImpl
from app.domains.stock_theme.application.request.recommend_stocks_request import RecommendStocksRequest
from app.domains.stock_theme.application.response.stock_recommendation_response import StockRecommendationResponse
from app.domains.stock_theme.application.response.stock_theme_response import StockThemeListResponse
from app.domains.stock_theme.application.usecase.get_stock_themes_usecase import GetStockThemesUseCase
from app.domains.stock_theme.application.usecase.recommend_stocks_usecase import RecommendStocksUseCase
from app.infrastructure.database.database import get_db
from app.infrastructure.external.openai_llm_client import get_openai_llm_client

router = APIRouter(prefix="/stock-theme", tags=["stock-theme"])


@router.get("", response_model=StockThemeListResponse)
async def get_stock_themes(db: AsyncSession = Depends(get_db)):
    repository = StockThemeRepositoryImpl(db)
    use_case = GetStockThemesUseCase(repository)
    return await use_case.execute()


@router.post("/recommend", response_model=StockRecommendationResponse)
async def recommend_stocks(request: RecommendStocksRequest, db: AsyncSession = Depends(get_db)):
    repository = StockThemeRepositoryImpl(db)
    llm = get_openai_llm_client()
    use_case = RecommendStocksUseCase(repository, llm)
    return await use_case.execute(request)
