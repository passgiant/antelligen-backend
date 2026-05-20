# Antelligen — 서비스 개발 및 문제점 해결 방안

> 분석 대상
> - `antelligen-backend` (FastAPI / Python / DDD-Hexagonal)
> - `antelligen-frontend` (Next.js 16 / React 19 / TypeScript 5)
>
> 참고 문서: `PROJECT_ANALYSIS.md`, `서비스_개발_동기_목적.md`, `경쟁사_분석_차별화_방안.md`
> 분석 기준일: 2026-04-28

---

## 0. 문서 목적

본 문서는 Antelligen 서비스를 개발하며 실제로 마주친 **개발·운영·UX·신뢰도 문제** 를
- (a) 어떤 증상으로 드러났는지
- (b) 근본 원인은 무엇이었는지
- (c) 어떤 코드/아키텍처로 해결했는지
- (d) 그 해결이 사용자/운영에 어떤 가치를 주는지

위 4가지 흐름으로 정리하고, **다음 단계 과제(Phase 2)** 를 제시한다. 모든 해결책은 현재 코드베이스에 반영되어 있거나, 진행 중인 항목이다.

---

## 1. 문제점 요약 매트릭스

| # | 영역 | 핵심 문제 | 해결 키 모듈 |
|---|------|-----------|-------------|
| 1 | 데이터 커버리지 | 뉴스 에이전트 8개 종목만 지원 | `TickerKeywordResolver` |
| 2 | 시장 확장 | KR 종목만 분석 가능 (US 미지원) | `MarketRegion` + 어댑터 분기 |
| 3 | 데이터 신선도 | 분기/연간 정규 재무만 — 잠정실적 누락 | `OpenDartPreliminaryEarningsProvider` |
| 4 | 신호 신뢰도 | 출처 무관 단순 평균 — 블룸버그 = 디시인사이드 | `SourceTier` + `_aggregate_signals()` |
| 5 | 도메인 특수성 | 엔터주 SNS 시그널이 LOW 로 묻힘 | `_SECTOR_OVERRIDE` (ENTERTAINMENT) |
| 6 | 비용 / quota | LLM·YouTube API hot-reload 마다 호출 | 다중 캐시 + 조건부 startup 잡 |
| 7 | 동시성 | 다중 사용자 동일 종목 동시 요청 → DART 중복 호출 / DB race | Redis 분산 락 |
| 8 | 응답 속도 | 메인 에이전트 cold path 5~10초 | PG 1h 캐시 + 사업개요 병렬 fetch |
| 9 | UX 맥락 | 시그널만 던져주고 회사 설명 없음 | `BusinessOverview` 카드 통합 |
| 10 | 부분 실패 | 한 서브에이전트 죽으면 전체 실패 | `asyncio.gather(return_exceptions=True)` |
| 11 | 신뢰성 / 거버넌스 | "왜 이 결론이냐" 추적 불가 | LangSmith tracing + 출처 기록 |
| 12 | 레이어 위반 | 어댑터가 다른 도메인 use case 상수 직접 import | Port 도입으로 의존성 역전 |
| 13 | 인증 UX | `/me` 200, `/agent/query` 401 — 토큰 종류별로 갈림 | `_require_auth()` 두 토큰 모두 허용 |
| 14 | 배포 안정성 | startup 잡 1개 실패 = 전체 부팅 실패 | try/except 격리 + graceful degrade |
| 15 | 운영 튜닝 | 가중치·기능 활성화에 재배포 필요 | env-tunable + Feature Flag |

---

## 2. 문제별 상세 — 증상 / 원인 / 해결 / 가치

### 2.1 [P-1] 뉴스 에이전트 8개 종목 제한

**증상**
- `005930`(삼성전자), `000660`(SK하이닉스) 등 8개만 시그널 산출.
- 그 외 종목 요청 시 빈 결과 → "왜 분석이 안 되지?" 사용자 혼란.

**원인**
- `analyze_news_signal_usecase.py` 내부에 `TICKER_TO_KEYWORDS` 딕셔너리 하드코딩.
- 어댑터(`news_sub_agent_adapter.py`) 가 이 use case 상수를 **다른 도메인에서 직접 import** — 레이어 위반까지 동반.

