import json
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.domains.agent.application.port.llm_synthesis_port import LlmSynthesisPort
from app.domains.agent.application.response.sub_agent_response import SubAgentResponse
from app.domains.agent.application.service.synthesis_prompt_builder import build_synthesis_prompt

logger = logging.getLogger(__name__)

_SYNTHESIS_MODEL = "gpt-4.1-mini"

_SYSTEM_PROMPT = """당신은 주식 종합 분석 전문가입니다.
뉴스·공시·재무 에이전트의 분석 결과를 교차 검증하여 투자자에게 실질적으로 유용한 심층 의견을 제공하세요.

분석 시 반드시 지키세요:
1. 각 에이전트의 시그널(긍정/부정/중립)과 신뢰도를 종합하고, 서로 상충하는 신호가 있으면 그 이유를 설명하세요.
2. 재무수치(ROE, ROA, 부채비율, 매출, 영업이익 등)가 제공된 경우 구체적인 수치를 언급하세요.
3. 긍정 요인과 위험 요인을 균형 있게 서술하세요.
4. 핵심 포인트는 "수치 또는 사실 근거 + 투자 판단 의미" 형태로 작성하세요.
5. 데이터가 없는 에이전트는 제외하고 있는 정보만으로 판단하세요.

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요:
{{"summary": "300자 이내 종합 투자 의견", "key_points": ["근거 기반 포인트 1", "근거 기반 포인트 2", "근거 기반 포인트 3", "근거 기반 포인트 4"]}}"""


class OpenAISynthesisClient(LlmSynthesisPort):
    def __init__(self, api_key: str, model: str = _SYNTHESIS_MODEL) -> None:
        llm = ChatOpenAI(model=model, api_key=api_key, temperature=0.3)
        prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("human", "{context}"),
        ])
        self._chain = prompt | llm | StrOutputParser()

    async def synthesize(
        self,
        ticker: str,
        query: str,
        sub_results: list[SubAgentResponse],
    ) -> tuple[str, list[str]]:
        context = build_synthesis_prompt(ticker, query, sub_results)
        try:
            raw = await self._chain.ainvoke({"context": context})
            parsed = json.loads(raw)
            summary = parsed.get("summary", "")
            key_points = parsed.get("key_points", [])
            if summary:
                return summary, key_points
        except Exception as exc:
            logger.warning("LLM synthesis failed, using fallback: %s", exc)

        # Fallback: 서브에이전트 요약 단순 연결
        summaries = [r.summary for r in sub_results if r.is_success() and r.summary]
        return " ".join(summaries) or "분석 결과를 생성하지 못했습니다.", []
