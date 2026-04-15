"""
LLM 기반 투자 질문 파서.

OpenAI ChatCompletion을 호출하여 자연어 투자 질문에서
company / intent / required_data 를 추출한다.

재시도 정책:
- LLM 응답이 JSON 형식이 아니거나 필수 키가 누락된 경우 최대 MAX_RETRIES회 재시도한다.
- 재시도 후에도 실패하면 QueryParseError를 상위로 전파한다.
"""

import json

from langchain_openai import ChatOpenAI

from app.domains.investment.application.port.query_parser_port import QueryParserPort
from app.domains.investment.domain.value_object.parsed_query import ParsedQuery, QueryParseError

MAX_RETRIES = 2

_SYSTEM_PROMPT = """당신은 한국 주식 투자 질문을 구조화된 데이터로 파싱하는 전문가입니다.

사용자의 투자 질문을 분석하여 반드시 아래 JSON 형식으로만 응답하세요 (마크다운, 코드블록, 기타 텍스트 절대 금지):
{
  "company": "<종목명 또는 티커, 특정 종목이 없으면 null>",
  "intent": "<매수판단|매도판단|리스크분석|전망조회|테마분석|기타 중 하나>",
  "required_data": ["<필요한 데이터 유형>", ...]
}

required_data 항목 예시: "뉴스", "재무데이터", "시장데이터", "공시정보", "유튜브영상", "섹터정보"

규칙:
- 특정 종목명이나 티커가 식별되지 않으면 company는 반드시 null
- intent는 위 6가지 중 하나만 선택
- required_data는 1개 이상 반드시 포함
- 의미 없는 입력(투자와 무관한 질문)이면 intent를 "기타"로 설정"""


class LLMQueryParser(QueryParserPort):
    """OpenAI LLM을 사용하여 투자 질문을 파싱하는 어댑터."""

    def __init__(self, *, api_key: str, model: str = "gpt-5-mini") -> None:
        self._llm = ChatOpenAI(api_key=api_key, model=model)
        self._model = model
        print(f"[LLMQueryParser] 초기화 완료 | model={model}")

    async def parse(self, query: str) -> ParsedQuery:
        """
        투자 질문을 파싱한다. 실패 시 MAX_RETRIES회 재시도 후 QueryParseError를 전파한다.
        """
        print(f"[LLMQueryParser] 파싱 시작 | query={query!r}")
        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 2):  # 1회 기본 + MAX_RETRIES 재시도
            print(f"[LLMQueryParser] LLM 호출 시도 #{attempt}")
            try:
                response = await self._llm.ainvoke(
                    [
                        ("system", _SYSTEM_PROMPT),
                        ("human", query),
                    ]
                )
                raw = response.content.strip()
                print(f"[LLMQueryParser] LLM 응답 수신 | raw={raw[:200]!r}")

                parsed = self._parse_response(raw)
                print(
                    f"[LLMQueryParser] 파싱 성공 | "
                    f"company={parsed['company']!r} | "
                    f"intent={parsed['intent']!r} | "
                    f"required_data={parsed['required_data']}"
                )
                return parsed

            except QueryParseError as e:
                print(f"[LLMQueryParser] 파싱 실패 (시도 #{attempt}): {e}")
                last_error = e
                # 재시도 남아있으면 계속
                if attempt <= MAX_RETRIES:
                    print(f"[LLMQueryParser] 재시도 중... ({attempt}/{MAX_RETRIES})")
                    continue

            except Exception as e:
                # LLM 네트워크 오류 등 — 즉시 상위로 전파
                print(f"[LLMQueryParser] LLM 호출 오류: {e}")
                raise

        raise QueryParseError(
            f"투자 질문 파싱에 {MAX_RETRIES + 1}회 모두 실패했습니다. "
            f"마지막 오류: {last_error}"
        ) from last_error

    def _parse_response(self, raw: str) -> ParsedQuery:
        """LLM 텍스트 응답을 ParsedQuery로 변환한다."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise QueryParseError(f"LLM 응답이 유효한 JSON이 아닙니다: {e}") from e

        if not isinstance(data, dict):
            raise QueryParseError(f"LLM 응답이 dict가 아닙니다: {type(data)}")

        if "intent" not in data:
            raise QueryParseError(f"LLM 응답에 'intent' 키가 없습니다: {data}")

        if "required_data" not in data or not isinstance(data["required_data"], list):
            raise QueryParseError(f"LLM 응답에 'required_data' 리스트가 없습니다: {data}")

        if len(data["required_data"]) == 0:
            raise QueryParseError("required_data가 비어 있습니다.")

        return ParsedQuery(
            company=data.get("company"),  # null → None 처리 포함
            intent=str(data["intent"]),
            required_data=[str(item) for item in data["required_data"]],
        )