**해결**
- `app/domains/news/application/port/ticker_keyword_resolver_port.py` 신규 — `async resolve(ticker) -> list[str]`.
- `app/domains/news/adapter/outbound/ticker_keyword_resolver.py` — `StockRepository` 로 `stock_name` 동적 조회 + alias 사전(현대차·기아 등) 결합.
- use case / adapter 모두 Port 주입으로 전환 → 레이어 위반 해소.

**가치**
- 모든 KRX 종목(2,500+) 자동 지원.
- 종목 추가 시 코드 수정 0 — DB 에 종목 마스터만 있으면 끝.

---

### 2.2 [P-2] 미국 종목 미지원

**증상**
- `AAPL`, `TSLA` 같은 US 티커로 `/agent/query` 호출하면 빈 시그널.
- 뉴스는 `gl=kr, hl=ko` 로 굳어 있어 영문 뉴스 미수집.
- 재무는 DART, 공시는 DART — 미국 데이터 소스 없음.

**원인**
- 시장 구분 추상이 없어 모든 경로가 KR 데이터 소스에 직결.

**해결 (3 stage 분리 — Stage B)**
- 도메인 추상 신설: `MarketRegion` enum + `MarketRegionResolver` (ticker 형식 / suffix `.KS`/`.KQ` / 알파벳 1~5자 → US).
- 뉴스: SerpAPI locale 파라미터를 region 으로 분기 (KR `gl=kr,hl=ko` / US `gl=us,hl=en`).
- 재무: `ForeignFinancialDataProvider` Port + `YfinanceFinancialDataProvider` 어댑터 (yfinance 동기 호출을 `asyncio.to_thread` 로 wrap).
- 공시: `ForeignDisclosureApiPort` Port + `SecEdgarApiClient` 어댑터 — `company_tickers.json` 으로 ticker→CIK 매핑, `submissions/CIK*.json` 로 8-K/10-K/10-Q filing 리스트.
- SEC 요구 `User-Agent` 헤더 → settings env (`sec_edgar_user_agent`) 로 주입.
- Feature Flag `enable_us_tickers` 로 점진 활성화.

**가치**
- 글로벌 ETF·미장 종목까지 동일 UI/UX 로 분석 가능 → 사용자 활용 범위 2배 이상 확장.
- 어댑터 분기라 KR 회귀 위험 0 (KR 코드 경로 수정 없음).

---

### 2.3 [P-3] 잠정실적 누락 (Stage C)

**증상**
- 분기 발표 직전·직후가 가장 중요한 매매 타이밍인데, 메인 에이전트는 직전 분기 정규 재무제표만 본다 → "이미 시장에 반영된 정보".

**원인**
- `OpenDartFinancialDataProvider` 가 정규 보고서(`report_code=11011/11012/11013`) 만 조회. DART "영업(잠정)실적" 공시는 별도 list API 필요.

**해결**
- 신규 Port `PreliminaryEarningsPort.fetch_latest_preliminary(corp_code, within_days=120)`.
- 어댑터 `OpenDartPreliminaryEarningsProvider` — 기존 `DartDisclosureApiClient` 재사용, `report_nm` 에 "영업(잠정)실적"/"잠정실적" 필터, `rcept_dt` desc 정렬 후 최신 1건.
- `FinanceSubAgentAdapter` (KR 분기) 가 정규 ratios 이후 잠정실적까지 fetch → payload 의 `preliminary_earnings` 블록.
- `langgraph_finance_agent_provider` 의 LLM 프롬프트에 "가장 최근 잠정실적" 섹션 주입.
- US 측은 yfinance `earnings_dates` / `quarterly_income_stmt` 로 동등 기능 (US 는 `is_preliminary=False` — 정식 잠정실적 개념 없음).

**가치**
- 잠정실적 발표일 ~ 정식 보고서 발표일 사이의 **gap window 정보 우위** 확보.
- 분기 어닝 서프라이즈 검출이 메인 시그널에 자동 반영.

---

### 2.4 [P-4] 출처 신뢰도 무관 단순 평균 (Stage D)

**증상**
- 블룸버그 기사와 디시인사이드 글이 **동일 가중**으로 종합 시그널 산출.
- DART 공시(=정답에 가까운 신호)와 SNS(=노이즈) 가 1:1 평균 → 신호 품질 저하.

