# 메인 에이전트 (통합 분석 에이전트) 개발 문서

## 개요

뉴스 · 공시 · 재무 서브에이전트를 **병렬 호출**하여 종합 투자 시그널과 LLM 기반 분석 요약을 반환하는 오케스트레이터 에이전트입니다.

---

## 아키텍처 개요

```
[POST /api/v1/agent/query]
        │
        ▼
ProcessAgentQueryUseCase
        │
        ├─ PostgreSQL 캐시 확인 (1시간 이내 결과 재사용)
        │
        ├─ asyncio.gather() ──────────────────────────────────┐
        │       ├─ NewsSubAgentAdapter (뉴스)                  │
        │       ├─ DisclosureSubAgentAdapter (공시)            │ 병렬
        │       └─ FinanceSubAgentAdapter (재무)               │
        │                                                     ◄┘
        ├─ 시그널 가중 집계 (bullish/bearish/neutral + confidence)
        │
        ├─ OpenAISynthesisClient → LLM 종합 요약 생성
        │
        ├─ IntegratedAnalysisRepositoryImpl.save() → PostgreSQL 저장
        │
        └─ AgentQueryResponse 반환
```

### 레이어별 파일 위치

| 레이어 | 파일 |
|--------|------|
| **Inbound Adapter** | `adapter/inbound/api/agent_router.py` |
| **UseCase** | `application/usecase/process_agent_query_usecase.py` |
| **Ports** | `application/port/news_agent_port.py` |
| | `application/port/disclosure_agent_port.py` |
| | `application/port/finance_agent_port.py` |
| | `application/port/llm_synthesis_port.py` |
| | `application/port/integrated_analysis_repository_port.py` |
| **Response DTO** | `application/response/integrated_analysis_response.py` |
| | `application/response/frontend_agent_response.py` |
| **Service** | `application/service/synthesis_prompt_builder.py` |
| **Outbound Adapters** | `adapter/outbound/external/disclosure_sub_agent_adapter.py` |
| | `adapter/outbound/external/finance_sub_agent_adapter.py` |
| | `adapter/outbound/external/news_sub_agent_adapter.py` |
| | `adapter/outbound/external/openai_synthesis_client.py` |
| | `adapter/outbound/persistence/integrated_analysis_repository_impl.py` |
| **ORM** | `infrastructure/orm/integrated_analysis_orm.py` |

---

## 엔드포인트 스펙

### POST /api/v1/agent/query — 종합 분석 실행

**요청**
```json
{
  "query": "삼성전자 투자해도 될까요?",
  "ticker": "005930",
  "session_id": "optional-uuid"
}
```

**응답**
```json
{
  "success": true,
  "message": "success",
  "data": {
    "session_id": "db7775a5-4c7b-4363-9b19-84d0ce95aa75",
    "result_status": "success",
    "answer": "삼성전자는 신제품 출시와 글로벌 공급계약 등 성장 모멘텀으로 긍정적이지만, 지정학적 리스크와 글로벌 공급망 불확실성은 주의 필요.",
    "agent_results": [
      {
        "agent_name": "news",
        "status": "success",
        "data": { "ticker": "005930" },
        "error_message": null,
        "execution_time_ms": 10378,
        "signal": "bullish",
        "confidence": 0.82,
        "summary": "신제품 출시와 대규모 수주로 단기 모멘텀이 뚜렷함.",
        "key_points": [
          "갤럭시 북6 출시로 AI PC 라인업 완성",
          "영국 콘월 히트펌프·에너지관리 솔루션 대량 공급 계약",
          "반도체 ETF 편입으로 투자자 관심 지속"
        ]
      },
      {
        "agent_name": "disclosure",
        "status": "success",
        "data": {
          "ticker": "005930",
          "filings": {
            "core": [{ "title": "사업보고서 (2025.12)", "filed_at": "2026-03-10", "type": "report" }],
            "other_summary": { "ownership": 35, "unknown": 12, "major_event": 2 }
          }
        },
        "error_message": null,
        "execution_time_ms": 452,
        "signal": "neutral",
        "confidence": 0.75,
        "summary": "2025년 사업보고서 기반 신사업 확장 전략 확인, 공급망 불확실성은 단기 위험 요인.",
        "key_points": [
          "[2026-03-10] 2025년 사업보고서 제출",
          "[positive] R&D 투자와 신사업 확장 전략 추진 중",
          "[positive] 글로벌 전자제품 시장 강력한 점유율 유지"
        ]
      },
      {
        "agent_name": "finance",
        "status": "success",
        "data": {
          "ticker": "005930",
          "stock_name": "삼성전자",
          "market": "KOSPI",
          "current_price": null,
          "roe": 10.36,
          "roa": 7.97,
          "debt_ratio": 29.94,
          "fiscal_year": "2025",
          "sales": 333605900000000.0,
          "operating_income": 43601100000000.0,
          "net_income": 45206800000000.0,
          "retrieved_chunk_count": 3,
          "cache_hit": false
        },
        "error_message": null,
        "execution_time_ms": 10490,
        "signal": "bullish",
        "confidence": 0.78,
        "summary": "매출·이익 성장률 견조, 수익성·재무안정성 양호.",
        "key_points": [
          "매출 +10.9%, 영업이익 +33.2%, 당기순이익 +31.2%",
          "ROE 10.36%, ROA 7.97%로 수익성 양호",
          "부채비율 29.94%로 재무안정성 높음"
        ]
      }
    ],
    "total_execution_time_ms": 13026
  }
}
```

