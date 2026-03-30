from pydantic import BaseModel


class StockThemeItem(BaseModel):
    id: int
    name: str
    code: str
    themes: list[str]


class StockThemeListResponse(BaseModel):
    total: int
    items: list[StockThemeItem]