**원인**
- `_aggregate_signals()` 가 `confidence` 평균만 사용. 출처 메타데이터 자체가 없었음.

**해결**
- 도메인 VO `SourceTier(HIGH/MEDIUM/MEDIUM_LOW/LOW)` + `default_multiplier()` (1.0/0.7/0.5/0.3 — env tunable).
- `SourceCredibilityRegistry` — 도메인 → 티어 하드코딩 매핑 (DART/SEC = HIGH, 글로벌 경제지 = MEDIUM, 국내 IB = MEDIUM_LOW, SNS/커뮤니티 = LOW).
- `SubAgentResponse.source_tier` 필드 추가 — 뉴스는 기사별 평균 티어 스탬프, 공시·재무는 HIGH 고정.
- `process_agent_query_usecase._aggregate_signals()` —
  ```python
  if use_tier:
      tier = r.source_tier or _AGENT_DEFAULT_TIER.get(r.agent_name, MEDIUM)
      multiplier = default_multiplier(tier)
      confidence = confidence * multiplier
  weighted_score += score * confidence
  confidence_total += confidence
  ```
- Feature Flag `enable_source_tier_weighting` 로 점진 활성화 + 가중치 4종을 settings 로 노출.

**가치**
- 종합 시그널이 **신호의 품질** 을 반영 → 동일 종목이라도 DART 공시가 강한 BULLISH 면 SNS 가 대량으로 BEARISH 라도 묻히지 않음.
- "왜 BULLISH 인가" 를 출처 티어 분포로 설명 가능 → **거버넌스/Explainability 강화**.

---

### 2.5 [P-5] 엔터주 SNS 시그널 묻힘 (도메인 특수성)

**증상**
- HYBE/SM/JYP 처럼 **팬덤 / SNS 가 본질** 인 엔터주에서 SNS 가 LOW(0.3) 로 깎임 → 정작 가장 중요한 시그널이 묻힘.

**원인**
- 단일 글로벌 가중치 테이블은 섹터별 정보 가치 차이를 반영하지 못함.

**해결 — 섹터 오버라이드 메커니즘**
```python
_SOCIAL_DOMAINS = {"youtube.com", "youtu.be", "twitter.com", "x.com", "instagram.com"}

_SECTOR_OVERRIDE: dict[Sector, tuple[set[str], SourceTier]] = {
    Sector.ENTERTAINMENT: (_SOCIAL_DOMAINS, SourceTier.MEDIUM),
}

# classify(): 섹터가 ENTERTAINMENT 이고 도메인이 SNS 면 LOW → MEDIUM 승격
```
- `Sector` enum + `SectorLookupPort` + `HardcodedSectorLookup` 시드(HYBE 352820, SM 041510, JYP 035900, YG 122870).
- 향후 게임 / 바이오 / 밈주 등은 `_SECTOR_OVERRIDE` 에 행 추가만으로 확장.

**가치**
- 도메인 지식을 코드 1줄로 반영 → 섹터별 "정보의 본질이 어디 있는가" 를 가중치에 직접 인코딩.
- "엔터는 팬덤 / 바이오는 임상 / 게임은 동접" 같은 도메인 특성을 미래에 수용 가능한 일반 구조.

---

### 2.6 [P-6] LLM·YouTube quota 폭주 (비용)

**증상**
- 개발 중 hot-reload, 배포 재시작이 자주 발생 → 매 startup 마다 매크로 분석 LLM 재호출 → OpenAI/YouTube quota 빠르게 소진.
- 24시간 동안 거의 변하지 않는 회사 마스터를 매 부팅마다 재수집.

**원인**
- 부트스트랩 잡이 무조건 실행. "최근에 했는지" 를 검사하지 않음.
- LLM 결과를 영속 캐시에 저장하지 않아 프로세스 재시작 = 결과 소실.

**해결 — 다층 캐시 + 조건부 startup**
- **Redis 영속 캐시 (4h)** — `MACRO_SNAPSHOT_REDIS_KEY` 에 `MarketRiskJudgementResponse` JSON 저장. startup 시 4h 이내 캐시 있으면 메모리 store 로 복원만 하고 LLM 스킵.
  ```python
  restored = await _try_restore_macro_snapshot(max_age_hours=4)
  if restored: logger.info("[Startup] Macro snapshot restored from Redis")
  else:        await job_refresh_market_risk()
  ```
