from openai import OpenAI

from app.common.exception.app_exception import AppException
from app.domains.stock.application.port.stock_embedding_generator import (
    StockEmbeddingGenerator,
)


class OpenAIStockEmbeddingGenerator(StockEmbeddingGenerator):
    def __init__(self, api_key: str, model: str):
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(self, text: str) -> list[float]:
        normalized_text = " ".join(text.split())
        if not normalized_text:
            return []

        try:
            response = self._client.embeddings.create(
                model=self._model,
                input=normalized_text,
            )
        except Exception as exc:
            raise AppException(
                status_code=502,
                message=f"OpenAI 임베딩 생성 중 오류가 발생했습니다: {str(exc)}",
            ) from exc

        if not response.data:
            raise AppException(
                status_code=502,
                message="OpenAI 임베딩 응답이 비어 있습니다.",
            )

        return response.data[0].embedding
