from app.domains.stock_theme.application.port.out.stock_theme_repository_port import StockThemeRepositoryPort
from app.domains.stock_theme.application.response.stock_theme_response import StockThemeItem, StockThemeListResponse


class GetStockThemesUseCase:
    def __init__(self, repository: StockThemeRepositoryPort):
        self._repository = repository

    async def execute(self) -> StockThemeListResponse:
        stock_themes = await self._repository.find_all()
        items = [
            StockThemeItem(id=st.id, name=st.name, code=st.code, themes=st.themes)
            for st in stock_themes
        ]
        return StockThemeListResponse(total=len(items), items=items)