- **24h 쿨다운** — `refresh_company_list` 는 `collection_job_orm` 의 마지막 success row 가 24h 이내면 스킵.
- **잔여물 기반** — `process_documents` 는 `find_unprocessed_core(limit=1)` 으로 처리 대기 공시가 있을 때만 실행.
- **다중 캐시 계층** — Redis 사업개요 7d / 회사프로필 1d / 통합분석 1h(Postgres) / 자산타입 settings TTL.

**가치**
- LLM 비용 감소 (실측 수준에서 부팅·hot-reload 1회당 LLM 호출 0회).
- YouTube quota 절약 (매크로 분석은 영상·자막·댓글 fetch 비용이 큼).
- 캐시 복원 로그가 운영 가시성에도 기여.

---

### 2.7 [P-7] 다중 사용자 동시 요청 → DART 중복 호출 / DB race

**증상**
- 워치리스트에 같은 종목을 가진 사용자 N명이 동시에 페이지를 열면 DART API 가 N번 호출됨.
- 동일 corp_code 에 동시에 `upsert_bulk` 가 들어가면서 race condition.
- 멀티 워커/멀티 인스턴스 배포 시 in-process Lock 무용지물.

**원인**
- 멱등성 + 동시성 제어가 없는 fetch-and-write 흐름.

**해결 — `OnDemandCollectUseCase` + Redis 분산 락**
```python
lock_key = f"lock:disclosure:on_demand:{corp_code}"
acquired = await self._redis.set(lock_key, "1", nx=True, ex=LOCK_TTL_SECONDS)  # atomic SET NX EX

if not acquired:
    await self._wait_for_other_request(corp_code)   # 다른 프로세스 결과 공유
    return 0

try:
    saved = await self._collect(corp_code, ticker)  # DART 5개 유형 병렬 fetch
    await self._company_repo.mark_as_collect_target(corp_code)
    return saved
finally:
    await self._redis.delete(lock_key)
```
- 멱등성: 시작 전 `find_by_corp_code(limit=1)` 로 이미 있으면 즉시 0 반환.
- TTL 60초 — 락 보유 프로세스가 죽어도 자동 해제 (deadlock 방지).
- Redis 자체 장애 시 `True` 반환하여 락 없이 진행 (가용성 우선 정책).
- 락 대기자는 2초 × 15회(=30초) 동안 DB row 등장 시 즉시 종료.

**가치**
- DART quota 절감 (동시 요청 N → 1).
- DB race condition 차단.
- 멀티 인스턴스 / Kubernetes 환경에서도 안전.

---

### 2.8 [P-8] 메인 에이전트 응답 지연

**증상**
- 신규 종목 cold path: 뉴스 + 공시 + 재무 + LLM 합성 = 5~10초 → 사용자 이탈.
- 동일 종목을 1분 안에 다시 요청해도 동일 비용 재발생.

**원인**
- 직렬 처리 + 캐시 부재 + 회사 정보 sub-call 추가 시 latency 가중.

**해결**
- **PostgreSQL 1시간 캐시** — `IntegratedAnalysisRepository.find_recent(ticker, within_seconds=3600)`. 캐시 hit 시 LLM 호출 0회로 즉시 반환.
- **3 서브에이전트 병렬** — `asyncio.gather(news, disclosure, finance, return_exceptions=True)`.
- **사업개요 별도 병렬 task** — `asyncio.create_task(self._fetch_overview_pair(ticker))` 로 메인 에이전트 처리와 동시 진행 → 추가 latency 거의 0.
- **이중 캐시 분리** — 통합분석 1h Postgres vs 사업개요 7d Redis. 캐시 hit/miss 어느 쪽 경로든 overview 부착.

**가치**
- 캐시 hit 시 응답 < 100ms.
- cold path 도 병렬화로 단일 sub-call 의 평균 응답시간으로 압축.
- PG·Redis TTL 분리로 "정보 신선도가 다른 데이터" 를 다른 주기로 갱신.

---

