class RecommendationPromptBuilder:

    @staticmethod
    def build(stock_name: str, matched_keywords: list[str], themes: list[str]) -> str:
        keywords_str = ", ".join(matched_keywords)
        themes_str = ", ".join(themes)
        return (
            f"다음 정보를 바탕으로 '{stock_name}' 종목을 추천하는 이유를 한국어로 2~3문장으로 자연스럽게 설명해줘.\n\n"
            f"- 종목명: {stock_name}\n"
            f"- 관련 테마: {themes_str}\n"
            f"- 매칭된 키워드: {keywords_str}\n\n"
            "투자자가 이 종목에 관심을 가져야 하는 이유를 방산·주식 시장 맥락에서 설명해줘. "
            "반드시 매칭된 키워드와 테마를 자연스럽게 포함해야 해."
        )
