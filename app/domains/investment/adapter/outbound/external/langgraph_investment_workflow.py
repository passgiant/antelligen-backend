"""
LangGraph 기반 투자 판단 멀티 에이전트 워크플로우.

흐름:
    START
      └→ orchestrator ──────────────────────────────────────────────────┐
              ↑           (conditional routing by next_agent)            │
              │      ┌── "retrieval"  → retrieval_agent                  │
              └──────┤── "analysis"   → analysis_agent                   │
                     ├── "synthesis"  → synthesis_agent                  │
                     └── "end"        → END ←──────────────────────────  ┘

Orchestrator 동작 순서:
  1) 첫 호출 시 QueryParser로 사용자 질문을 파싱하여 parsed_query를 State에 기록한다.
  2) State 상태에 따라 다음 에이전트를 동적으로 결정한다.
  3) 최대 반복 횟수(max_iterations)를 초과하면 강제 종료한다.
"""

from typing import Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.domains.investment.adapter.outbound.external.llm_query_parser import LLMQueryParser
from app.domains.investment.application.port.investment_workflow_port import InvestmentWorkflowPort
from app.domains.investment.domain.value_object.parsed_query import ParsedQuery

MAX_ITERATIONS = 10


# ──────────────────────────────────────────────
# 공유 State 정의
# ──────────────────────────────────────────────

class InvestmentAgentState(TypedDict, total=False):
    user_id: str
    user_query: str

    # Query Parser 결과 (Orchestrator 첫 호출 시 기록)
    parsed_query: Optional[ParsedQuery]

    # Orchestrator 제어
    next_agent: str       # "retrieval" | "analysis" | "synthesis" | "end"
    iteration_count: int
    max_iterations: int

    # 각 에이전트 결과
    retrieved_data: list[dict[str, Any]]   # Retrieval Agent 결과
    analysis_insights: dict[str, Any]      # Analysis Agent 결과
    final_response: str                    # Synthesis Agent 최종 응답


# ──────────────────────────────────────────────
# 워크플로우 클래스 (노드는 인스턴스 메서드)
# ──────────────────────────────────────────────