### 2.9 [P-9] 시그널만 있고 맥락이 없음 (UX)

**증상**
- 사용자: "BULLISH 0.7 입니다." → "이 회사가 뭐 하는 회사인지도 모르는데 어떻게 매매하라고?"

**원인**
- 메인 에이전트가 "신호" 산출에만 집중하고 "회사 컨텍스트" 를 응답에 포함하지 않음.

**해결 — `BusinessOverview` 통합**
- `app/domains/company_profile/domain/value_object/business_overview.py` — `summary, revenue_sources, source(rag_summary|llm_only|asset_llm_only), founding_story, business_model` 5필드.
- DART 사업보고서 RAG chunk(최대 5청크 / 3000자) → OpenAI 요약 → Redis 7d 캐시.
- 메인 에이전트가 사업개요를 (1) LLM 합성 컨텍스트로 주입 (답변 품질 향상) + (2) 응답 페이로드에 카드로 부착 (UX) — **이중 활용**.
- 프론트엔드 `features/company-profile/` 가 카드 컴포넌트 렌더링.

**가치**
- 처음 보는 종목도 "이 회사 본질 → 시그널 → 매매 판단" 의 인지 루프가 한 화면에서 완성.
- LLM 합성 답변도 회사 본질을 알고 작성 → 동일 시그널이라도 답변 품질 향상.
- 7일 캐시로 LLM 비용 통제.

---

### 2.10 [P-10] 한 서브에이전트 죽으면 전체 실패

**증상**
- 외부 API 일시 장애로 SEC EDGAR 가 timeout → 전체 응답 실패 → 뉴스/재무가 살아있어도 사용자에게 아무것도 못 보여줌.

**원인**
- 직렬 호출 + 예외 전파.

**해결 — 부분 실패 허용**
```python
news_r, disclosure_r, finance_r = await asyncio.gather(
    self._news.analyze(ticker, request.query),
    self._disclosure.analyze(ticker),
    self._finance.analyze(ticker, request.query),
    return_exceptions=True,
)
agent_results = [self._coerce(r, name) for r, name in zip([news_r, disclosure_r, finance_r], ["news","disclosure","finance"])]
```
- `_coerce()` 가 Exception 을 `SubAgentResponse.error()` 로 변환.
- `_aggregate_signals()` 는 성공한 결과만으로 가중 평균 (성공 0개면 neutral / 0.0).
- `result_status` 필드로 SUCCESS / PARTIAL_SUCCESS / FAILURE 구분 → 프론트엔드가 일부 카드 빈 상태로 렌더링.

**가치**
- 가용성 향상 — 외부 API 1개 장애가 전체 응답 차단으로 이어지지 않음.
- "공시는 못 받았지만 뉴스+재무 기준으론 BULLISH" 같은 부분 결과도 정직하게 보여줌.

---

### 2.11 [P-11] 거버넌스 / Explainability — "왜 이 결론?"

**증상**
- 경쟁사 분석 문서에서도 강조하듯 "AI 에이전트 도입의 가장 큰 장벽은 거버넌스" — 사용자/규제기관이 의사결정 과정을 추적할 방법이 없으면 신뢰 안 함.

**원인**
- 단순 결과만 반환하고, 내부 추론·소스 추적이 흩어져 있음.

**해결**
- **LangSmith tracing** — `configure_langsmith()` (`app/infrastructure/config/langsmith_config.py`) + `langsmith_tracing/api_key/project/endpoint` env. 모든 LLM 체인의 입력/출력/latency 가 LangSmith 대시보드에 자동 기록.
- **출처 메타 영속화** — `SubAgentResponse` 가 `evidence_urls` / `source_tier` / `confidence` 를 함께 반환 → 사용자에게도 노출.
- **PostgreSQL 통합분석 영속화** — `integrated_analysis_orm` 에 `sub_results` JSON 저장 → 사후 감사 가능.
- **Source Tier 가중치** 자체가 Explainability — "DART 공시 HIGH(1.0) × confidence 0.8 + Bloomberg MEDIUM(0.7) × 0.6 = ..." 로 사용자에게 보여줄 수 있음.

