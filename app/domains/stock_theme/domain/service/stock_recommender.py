from dataclasses import dataclass

from app.domains.stock_theme.domain.entity.stock_theme import StockTheme


@dataclass
class StockRecommendation:
    stock: StockTheme
    matched_keywords: list[str]
    score: int


class StockRecommender:

    @staticmethod
    def recommend(
        stock_themes: list[StockTheme],
        keyword_frequencies: dict[str, int],
    ) -> list[StockRecommendation]:
        """
        키워드 빈도수 딕셔너리와 종목 테마를 매칭하여 관련성 점수 순으로 정렬된 추천 결과를 반환한다.
        score = 매칭된 키워드 빈도수의 합
        """
        results: list[StockRecommendation] = []

        for stock in stock_themes:
            matched = [kw for kw in stock.themes if kw in keyword_frequencies]
            if not matched:
                continue
            score = sum(keyword_frequencies[kw] for kw in matched)
            results.append(StockRecommendation(stock=stock, matched_keywords=matched, score=score))

        results.sort(key=lambda r: r.score, reverse=True)
        return results
