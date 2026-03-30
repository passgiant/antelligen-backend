from pydantic import BaseModel


class StockRecommendationItem(BaseModel):
    name: str
    code: str
    themes: list[str]
    matched_keywords: list[str]
    score: int
    reason: str


class StockRecommendationResponse(BaseModel):
    total: int
    items: list[StockRecommendationItem]