**가치**
- 경쟁사 분석에서 핵심 메시지로 강조한 **"검증 가능한 의사결정 과정 제공"** 을 코드 레벨에서 충족.
- 향후 규제 대응 / Audit Trail / 리포트 자동화로 자연스럽게 확장 가능.

---

### 2.12 [P-12] 레이어 위반 — 어댑터가 다른 도메인 use case 상수 import

**증상**
- `agent` 도메인의 어댑터가 `news` 도메인의 use case 모듈에서 직접 상수를 import 함 → 도메인 경계 무너짐.

**원인**
- 임시방편으로 use case 내부 상수를 외부에 노출.

**해결**
- `TickerKeywordResolverPort` 도입 후 어댑터는 use case 가 아닌 **Port** 만 의존 → 의존성 역전 원칙 준수.
- 도메인 레이어 (`domain/`) 는 FastAPI/SQLAlchemy/Redis/Pydantic 일체 import 금지 (CLAUDE.md 강제).

**가치**
- 도메인 단위 변경/대체가 다른 도메인을 망가뜨리지 않음.
- 단위 테스트 시 Port 만 mock 하면 됨 → 테스트 작성/유지비 감소.

---

### 2.13 [P-13] 인증 UX 분열 — `/me` 200, `/agent/query` 401

**증상**
- 카카오 OAuth 첫 콜백 시 발급되는 `temp_token` 사용자가 `/me` 는 통과하지만 `/agent/query` 에서 401 → "로그인 됐는데 왜 분석은 안 되나" 혼란.

**원인**
- 엔드포인트마다 허용 토큰 종류가 달랐음.

**해결**
- `agent_router._require_auth()` 가 `user_token` 과 `temp_token` 양쪽 모두 허용.
- 쿠키 + `Authorization: Bearer` 헤더 양쪽 입력 모두 지원.
- Redis `session:{token}` / `temp_token:{token}` 키 분리하여 두 흐름을 모두 검증.
- `/authentication/me` 와 동일한 허용 범위 보장.

**가치**
- 가입 전(`temp_token`) 사용자도 핵심 기능 시연 가능 → 가입 전환율 향상.
- 401 UX 일관성으로 디버깅 비용 감소.

---

### 2.14 [P-14] startup 잡 1개 실패 = 전체 부팅 실패

**증상**
- DART 단발 5xx 로 `bootstrap` 잡이 실패 → 전체 서버 부팅 실패 → 다른 멀쩡한 기능까지 정지.

**원인**
- 부트스트랩이 lifespan 안에서 직선적으로 throw.

**해결 — graceful degrade**
```python
try:
    await job_bootstrap()
except Exception as e:
    logger.error("Bootstrap failed (server continues normally): %s", str(e))

try:
    await job_collect_news()
except Exception as e:
    logger.error("News bootstrap failed (server continues normally): %s", str(e))

# ... 모든 startup 잡 동일 패턴
```
- DB 헬스체크(`check_db_health()`) 만 hard fail — 그 외 부트스트랩은 모두 try/except 격리.

**가치**
- 외부 API 일시 장애가 서버 부팅 차단으로 이어지지 않음.
- "DART 가 죽어도 일단 뜨고 추후 catch-up" 가능.

---

### 2.15 [P-15] 운영 튜닝마다 재배포 — 가중치/기능 활성화

**증상**
- "MEDIUM 가중치 0.7 → 0.6 으로 시험해보자" 같은 실험을 위해 매번 코드 수정 + 재배포 필요.

**원인**
- 상수가 코드 안에 박힘.

**해결**
- `app/infrastructure/config/settings.py` 의 pydantic-settings 기반 env 노출:
  - `enable_us_tickers: bool = False`
  - `enable_source_tier_weighting: bool = False`
  - `tier_multiplier_high/medium/medium_low/low: float`
  - `sec_edgar_user_agent: str`
- `default_multiplier(tier)` 가 settings 값을 읽도록 구성 → env 변경 + 재시작만으로 가중치 튜닝.

**가치**
- 점진 롤아웃: 머지 후 flag OFF → 회귀 검증 → flag ON.
- 운영 중 A/B 실험 가능.

---

## 3. 해결 원칙 (요약)

위 문제들을 관통하는 6가지 원칙:

