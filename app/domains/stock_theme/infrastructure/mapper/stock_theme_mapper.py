from app.domains.stock_theme.domain.entity.stock_theme import StockTheme
from app.domains.stock_theme.infrastructure.orm.stock_theme_orm import StockThemeOrm


class StockThemeMapper:

    @staticmethod
    def to_entity(orm: StockThemeOrm) -> StockTheme:
        return StockTheme(
            id=orm.id,
            name=orm.name,
            code=orm.code,
            themes=orm.themes,
        )

    @staticmethod
    def to_orm(entity: StockTheme) -> StockThemeOrm:
        return StockThemeOrm(
            name=entity.name,
            code=entity.code,
            themes=entity.themes,
        )
