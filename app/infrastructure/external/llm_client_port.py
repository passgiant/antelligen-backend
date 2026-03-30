from abc import ABC, abstractmethod


class LlmClientPort(ABC):

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """프롬프트를 입력받아 LLM이 생성한 텍스트를 반환한다."""
        pass