1. **추상은 도메인에서, 실행은 어댑터에서** — Port 만 use case 가 의존, 어댑터 교체로 외부 변화 흡수 (P-1, P-2, P-3, P-12).
2. **시간을 캐시로 사면, LLM 비용은 떨어진다** — 4h/7d/1d/1h 다층 TTL (P-6, P-8).
3. **부분 실패는 기능 — 전체 실패는 버그** — `return_exceptions=True` + try/except 격리 (P-10, P-14).
4. **신호의 품질을 메타데이터로 표현** — Source Tier + Sector Override (P-4, P-5).
5. **동시성은 atomic primitive 로 — `SET NX EX`** — 멱등성 + TTL + graceful degrade (P-7).
6. **거버넌스는 사후가 아니라 사전 설계** — tracing + 출처 영속화 + Explainable 가중치 (P-11).

---

## 4. 다음 단계 — Phase 2 과제

### 4.1 단기 (1~2 sprint)

| 항목 | 동기 |
|------|------|
| Stage D 안정화 + `enable_source_tier_weighting=True` 정식 활성화 | 회귀 데이터 확보 후 production 가중치 ON |
| US 지원 — 프론트엔드 마무리 | 백엔드는 완료, 프론트 UI 만 남음 |
| 국내 IB 리포트 세분화 (산업 vs 레이팅) | 현재 일괄 MEDIUM_LOW — 산업 리포트는 MEDIUM 으로 분리 |
| 섹터 오버라이드 확장 (게임·바이오·밈주) | 구조는 이미 일반화됨, 시드만 추가 |
| 에이전트별 출처 / 가중치 분포 UI 카드화 | "왜 BULLISH" 를 사용자에게 가시화 |

### 4.2 중기 (1~2 분기)

| 항목 | 동기 |
|------|------|
| `SourceCredibilityRegistry` CSV/DB 이관 | 운영 중 무재배포 튜닝 |
| SEC 10-K/10-Q 본문 파싱 | 현재는 메타데이터까지 — 본문 RAG 까지 |
| DART 잠정실적 본문 숫자 추출 강화 | 현재 best-effort — 매출·영업이익 정확 추출 |
| 월가 애널리스트 PDF 리포트 직접 수집 | 현재는 언론 매체 URL 기반이라 "공식 리포트" 가 티어에 미반영 |
| 분산 락 ownership 토큰화 | 동일 corp_code 라도 락 보유자만 해제 — 안전성 강화 |

### 4.3 장기 (분기 이상)

| 항목 | 동기 |
|------|------|
| Audit Trail 영속화 + 규제 대응 리포트 | 경쟁사 차별화의 핵심 — "검증 가능한 의사결정" |
| Human-in-the-loop — 매매 전 사용자 승인 / 의사결정 설명 | 신뢰 기반 UX |
| Guardrails (PII 보호 / Prompt Injection 방어) | 금융 AI 의 Safety 요건 |
| 에이전트 결정 트리 시각화 (Tracing UI) | "왜 이 판단" 을 운영자/사용자에게 그래프로 |
| 다국어 / 다지역 (JP·HK 시장) 확장 | `MarketRegion` 추상이 이미 준비됨 |

---

## 5. 결론

Antelligen 의 모든 핵심 설계는 다음 한 문장으로 요약된다:

> **"신호의 양을 늘리되(P-1, P-2, P-3), 신호의 품질을 메타데이터로 표현하고(P-4, P-5),
> 비용을 캐시로 통제하며(P-6, P-8), 부분 실패와 동시성을 운영 가능한 형태로 다루고(P-7, P-10, P-14),
> 결과만이 아니라 결정 과정을 사용자에게 보여준다(P-9, P-11)."**

이는 경쟁사 분석에서 도출한 **"투자 결과가 아니라 검증 가능한 의사결정 과정과 안전한 실행 구조를 제공하는 서비스가 시장 승자가 된다"** 라는 핵심 메시지를 코드 레벨에서 일관되게 구현한 것이다.

각 문제와 해결의 코드 위치는 `PROJECT_ANALYSIS.md` (전체 구조), `YOUNGJIN_IMPLEMENTATION_REPORT.md` (Stage A~D + 회사정보 / 사업개요 / 분산 락 구현 디테일) 와 교차 참조하면 된다.