**`result_status` 가능한 값**
- `success` — 전체 성공
- `partial_failure` — 일부 에이전트 실패
- `failure` — 전체 실패

**응답 시간 참고**
- 뉴스 에이전트: 8~12초 (OpenAI 감성 분석)
- 공시 에이전트: ~500ms (캐시 히트 시), 7~20초 (LangGraph RAG 분석)
- 재무 에이전트: ~10초 (캐시 히트 시 1초 이내)
- 처음 분석하는 종목: 재무 데이터 자동 수집으로 40~60초 소요 가능
- 동일 종목 재요청: ~1초 (PostgreSQL 캐시)

---

### GET /api/v1/agent/history — 분석 이력 조회

**쿼리 파라미터**
- `ticker` (필수): 종목 코드 (예: `005930`)
- `limit` (선택, 기본 10, 최대 50): 조회할 이력 개수

**응답**
```json
{
  "success": true,
  "message": "success",
  "data": [
    {
      "ticker": "005930",
      "query": "삼성전자 투자해도 될까요?",
      "overall_signal": "bullish",
      "confidence": 0.78,
      "summary": "...",
      "key_points": ["...", "..."],
      "sub_results": [...],
      "execution_time_ms": 13026,
      "created_at": "2026-04-01T13:37:03.156283+00:00"
    }
  ]
}
```

---

## 분석 가능 종목

뉴스 에이전트는 `TICKER_TO_KEYWORDS` 매핑에 등록된 종목만 실제 분석합니다. 그 외 종목은 뉴스 에이전트가 `no_data`로 응답하며, 공시·재무 에이전트는 모든 종목 지원합니다.

| ticker | 종목명 |
|--------|--------|
| 005930 | 삼성전자 |
| 000660 | SK하이닉스 |
| 005380 | 현대차 |
| 035420 | 네이버 |
| 035720 | 카카오 |
| 068270 | 셀트리온 |
| 207940 | 삼성바이오로직스 |
| 005490 | 포스코 |

> 새 종목 추가 시 `analyze_news_signal_usecase.py`의 `TICKER_TO_KEYWORDS`와 `collect_naver_news_usecase.py`의 `COLLECTION_KEYWORDS` 두 곳 모두 수정 필요.

---

## DB 테이블: integrated_analysis_results

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | INTEGER (PK) | 자동 증가 |
| `ticker` | VARCHAR(20) | 종목 코드 (인덱스) |
| `query` | TEXT | 사용자 질문 |
| `overall_signal` | VARCHAR(20) | bullish / bearish / neutral |
| `confidence` | FLOAT | 0.0 ~ 1.0 |
| `summary` | TEXT | LLM 종합 요약 |
| `key_points` | JSON | 핵심 포인트 리스트 |
| `sub_results` | JSON | 서브에이전트별 결과 전체 |
| `execution_time_ms` | INTEGER | 처리 시간 (ms) |
| `created_at` | DATETIME | 생성 시각 |

