from collections import Counter

from app.domains.market_video.domain.service.synonym_table import SYNONYM_MAP


class NounExtractor:

    @staticmethod
    def merge_synonyms(nouns: list[str]) -> list[str]:
        """동의어 매핑 테이블을 기반으로 각 명사를 대표어로 치환한다."""
        return [SYNONYM_MAP.get(noun, noun) for noun in nouns]

    @staticmethod
    def count_frequencies(nouns: list[str]) -> list[tuple[str, int]]:
        if not nouns:
            return []
        return Counter(nouns).most_common()
