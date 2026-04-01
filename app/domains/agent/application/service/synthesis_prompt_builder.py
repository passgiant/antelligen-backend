from app.domains.agent.application.response.sub_agent_response import SubAgentResponse

_SIGNAL_LABEL = {
    "bullish": "긍정(매수)",
    "bearish": "부정(매도)",
    "neutral": "중립",
}

_AGENT_LABEL = {
    "news": "뉴스",
    "disclosure": "공시",
    "finance": "재무",
}

_FINANCE_FIELDS = [
    ("stock_name", "종목명"),
    ("fiscal_year", "기준연도"),
    ("current_price", "현재주가"),
    ("roe", "ROE(%)"),
    ("roa", "ROA(%)"),
    ("debt_ratio", "부채비율(%)"),
    ("sales", "매출액"),
    ("operating_income", "영업이익"),
    ("net_income", "당기순이익"),
]


def build_synthesis_prompt(ticker: str, query: str, sub_results: list[SubAgentResponse]) -> str:
    lines = [f"[종목코드: {ticker}] 사용자 질문: {query}\n"]

    for r in sub_results:
        agent_label = _AGENT_LABEL.get(r.agent_name, r.agent_name)

        if not r.is_success() or r.signal is None:
            lines.append(f"[{agent_label} 에이전트] 데이터 없음 또는 오류\n")
            continue

        signal_label = _SIGNAL_LABEL.get(r.signal.value, r.signal.value)
        confidence_str = f"{r.confidence:.0%}" if r.confidence is not None else "N/A"
        key_points_str = "\n  ".join(f"• {p}" for p in r.key_points) if r.key_points else "없음"

        block = (
            f"[{agent_label} 에이전트] 시그널={signal_label}, 신뢰도={confidence_str}\n"
            f"  요약: {r.summary or '없음'}\n"
            f"  핵심포인트:\n  {key_points_str}"
        )

        # 재무 에이전트는 수치 데이터를 추가로 포함
        if r.agent_name == "finance" and r.data:
            finance_lines = []
            for field, label in _FINANCE_FIELDS:
                val = r.data.get(field)
                if val is not None:
                    finance_lines.append(f"{label}: {val}")
            if finance_lines:
                block += "\n  재무수치: " + ", ".join(finance_lines)

        lines.append(block)

    return "\n".join(lines)
