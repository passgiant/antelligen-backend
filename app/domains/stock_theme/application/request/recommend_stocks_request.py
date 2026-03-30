from pydantic import BaseModel


class KeywordFrequencyItem(BaseModel):
    keyword: str
    count: int


class RecommendStocksRequest(BaseModel):
    keywords: list[KeywordFrequencyItem]
