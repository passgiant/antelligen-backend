from dataclasses import dataclass


@dataclass
class StockTheme:
    id: int | None
    name: str        # 종목명 (예: "한화에어로스페이스")
    code: str        # 종목코드 (예: "012450")
    themes: list[str]  # 관련 테마 키워드 (예: ["전투기", "미사일"])