class LangGraphInvestmentWorkflow(InvestmentWorkflowPort):
    """LangGraph 기반 투자 판단 워크플로우 Port 구현체."""

    def __init__(
        self,
        *,
        api_key: str,
        query_parser_model: str = "gpt-5-mini",
        max_iterations: int = MAX_ITERATIONS,
    ) -> None:
        self._query_parser = LLMQueryParser(api_key=api_key, model=query_parser_model)
        self._max_iterations = max_iterations
        self._graph = self._build_graph()
        print(f"[LangGraphInvestmentWorkflow] 그래프 빌드 완료 | max_iterations={max_iterations}")

    # ── 단일 진입점 ───────────────────────────

    async def run(self, *, user_id: str, query: str) -> dict:
        """워크플로우를 실행하고 최종 State를 반환한다."""
        print(f"\n[LangGraphInvestmentWorkflow] run_agent_workflow 진입 "
              f"| user_id={user_id} | query={query!r}")

        initial_state: InvestmentAgentState = {
            "user_id": user_id,
            "user_query": query,
            "iteration_count": 0,
            "max_iterations": self._max_iterations,
        }

        # LLM 호출 실패 등의 예외는 상위로 명확하게 전파된다 (내부 catch 없음)
        final_state = await self._graph.ainvoke(initial_state)

        print(f"\n[LangGraphInvestmentWorkflow] 워크플로우 종료 "
              f"| total_iterations={final_state.get('iteration_count', 0)}")
        return final_state

    # ── 그래프 빌드 ───────────────────────────

    def _build_graph(self):
        graph = StateGraph(InvestmentAgentState)

        graph.add_node("orchestrator", self._orchestrator_node)
        graph.add_node("retrieval", self._retrieval_node)
        graph.add_node("analysis", self._analysis_node)
        graph.add_node("synthesis", self._synthesis_node)

        graph.add_edge(START, "orchestrator")

        graph.add_conditional_edges(
            "orchestrator",
            self._route_from_orchestrator,
            {
                "retrieval": "retrieval",
                "analysis": "analysis",
                "synthesis": "synthesis",
                "end": END,
            },
        )

        graph.add_edge("retrieval", "orchestrator")
        graph.add_edge("analysis", "orchestrator")
        graph.add_edge("synthesis", "orchestrator")

        return graph.compile()

    # ── 라우팅 함수 ───────────────────────────

    def _route_from_orchestrator(self, state: InvestmentAgentState) -> str:
        next_agent = state.get("next_agent", "end")
        print(f"[Router] 조건부 엣지 → {next_agent}")
        return next_agent

    # ── 노드 구현 ─────────────────────────────

    async def _orchestrator_node(self, state: InvestmentAgentState) -> InvestmentAgentState:
        """
        현재 State를 기반으로 다음 실행 Agent를 결정한다.

        첫 호출 시 QueryParser로 질문을 파싱한다.
        이후 State 완성도에 따라 retrieval → analysis → synthesis → end 순으로 라우팅한다.
        """
        iteration = state.get("iteration_count", 0) + 1
        max_iter = state.get("max_iterations", MAX_ITERATIONS)

        print(f"\n[Orchestrator] ===== 반복 #{iteration} / 최대 {max_iter} =====")
        print(f"[Orchestrator] 사용자 질의: {state.get('user_query')!r}")
        print(
            f"[Orchestrator] 현재 State 요약 → "
            f"parsed_query={'있음' if state.get('parsed_query') else '없음'} | "
            f"retrieved_data={'있음' if state.get('retrieved_data') else '없음'} | "
            f"analysis_insights={'있음' if state.get('analysis_insights') else '없음'} | "
            f"final_response={'있음' if state.get('final_response') else '없음'}"
        )

        updates: InvestmentAgentState = {"iteration_count": iteration}

        # 최대 반복 초과 → 강제 종료
        if iteration > max_iter:
            print(f"[Orchestrator] 최대 반복 횟수 초과 → 워크플로우 강제 종료")
            updates["next_agent"] = "end"
            return updates

        # 첫 호출: Query Parser로 질문 파싱 후 State에 기록
        if not state.get("parsed_query"):
            print(f"[Orchestrator] Query Parser 호출 중...")
            # QueryParseError 등의 예외는 상위로 명확하게 전파된다
            parsed = await self._query_parser.parse(state.get("user_query", ""))
            updates["parsed_query"] = parsed
            print(
                f"[Orchestrator] 파싱 결과 State 기록 완료 → "
                f"company={parsed['company']!r} | "
                f"intent={parsed['intent']!r} | "
                f"required_data={parsed['required_data']}"
            )

        # 상태 기반 동적 라우팅 결정
        if not state.get("retrieved_data"):
            next_agent = "retrieval"
        elif not state.get("analysis_insights"):
            next_agent = "analysis"
        elif not state.get("final_response"):
            next_agent = "synthesis"
        else:
            next_agent = "end"

        print(f"[Orchestrator] 다음 실행 에이전트 → {next_agent}")
        updates["next_agent"] = next_agent
        return updates

    async def _retrieval_node(self, state: InvestmentAgentState) -> InvestmentAgentState:
        """
        투자 관련 원천 데이터를 수집하여 State에 적재한다.
        parsed_query의 company와 required_data를 활용하여 수집 범위를 결정한다.

        TODO: 실제 외부 데이터 소스 연동 (SERP API, YouTube Data API v3, DB 기사 조회)
        """
        parsed: ParsedQuery = state.get("parsed_query") or {}
        company = parsed.get("company") or "전체 시장"
        required_data = parsed.get("required_data", [])

        print(f"\n[RetrievalAgent] 데이터 수집 시작 | company={company!r} | required_data={required_data}")
        print(f"[RetrievalAgent] 수집 소스: SERP 뉴스 검색 / 저장된 기사 / YouTube API")

        # TODO: 실제 SERP 뉴스 검색 호출
        # TODO: 실제 YouTube API 검색 호출
        # TODO: DB에서 저장된 기사 조회

        retrieved_data = [
            {"source": "news", "content": f"[STUB] {company} 관련 뉴스 데이터"},
            {"source": "youtube", "content": f"[STUB] {company} 관련 YouTube 영상 정보"},
            {"source": "saved_article", "content": f"[STUB] {company} 관련 저장된 기사"},
        ]

        print(f"[RetrievalAgent] 수집 완료 | 항목 수: {len(retrieved_data)}")
        for item in retrieved_data:
            print(f"[RetrievalAgent]   - [{item['source']}] {item['content']}")

        return {"retrieved_data": retrieved_data}

    async def _analysis_node(self, state: InvestmentAgentState) -> InvestmentAgentState:
        """
        수집된 데이터를 기반으로 종목 전망, 리스크, 투자 포인트를 분석하여
        인사이트를 생성하고 State에 기록한다.

        TODO: LLM 호출을 통한 실제 분석 로직 구현
        """
        parsed: ParsedQuery = state.get("parsed_query") or {}
        company = parsed.get("company") or "전체 시장"
        intent = parsed.get("intent", "기타")
        retrieved_data = state.get("retrieved_data", [])

        print(f"\n[AnalysisAgent] 분석 시작 | company={company!r} | intent={intent!r}")
        print(f"[AnalysisAgent] 입력 데이터 항목 수: {len(retrieved_data)}")

        # TODO: LLM 호출 — 종목 전망 / 리스크 / 투자 포인트 분석
        # LLM 호출 실패 시 예외를 상위로 전파 (try/except 없이 직접 raise)

        analysis_insights = {
            "outlook": f"[STUB] {company}에 대한 종목 전망 분석 결과",
            "risk": f"[STUB] {company}에 대한 리스크 분석 결과",
            "investment_points": [
                f"[STUB] 투자 포인트 1",
                f"[STUB] 투자 포인트 2",
                f"[STUB] 투자 포인트 3",
            ],
        }

        print(f"[AnalysisAgent] 분석 완료")
        print(f"[AnalysisAgent]   - 전망: {analysis_insights['outlook']}")
        print(f"[AnalysisAgent]   - 리스크: {analysis_insights['risk']}")
        print(f"[AnalysisAgent]   - 투자 포인트: {len(analysis_insights['investment_points'])}개")

        return {"analysis_insights": analysis_insights}

    async def _synthesis_node(self, state: InvestmentAgentState) -> InvestmentAgentState:
        """
        분석 결과를 기반으로 사용자 질문에 대한 투자 판단 참고 응답을 생성한다.
        응답에는 투자 권유가 아닌 정보 제공임을 명시하는 면책 문구가 포함된다.

        TODO: LLM 호출을 통한 실제 종합 응답 생성 로직 구현
        """
        query = state.get("user_query", "")
        analysis_insights = state.get("analysis_insights", {})
        parsed: ParsedQuery = state.get("parsed_query") or {}

        print(f"\n[SynthesisAgent] 응답 종합 시작 | query={query!r}")
        print(f"[SynthesisAgent] 분석 인사이트 수신: {list(analysis_insights.keys())}")
        print(f"[SynthesisAgent] 파싱된 의도: intent={parsed.get('intent')!r}")

        # TODO: LLM 호출 — 분석 인사이트를 바탕으로 자연어 응답 생성
        # LLM 호출 실패 시 예외를 상위로 전파 (try/except 없이 직접 raise)

        DISCLAIMER = (
            "\n\n※ 본 응답은 투자 권유가 아닌 정보 제공 목적으로만 활용되어야 하며, "
            "투자 판단 및 그에 따른 결과는 전적으로 투자자 본인의 책임입니다."
        )

        final_response = (
            f"[STUB] '{query}'에 대한 투자 판단 참고 응답입니다.\n"
            f"전망: {analysis_insights.get('outlook', '')}\n"
            f"리스크: {analysis_insights.get('risk', '')}"
            + DISCLAIMER
        )

        print(f"[SynthesisAgent] 응답 종합 완료 | 응답 길이: {len(final_response)}자")
        return {"final_response": final_response}