### 캐시 전략

- 동일 `ticker` 재조회 시 `created_at` 기준 **1시간 이내** 결과 재사용
- 만료 시 서브에이전트 재호출 → 새 row INSERT

---

## 시그널 집계 로직

| 조건 | 결과 |
|------|------|
| 가중 평균 점수 > 0.2 | bullish |
| 가중 평균 점수 < -0.2 | bearish |
| 그 외 | neutral |

가중치 계산: `score = Σ(signal_score × confidence) / Σ(confidence)`

- bullish = +1.0, neutral = 0.0, bearish = -1.0

---

## 프론트엔드 응답 필터링

`FrontendAgentResponse.from_internal()`에서 내부 디버그 데이터를 제거합니다.

- `finance.data.retrieved_chunks` — 프론트엔드 응답에서 제외 (RAG 청크 원문)
- `finance.data.retrieved_chunk_count` — 유지 (참조 청크 수)

---

## 재무 에이전트 자동 수집

`FinanceSubAgentAdapter`에서 벡터 DB에 데이터가 없는 종목을 처음 요청할 때 자동으로 SerpAPI + DART에서 데이터를 수집합니다.

```
analyze(ticker) 호출
    │
    ├─ GetStoredStockDataUseCase → 404 (데이터 없음)
    │       │
    │       ▼
    │   CollectStockDataUseCase.execute(ticker)
    │   (SerpAPI 기본 정보 + DART 재무비율 수집 → 벡터 DB 저장)
    │       │
    │       ▼
    └─ GetStoredStockDataUseCase → 재시도 → 분석 완료
```

첫 요청 시 수집 시간이 추가되어 40~60초 소요될 수 있습니다.

---

## 설정값 (settings.py)

| 설정 키 | 기본값 | 설명 |
|---------|--------|------|
| `openai_api_key` | — | LLM 종합 요약 및 뉴스 분석용 OpenAI 키 |
| `openai_finance_agent_model` | gpt-5-mini | 재무 에이전트 모델 |
| `openai_embedding_model` | text-embedding-3-small | 임베딩 모델 |
| `finance_rag_top_k` | 3 | RAG 검색 청크 수 |
| `finance_analysis_cache_ttl_seconds` | 3600 | 재무 분석 Redis TTL |
| `naver_client_id` | — | 네이버 뉴스 API 클라이언트 ID |
| `naver_client_secret` | — | 네이버 뉴스 API 클라이언트 시크릿 |

통합 분석 캐시 TTL은 `ProcessAgentQueryUseCase.execute()` 내 `within_seconds=3600`을 직접 수정합니다.


  ---
  뉴스 에이전트가 지원하는 8개 종목 중 삼성전자 제외한 7개입니다:

  ┌────────┬──────────────────┬─────────────────────────────────────────────────┐
  │ ticker │       종목       │                    질문 예시                    │
  ├────────┼──────────────────┼─────────────────────────────────────────────────┤
  │ 000660 │ SK하이닉스       │ "SK하이닉스 HBM 실적 기대되는데 투자해도 될까?" │
  ├────────┼──────────────────┼─────────────────────────────────────────────────┤
  │ 005380 │ 현대차           │ "현대차 전기차 전환 어떻게 보고 있어?"          │
  ├────────┼──────────────────┼─────────────────────────────────────────────────┤
  │ 035420 │ 네이버           │ "네이버 AI 사업 성장 가능성 어때?"              │
  ├────────┼──────────────────┼─────────────────────────────────────────────────┤
  │ 035720 │ 카카오           │ "카카오 지금 저점 매수 타이밍일까?"             │
  ├────────┼──────────────────┼─────────────────────────────────────────────────┤
  │ 068270 │ 셀트리온         │ "셀트리온 바이오시밀러 전망은?"                 │
  ├────────┼──────────────────┼─────────────────────────────────────────────────┤
  │ 207940 │ 삼성바이오로직스 │ "삼성바이오로직스 장기 투자 괜찮을까?"          │
  ├────────┼──────────────────┼─────────────────────────────────────────────────┤
  │ 005490 │ 포스코           │ "포스코홀딩스 2차전지 소재 사업 어때?"          │
  └────────┴──────────────────┴─────────────────────────────────────────────────┘