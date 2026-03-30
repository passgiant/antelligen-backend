from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.stock_theme.application.port.out.stock_theme_repository_port import StockThemeRepositoryPort
from app.domains.stock_theme.domain.entity.stock_theme import StockTheme
from app.domains.stock_theme.infrastructure.mapper.stock_theme_mapper import StockThemeMapper
from app.domains.stock_theme.infrastructure.orm.stock_theme_orm import StockThemeOrm


class StockThemeRepositoryImpl(StockThemeRepositoryPort):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def save_all(self, stock_themes: list[StockTheme]) -> None:
        for entity in stock_themes:
            self._db.add(StockThemeMapper.to_orm(entity))
        await self._db.commit()

    async def find_all(self) -> list[StockTheme]:
        stmt = select(StockThemeOrm)
        result = await self._db.execute(stmt)
        return [StockThemeMapper.to_entity(orm) for orm in result.scalars().all()]

    async def exists_any(self) -> bool:
        stmt = select(func.count()).select_from(StockThemeOrm)
        result = await self._db.execute(stmt)
        return result.scalar() > 0
