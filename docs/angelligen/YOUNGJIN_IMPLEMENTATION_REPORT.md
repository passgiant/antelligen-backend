# 내가 맡은 영역 — 구현 보고서

> 분석 대상 두 리포지토리에서 **본인 담당 7개 작업** 의 코드 레벨 구현 사항만 추출하여 정리.
>
> 분석 기준일: 2026-04-28
> 관련 리포지토리: `antelligen-backend`, `antelligen-frontend`

---

## 담당 작업 7가지

1. **뉴스 에이전트 종목 8개 제한 풀기**
2. **뉴스 / 공시 / 재무 에이전트 — 미국 주식까지 확대 (재무는 잠정실적 등 최신정보까지)**
3. **출처 신뢰도(티어) 기반 컨피던스 차등 — 메인 에이전트 종합 시그널 반영 (엔터테인먼트 SNS 가중치 보정 포함)**
4. **Startup 시 조건부 주기 잡 실행 기능**
5. **On-demand 공시 수집 + Redis 분산 락**
6. **회사 기본정보 조회 API**
7. **메인 에이전트 답변에 회사 정보 / 사업개요 카드 추가**

---

## 1. 뉴스 에이전트 종목 8개 제한 풀기

### 1.1 문제

- 기존 코드: `app/domains/news/application/usecase/analyze_news_signal_usecase.py` 내부에 `TICKER_TO_KEYWORDS` 하드코딩 딕셔너리가 있어 **8개 종목**(삼성전자, SK하이닉스, 현대차, 네이버, 카카오, 셀트리온, 삼성바이오, 포스코) 만 키워드 해석이 가능했음.
- 그 외 종목은 키워드 해석 실패 → 빈 결과 → 시그널 산출 불가.
- 게다가 `news_sub_agent_adapter.py` 가 use case 내부 상수를 직접 import 하여 **레이어 위반** 까지 발생하고 있었음.

### 1.2 해결 — `TickerKeywordResolverPort` 도입

새 Port + Adapter 로 동적 해결:

| 파일 | 위치 | 역할 |
|------|------|------|
| `TickerKeywordResolverPort` | `app/domains/news/application/port/ticker_keyword_resolver_port.py` | `async resolve(ticker) -> list[str]` 인터페이스 |
| `TickerKeywordResolver` | `app/domains/news/adapter/outbound/ticker_keyword_resolver.py` | `StockRepository` 로 `stock_name` 조회 + alias(현대차·기아 등) synonym 사전 결합 |

### 1.3 변경된 파일

- `app/domains/news/application/usecase/analyze_news_signal_usecase.py` — `TICKER_TO_KEYWORDS` 상수 제거 / Port 주입 / `await self._keyword_resolver.resolve(ticker)` 로 동적 키워드 획득.
- `app/domains/agent/adapter/outbound/external/news_sub_agent_adapter.py` — use case 내부 상수 import 제거 (레이어 위반 해소). Port 사용.
- `main.py` / `agent_router.py` — `TickerKeywordResolver(StockRepositoryImpl(...))` 와이어링.

### 1.4 효과

- 모든 KRX 종목(2,500+) 에 대해 자동으로 키워드 해석 → 뉴스 검색 → 시그널 산출 가능.
- `AnalyzeNewsSignalUseCase.execute("000270")` (기아, 기존 맵에 없던 종목) 도 정상 동작 검증.
- 기존 8개 종목 회귀 smoke 통과.

---

## 2. 미국 주식 확대 — 뉴스·공시·재무 + 잠정실적

### 2.1 시장 구분 인프라 (KR/US 분기의 기반)

새 도메인 VO + 리졸버 도입:

| 파일 | 핵심 |
|------|------|
| `app/domains/stock/domain/value_object/market_region.py` | enum `KR_KOSPI / KR_KOSDAQ / KR_KONEX / US_NYSE / US_NASDAQ / UNKNOWN` + `is_korea()` / `is_us()` |
| `app/domains/stock/domain/service/market_region_resolver.py` | ticker 형식 추론 — 6자리 숫자 → KR, `.KS`/`.KQ` 접미사 → KOSPI/KOSDAQ, 알파벳 1~5자 → US_NASDAQ. `market_hint` 우선 |

순수 Python (Pydantic / SQLAlchemy / FastAPI 일체 미사용 — 도메인 레이어 규칙 준수).

### 2.2 뉴스 (US) — SerpAPI locale 분기

- `app/domains/news/adapter/outbound/external/serp_news_search_provider.py` — `gl="kr", hl="ko"` 하드코딩 제거 → `MarketRegion` 받아 KR(`gl=kr,hl=ko`) / US(`gl=us,hl=en`) 로 매핑.
- `app/domains/agent/adapter/outbound/external/news_sub_agent_adapter.py` — `_collect()` 내부에서 region 분기. KR 은 `NaverNewsClient`, US 는 SerpAPI.

### 2.3 재무 (US) — yfinance 라우팅 + 잠정실적 통합

- 신규 Port: `app/domains/stock/application/port/foreign_financial_data_provider.py`
  - `fetch_financial_ratios(ticker)` / `fetch_recent_earnings(ticker)`
- 신규 VO: `app/domains/stock/domain/value_object/earnings_release.py` — `ticker, report_date, revenue, net_income, eps, is_preliminary, source` (pure Python).
- 신규 어댑터: `app/domains/stock/adapter/outbound/external/yfinance_financial_data_provider.py` — yfinance 동기 호출을 `asyncio.to_thread` 로 wrap. 기존 `FinancialRatio` 엔티티 재사용.
- 수정: `app/domains/agent/adapter/outbound/external/finance_sub_agent_adapter.py` — region 분기 후 KR(DART) / US(yfinance) 라우팅.

### 2.4 공시 (US) — SEC EDGAR

- 신규 Port: `app/domains/disclosure/application/port/foreign_disclosure_api_port.py` — `fetch_recent_filings(ticker, form_types=["8-K","10-K","10-Q"], limit=20)`
- 신규 엔티티: `app/domains/disclosure/domain/entity/foreign_filing.py`
- 신규 어댑터: `app/domains/disclosure/adapter/outbound/external/sec_edgar_api_client.py`
  - `sec.gov/files/company_tickers.json` 으로 ticker → CIK 매핑
  - `data.sec.gov/submissions/CIK{...}.json` 으로 최근 filing 조회
  - **SEC 요구사항: `User-Agent` 헤더 필수** (settings 의 `sec_edgar_user_agent` 주입)
- 수정: `app/domains/disclosure/application/service/disclosure_analysis_service.py` — `MarketRegion.is_us()` 일 때 CompanyRepo 우회하여 SEC 포트 호출. (Phase 1 은 filing 메타데이터까지, 본문 파싱 제외.)

### 2.5 재무 — 잠정실적(영업잠정실적) 페처

기존 DART `fetch_financial_ratios` 가 정규 분기/연간 재무제표(`report_code=11011/11012/11013`) 만 수집했고 "영업(잠정)실적" 공시는 누락되어 있었음. 이걸 보강.

- 신규 Port: `app/domains/stock/application/port/preliminary_earnings_port.py` — `async fetch_latest_preliminary(corp_code, within_days=120) -> Optional[EarningsRelease]`
- 신규 어댑터: `app/domains/stock/adapter/outbound/external/opendart_preliminary_earnings_provider.py`
  - 기존 `DartDisclosureApiClient` 재사용 (`/list.json`)
  - `report_nm` 에 "영업(잠정)실적" / "잠정실적" 필터
  - `rcept_dt` desc 정렬 후 최신 1건 반환
  - Phase 1 은 메타데이터 위주, 본문 숫자 추출은 best-effort
- 신규 UseCase: `app/domains/stock/application/usecase/fetch_preliminary_earnings_usecase.py`
- 수정:
  - `finance_sub_agent_adapter.py` (KR 분기) — DART ratios 이후 `FetchPreliminaryEarningsUseCase` 호출 → payload 에 `preliminary_earnings` 블록 부착
  - `langgraph_finance_agent_provider.py` — 잠정실적이 있으면 LLM 프롬프트에 "가장 최근 잠정실적" 섹션으로 주입
- US 측: yfinance `earnings_dates` / `quarterly_income_stmt` 로 동등 기능 구현 (`is_preliminary=False`).

### 2.6 의존성 / 설정

- `requirements.txt`: `yfinance>=0.2.0` 추가 (이미 머지됨).
- `app/infrastructure/config/settings.py`:
  - `sec_edgar_user_agent: str = "Antelligen research@example.com"` (필수, 기본값 제공)
  - `enable_us_tickers: bool = False` (feature flag — 안정화 후 활성화)

### 2.7 검증 시나리오

- `POST /api/v1/agent/query { ticker: "AAPL" }` → 영어 뉴스 + yfinance 재무(분기 EPS) + SEC 최근 filing 리스트 채워짐.
- `{ ticker: "005930" }` 회귀 — 결과 동일.
- `{ ticker: "000270" }` (기아) → 새 키워드 리졸버 + DART 재무 + 최근 잠정실적까지 부착됨.

---

## 3. 출처 티어 가중치 시스템 — 메인 에이전트 종합 시그널 반영

### 3.1 4단계 티어

요구사항을 다음 enum 으로 매핑:

`app/domains/agent/domain/value_object/source_tier.py`

```python
class SourceTier(str, Enum):
    HIGH = "HIGH"          # DART 공시, SEC, 미국 IB 공식 리포트, 기업 IR
    MEDIUM = "MEDIUM"      # Bloomberg, Reuters, WSJ, FT, 한경, 매경, 월가 애널리스트
    MEDIUM_LOW = "MEDIUM_LOW"  # 국내 IB 공식 리포트 (buy-bias 보정)
    LOW = "LOW"            # SNS, 일반 뉴스, 커뮤니티

_DEFAULT_WEIGHTS = {
    SourceTier.HIGH: 1.0,
    SourceTier.MEDIUM: 0.7,
    SourceTier.MEDIUM_LOW: 0.5,
    SourceTier.LOW: 0.3,
}
```

가중치 수치는 settings env 로 노출 — `tier_multiplier_high/medium/medium_low/low` (`settings.py:134-137`).

### 3.2 출처 분류 레지스트리 + 섹터 오버라이드

`app/domains/agent/adapter/outbound/source_credibility_registry.py` — 도메인 → 티어 하드코딩 매핑.

| 티어 | 포함 도메인 |
|------|-----------|
| HIGH | `dart.fss.or.kr`, `sec.gov`, `edgar.sec.gov` |
| MEDIUM | `bloomberg.com`, `reuters.com`, `wsj.com`, `ft.com`, `cnbc.com`, `marketwatch.com`, `barrons.com`, `seekingalpha.com`, `hankyung.com`, `mk.co.kr`, `edaily.co.kr`, `etnews.com`, `sedaily.com` |
| MEDIUM_LOW | `samsung-pop.com`, `miraeassetdaewoo.com`, `nhqv.com`, `kiwoom.com`, `shinyoung.com`, `koreainvestment.com` |
| LOW | `naver.com`, `n.news.naver.com`, `daum.net`, `news.daum.net`, `youtube.com`, `youtu.be`, `twitter.com`, `x.com`, `instagram.com`, `reddit.com`, `dcinside.com`, `ruliweb.com`, `blind.com`, `clien.net` |

#### **엔터테인먼트 섹터 — SNS 가중치 보정**

요구사항대로 엔터테인먼트 회사는 SNS 가 중요한 시그널 소스이므로 LOW → MEDIUM 으로 승격:

```python
_SOCIAL_DOMAINS = {"youtube.com", "youtu.be", "twitter.com", "x.com", "instagram.com"}

_SECTOR_OVERRIDE: dict[Sector, tuple[set[str], SourceTier]] = {
    Sector.ENTERTAINMENT: (_SOCIAL_DOMAINS, SourceTier.MEDIUM),
}

# classify() 내부
if sector in _SECTOR_OVERRIDE:
    override_domains, upgraded_tier = _SECTOR_OVERRIDE[sector]
    if domain in override_domains and tier == SourceTier.LOW:
        tier = upgraded_tier
```

→ 엔터(HYBE/SM/JYP/YG) 종목 분석 시 YouTube·X·Instagram 글이 LOW(0.3) 가 아닌 MEDIUM(0.7) 으로 컨피던스 가중. **추후 밈주 / 게임 / 바이오 등 섹터 확장 가능한 일반 구조** 로 설계.

섹터 매핑은 `app/domains/agent/domain/value_object/sector.py` (Sector enum) + `app/domains/stock/application/port/sector_lookup_port.py` + `app/domains/stock/adapter/outbound/persistence/hardcoded_sector_lookup.py` 로 구성. 시드: HYBE(352820), SM(041510), JYP(035900), YG(122870).

### 3.3 종합 시그널 가중 — `ProcessAgentQueryUseCase._aggregate_signals()`

핵심 변경: `app/domains/agent/application/usecase/process_agent_query_usecase.py:171-211`

```python
@staticmethod
def _aggregate_signals(results: list[SubAgentResponse]) -> tuple[str, float]:
    settings = get_settings()
    use_tier = settings.enable_source_tier_weighting

    _AGENT_DEFAULT_TIER = {
        "news": SourceTier.MEDIUM,
        "disclosure": SourceTier.HIGH,
        "finance": SourceTier.HIGH,
    }

    weighted_score = 0.0
    confidence_total = 0.0
    count = 0
    for r in results:
        if r.is_success() and r.signal is not None and r.confidence is not None:
            score = _SIGNAL_SCORE.get(r.signal, 0.0)
            confidence = r.confidence
            if use_tier:
                tier = r.source_tier or _AGENT_DEFAULT_TIER.get(r.agent_name, SourceTier.MEDIUM)
                multiplier = default_multiplier(tier)
                confidence = confidence * multiplier
            weighted_score += score * confidence
            confidence_total += confidence
            count += 1
    ...
    avg_score = weighted_score / confidence_total
    if avg_score > 0.2:   signal = "bullish"
    elif avg_score < -0.2: signal = "bearish"
    else:                 signal = "neutral"
    return signal, round(avg_confidence, 4)
```

티어 granularity = **기사별(뉴스) + 에이전트 고정(공시·재무)** 혼합:
- 뉴스: 기사별로 `classify()` 호출 → 평균 티어를 `SubAgentResponse.source_tier` 에 스탬프
- 공시: HIGH 고정 스탬프
- 재무: HIGH 고정 스탬프

`SubAgentResponse` 확장: `source_tier: Optional[SourceTier] = None` 필드 추가 (`app/domains/agent/application/response/sub_agent_response.py`).

### 3.4 Feature Flag

`enable_source_tier_weighting: bool = False` (settings.py:133) — 안정화 검증 후 ON.

---

## 4. Startup 시 조건부 주기 잡 실행

### 4.1 문제

기존엔 서버 startup 시 모든 부트스트랩/주기 잡을 무조건 실행 → 짧은 재시작/hot-reload 주기에서 LLM·외부 API quota 낭비, 같은 작업이 1시간 내 여러 번 실행되는 문제.

### 4.2 해결 — `lifespan` 에 조건부 트리거 도입

`main.py` 의 `lifespan` 컨텍스트에서 잡별로 "최근 성공 시각 / 미처리 잔여물" 등을 검사 후 실행 여부 결정.

#### 4.2.1 `refresh_company_list` — 24시간 쿨다운

```python
async with AsyncSessionLocal() as session:
    latest = await CollectionJobRepositoryImpl(session).find_latest_by_job_name(
        "refresh_company_list"
    )
    should_run = (
        latest is None
        or latest.status != "success"
        or latest.started_at is None
        or (datetime.now() - latest.started_at) > timedelta(hours=24)
    )
if should_run:
    await job_refresh_company_list()
else:
    logger.info("[Startup] refresh_company_list skipped (last success < 24h)")
```

→ 24시간 내 성공 이력이 있으면 startup 잡 스킵. `collection_job_orm` 의 마지막 성공 row 를 키로 사용.

#### 4.2.2 `process_documents` — 미처리 잔여물 기반

```python
async with AsyncSessionLocal() as session:
    unprocessed = await DisclosureRepositoryImpl(session).find_unprocessed_core(limit=1)
if unprocessed:
    await job_process_documents()
else:
    logger.info("[Startup] process_documents skipped (no unprocessed core disclosures)")
```

→ `is_core=True` 이고 처리 안 된 공시가 1건이라도 있으면 실행, 없으면 스킵.

#### 4.2.3 `refresh_market_risk` — Redis 영속 캐시 4h 이내 복원

```python
async def _try_restore_macro_snapshot(max_age_hours: int) -> bool:
    raw = await redis_client.get(MACRO_SNAPSHOT_REDIS_KEY)
    if not raw: return False
    payload = json.loads(raw)
    updated_at = datetime.fromisoformat(payload["updated_at"])
    if datetime.now() - updated_at > timedelta(hours=max_age_hours):
        return False
    response = MarketRiskJudgementResponse.model_validate(payload["response"])
    get_market_risk_snapshot_store().set(response, updated_at=updated_at)
    return True

# lifespan 본문
restored = await _try_restore_macro_snapshot(max_age_hours=4)
if restored:
    logger.info("[Startup] Macro snapshot restored from Redis (skip bootstrap)")
else:
    await job_refresh_market_risk()
```

→ Redis 에 4시간 이내 매크로 스냅샷이 있으면 메모리 store 로 복원, 없으면 신규 생성. **YouTube quota / LLM 비용 절약** 의 가장 큰 기여 포인트.

### 4.3 그 외 부트스트랩 잡 — 항상 try/except 로 격리

```python
try:
    await job_bootstrap()
except Exception as e:
    logger.error("Bootstrap failed (server continues normally): %s", str(e))
```

→ 어느 잡이 죽어도 서버 자체는 항상 부팅 성공 (graceful degrade).

### 4.4 정기 cron 등록은 별도

`app/infrastructure/scheduler/disclosure_scheduler.py` 의 `create_disclosure_scheduler()` 가 APScheduler 에 20+ 개 cron job 등록.

---

## 5. On-demand 공시 수집 + Redis 분산 락

### 5.1 문제

- 기존 공시 수집은 스케줄러 기반 batch 수집 → "사용자가 방금 본 종목" 의 최신 공시는 다음 배치까지 보이지 않음.
- 사용자가 동일 종목을 동시에 여러 번 요청하면 DART API 가 중복 호출 → quota 낭비 / DB 중복 upsert / race condition.
- 멀티프로세스 / 멀티서버 배포 시 in-process Lock 으론 부족 → **Redis 분산 락** 필요.

### 5.2 구현 — `OnDemandCollectUseCase`

`app/domains/disclosure/application/usecase/on_demand_collect_usecase.py`

핵심 의존성:
```python
def __init__(
    self,
    dart_disclosure_api: DartDisclosureApiPort,
    disclosure_repository: DisclosureRepositoryPort,
    company_repository: CompanyRepositoryPort,
    redis: aioredis.Redis,        # ← 분산 락용
):
```

상수:
```python
ON_DEMAND_PBLNTF_TYPES = ["A", "B", "C", "D", "E"]  # 5개 공시 유형 병렬 fetch
ON_DEMAND_LOOKBACK_DAYS = 180
LOCK_TTL_SECONDS = 60
LOCK_WAIT_SECONDS = 2
LOCK_MAX_RETRIES = 15  # 최대 30초 대기
```

### 5.3 분산 락 로직

```python
async def execute(self, corp_code: str, ticker: Optional[str] = None) -> int:
    # 1) 이미 수집된 적 있으면 즉시 0 반환 (idempotent)
    existing = await self._disclosure_repo.find_by_corp_code(corp_code, limit=1)
    if existing:
        return 0

    # 2) 분산 락 획득 시도 — Redis SET NX EX
    lock_key = f"lock:disclosure:on_demand:{corp_code}"
    acquired = await self._acquire_lock(lock_key)

    if not acquired:
        # 3) 락 획득 실패 = 다른 프로세스가 동일 종목 수집 중 → 대기
        await self._wait_for_other_request(corp_code)
        return 0

    try:
        # 4) DART 5개 유형 병렬 호출 + DB upsert
        saved = await self._collect(corp_code, ticker)
        await self._company_repo.mark_as_collect_target(corp_code)
        return saved
    finally:
        # 5) 락 반드시 해제
        await self._redis.delete(lock_key)

async def _acquire_lock(self, lock_key: str) -> bool:
    try:
        return bool(await self._redis.set(lock_key, "1", nx=True, ex=LOCK_TTL_SECONDS))
    except aioredis.RedisError as e:
        logger.warning("Redis 락 획득 실패 (%s): %s — 락 없이 진행", lock_key, e)
        return True   # ← Redis 다운 시 graceful degrade (락 없이 진행)
```

#### 락의 핵심 보장
- `SET key value NX EX` — atomic single-shot — race condition 없음
- `LOCK_TTL_SECONDS=60` — 프로세스 죽어도 60초 후 자동 해제 (deadlock 방지)
- `try/finally` 로 정상 종료 시 즉시 해제
- Redis 장애 시 `True` 반환하여 락 없이 진행 (가용성 우선)

### 5.4 다른 프로세스 대기 로직

```python
async def _wait_for_other_request(self, corp_code: str) -> None:
    for _ in range(LOCK_MAX_RETRIES):  # 15회
        await asyncio.sleep(LOCK_WAIT_SECONDS)  # 2초씩
        existing = await self._disclosure_repo.find_by_corp_code(corp_code, limit=1)
        if existing:
            return  # 다른 프로세스가 저장 완료 → 즉시 리턴
    logger.warning("다른 on-demand 수집 대기 시간 초과 (corp_code=%s)", corp_code)
```

→ 동시 요청자는 락 보유자가 끝날 때까지 최대 30초 대기 후 결과 공유 (DB row 가 보이면 즉시 종료).

### 5.5 DART 5개 유형 병렬 호출

```python
async def _collect(self, corp_code: str, ticker: Optional[str]) -> int:
    fetch_tasks = [
        self._dart_api.fetch_all_pages(
            bgn_de=bgn_date, end_de=end_date,
            corp_code=corp_code, pblntf_ty=pblntf_ty,
        )
        for pblntf_ty in ON_DEMAND_PBLNTF_TYPES  # A, B, C, D, E
    ]
    results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
    # ... 부분 실패 허용, 성공한 결과만 합쳐 upsert_bulk
```

5개 공시 유형(A: 정기공시 / B: 주요사항 / C: 발행공시 / D: 지분공시 / E: 기타) 을 동시 fetch → 평균 응답시간 단축.

### 5.6 별도 `OndemandCollectUseCase` (admin)

`app/domains/disclosure/application/usecase/ondemand_collect_usecase.py` 는 사용자 입력(`bgn_de`, `end_de`, `pblntf_ty` 명시) 기반 admin 수집용. 락 없이 단일 호출(`CompanyDataCoverage` 갱신 포함). `on_demand_collect_usecase` 와 별개 흐름.

---

## 6. 회사 기본정보 조회 API

### 6.1 신규 엔드포인트

`GET /api/v1/company-profile/{ticker}`

`app/domains/company_profile/adapter/inbound/api/company_profile_router.py:52`

```python
@router.get("/{ticker}", response_model=CompanyProfileResponse)
async def get_company_profile(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    settings = get_settings()
    sec_client = SecEdgarApiClient(user_agent=settings.sec_edgar_user_agent)
    asset_type_port = CachedAssetTypeAdapter(YahooFinanceAssetTypeClient(), redis)

    usecase = GetCompanyProfileUseCase(
        company_repository=CompanyRepositoryImpl(db),
        dart_company_info=DartCompanyInfoClient(),
        cache=RedisCompanyProfileCache(redis),
        rag_chunk_repository=RagChunkRepositoryImpl(db),
        business_overview=OpenAIBusinessOverviewClient(),
        overview_cache=RedisBusinessOverviewCache(redis),
        us_company_name=SecCompanyNameAdapter(sec_client),
        asset_type_port=asset_type_port,
    )
    profile, overview = await usecase.execute(ticker)
    if profile is None:
        raise HTTPException(404, f"Company profile not found for ticker '{ticker}'.")
    return CompanyProfileResponse.from_entity(profile, overview)
```

### 6.2 도메인 — `CompanyProfile` 엔티티

`app/domains/company_profile/domain/entity/company_profile.py` — 순수 dataclass.
- 식별: `corp_code`, `corp_name`, `corp_name_eng`, `stock_name`, `stock_code`
- 조직: `ceo_nm`, `corp_cls`(KOSPI/KOSDAQ/US/...)
- 등록: `jurir_no`, `bizr_no`, `adres`
- 연락: `hm_url`, `ir_url`, `phn_no`, `fax_no`
- 산업: `induty_code`, `est_dt`, `acc_mt`
- 자산: `asset_type` (EQUITY / ETF / INDEX)

### 6.3 분기 처리 — 자산 유형별 조회 경로

`GetCompanyProfileUseCase.execute()` 가 3분기:

```
ticker 입력
   │
   ├─ asset_type 분류 (yfinance quoteType, Redis 캐시)
   │
   ├─ ETF / INDEX 경로
   │     └ DART/SEC/RAG 미적용
   │     └ 합성 profile + LLM-only 자산 설명 (asset_llm_only)
   │
   ├─ US EQUITY 경로 (MarketRegion.is_us())
   │     └ SEC company_tickers.json → 회사명 매핑
   │     └ 합성 profile (corp_cls="US")
   │     └ LLM-only 사업 개요 (RAG 불가)
   │
   └─ KR EQUITY 경로 (default)
         └ Redis 캐시 hit?  → 즉시 반환
         └ DART 회사 마스터(CompanyRepository) 에서 corp_code 조회
         └ DART /company.json 로 기업 개황 fetch
         └ Redis 1d 캐시 저장
         └ + 사업개요 (RAG 기반 LLM 요약)
```

### 6.4 캐시 전략

| 캐시 | TTL | 키 |
|------|-----|----|
| `RedisCompanyProfileCache` | **1일** (DART 기업개황은 거의 안 변함) | `ticker` |
| `RedisBusinessOverviewCache` | **7일** (LLM 비용 큼) | `corp_code` 또는 `asset:{ticker}` |
| `CachedAssetTypeAdapter` | settings TTL | `ticker` (yfinance quoteType) |

### 6.5 외부 클라이언트

- `DartCompanyInfoClient` (`/api/company.json`) — KR 기업개황
- `SecCompanyNameAdapter` + `SecEdgarApiClient` — US 회사명
- `YahooFinanceAssetTypeClient` — 자산 유형 분류

---

## 7. 메인 에이전트 답변에 회사정보 / 사업개요 카드 추가

### 7.1 백엔드 — `BusinessOverview` VO + `agent/query` 응답에 부착

**도메인 VO** — `app/domains/company_profile/domain/value_object/business_overview.py`:

```python
@dataclass(frozen=True)
class BusinessOverview:
    summary: str
    revenue_sources: list[str] = field(default_factory=list)
    source: str = "llm_only"  # "rag_summary" | "llm_only" | "asset_llm_only"
    founding_story: Optional[str] = None
    business_model: Optional[str] = None
```

**Application Port** — 외부 의존성 분리:
- `BusinessOverviewPort` (out) — `generate(corp_name, induty_code, rag_context)` / `generate_for_asset(ticker, asset_type)`
- `BusinessOverviewCachePort` (out) — Redis 캐시 인터페이스

**Adapter** — `OpenAIBusinessOverviewClient` (LLM 생성) + `RedisBusinessOverviewCache` (7일 TTL).

**RAG chunk 보강** — `RagChunkRepositoryPort.find_business_chunks_by_corp_code()` 메서드 추가. DART 사업보고서 본문에서 "사업의 개요" / "주요 제품 및 서비스" 섹션 청크를 LLM 컨텍스트로 주입 (최대 5청크 / 3000자).

### 7.2 메인 에이전트 응답에 통합

`process_agent_query_usecase.py:64-133`:

```python
async def execute(self, request: AgentQueryRequest) -> AgentQueryResponse:
    ...
    # 회사 사업개요는 7일 Redis 캐시라 통합분석 1시간 캐시와 독립적으로 늘 fetch.
    overview_task = asyncio.create_task(self._fetch_overview_pair(ticker))

    # 1시간 PostgreSQL 캐시 hit 시에도 overview 부착
    if cached:
        _, overview_dto = await overview_task
        return self._from_cached(cached, session_id, overview_dto)

    # 3개 서브에이전트 병렬 호출 ...

    # LLM 합성 시 overview_vo 를 컨텍스트로 함께 주입
    profile_overview, overview_dto = await overview_task
    profile, overview_vo = profile_overview if profile_overview else (None, None)
    summary, key_points = await self._llm_synthesis.synthesize(
        ticker=ticker, query=request.query,
        sub_results=agent_results,
        business_overview=overview_vo,        # ← 사업개요를 LLM 컨텍스트에
        corp_name=profile.corp_name if profile else None,
    )
    ...
    return AgentQueryResponse(
        ...,
        agent_results=agent_results,
        business_overview=overview_dto,        # ← 응답 페이로드에 카드 데이터
    )
```

핵심 설계 포인트:
- **병렬 fetch** — `asyncio.create_task` 로 사업개요 fetch 와 메인 에이전트 처리를 동시 실행 → 추가 latency 거의 0
- **graceful 실패** — `_fetch_overview_pair()` 내부에서 try/except → overview 없어도 메인 응답은 정상 반환
- **이중 활용** — overview 가 (1) LLM 합성 컨텍스트로 들어가서 답변 품질 향상 + (2) 응답 페이로드에 카드 DTO 로 따로 부착
- **PostgreSQL 1h 캐시 hit 경로에서도 부착** — 캐시는 "시그널" 만 캐시하고 "사업개요" 는 별도 7일 캐시이므로 hit/miss 어느 쪽이든 attach.

### 7.3 응답 DTO — `AgentBusinessOverview`

`app/domains/agent/application/response/agent_business_overview.py`

```python
class AgentBusinessOverview:
    @classmethod
    def from_overview(cls, corp_name: str, overview: BusinessOverview) -> "AgentBusinessOverview":
        ...
```

`AgentQueryResponse.business_overview: Optional[AgentBusinessOverview]` 필드로 노출 → `FrontendAgentResponse.from_internal()` 에서 그대로 전달.

### 7.4 프론트엔드 — UI 카드 컴포넌트

- `features/company-profile/domain/model/` — `BusinessOverview` 타입 (`summary`, `revenueSources`, `source`, `foundingStory`, `businessModel`)
- `features/company-profile/ui/` — 사업개요 카드 컴포넌트 (Dumb Component)
- 메인 에이전트 답변 화면(`/stock` 또는 분석 결과 페이지) 에 카드 렌더링
- `source` 필드별 배지 표시: `rag_summary` (DART 본문 기반) / `llm_only` (요약만) / `asset_llm_only` (ETF/INDEX)

### 7.5 사용자 가치

- 종목 분석을 처음 보는 사용자도 "이 회사가 뭐 하는 회사인지" 즉시 파악 → 시그널의 맥락 이해도 향상
- LLM 합성 답변의 품질 향상 (회사 본질을 알고 답변)
- 7일 캐시로 LLM 비용 통제
- ETF/INDEX 종목도 "지수/펀드 구성 설명" 으로 동일 카드 형식 제공 (UX 일관성)

---

## 8. 변경 파일 요약 (담당 부분)

### 8.1 백엔드 신규 / 수정 파일 매트릭스

| 작업 | 신규 파일 | 수정 파일 |
|------|-----------|----------|
| 1. 티커 제한 해제 | `news/application/port/ticker_keyword_resolver_port.py`<br>`news/adapter/outbound/ticker_keyword_resolver.py` | `news/application/usecase/analyze_news_signal_usecase.py`<br>`agent/adapter/outbound/external/news_sub_agent_adapter.py`<br>`main.py` |
| 2-1. MarketRegion | `stock/domain/value_object/market_region.py`<br>`stock/domain/service/market_region_resolver.py` | — |
| 2-2. US 뉴스 | — | `news/adapter/outbound/external/serp_news_search_provider.py`<br>`agent/adapter/outbound/external/news_sub_agent_adapter.py` |
| 2-3. US 재무 (yfinance) | `stock/application/port/foreign_financial_data_provider.py`<br>`stock/domain/value_object/earnings_release.py`<br>`stock/adapter/outbound/external/yfinance_financial_data_provider.py` | `agent/adapter/outbound/external/finance_sub_agent_adapter.py` |
| 2-4. US 공시 (SEC) | `disclosure/application/port/foreign_disclosure_api_port.py`<br>`disclosure/domain/entity/foreign_filing.py`<br>`disclosure/adapter/outbound/external/sec_edgar_api_client.py` | `disclosure/application/service/disclosure_analysis_service.py` |
| 2-5. 잠정실적 | `stock/application/port/preliminary_earnings_port.py`<br>`stock/adapter/outbound/external/opendart_preliminary_earnings_provider.py`<br>`stock/application/usecase/fetch_preliminary_earnings_usecase.py` | `agent/adapter/outbound/external/finance_sub_agent_adapter.py`<br>`agent/adapter/outbound/external/langgraph_finance_agent_provider.py` |
| 3. 소스 티어 | `agent/domain/value_object/source_tier.py`<br>`agent/domain/value_object/sector.py`<br>`agent/application/port/source_credibility_port.py`<br>`agent/adapter/outbound/source_credibility_registry.py`<br>`stock/application/port/sector_lookup_port.py`<br>`stock/adapter/outbound/persistence/hardcoded_sector_lookup.py` | `agent/application/usecase/process_agent_query_usecase.py`<br>`agent/application/response/sub_agent_response.py`<br>`agent/adapter/outbound/external/news_sub_agent_adapter.py`<br>`agent/adapter/outbound/external/disclosure_sub_agent_adapter.py`<br>`agent/adapter/outbound/external/finance_sub_agent_adapter.py`<br>`infrastructure/config/settings.py` |
| 4. 조건부 startup | — | `main.py` (lifespan 내부) |
| 5. On-demand + 분산 락 | `disclosure/application/usecase/on_demand_collect_usecase.py` | (라우터 와이어링) |
| 6. 회사 기본정보 API | `company_profile/...` (도메인 전체 신규)<br>(entity / VO / port / usecase / cache / DART client / SEC adapter / router / response DTO) | `app/adapter/inbound/api/v1_router.py` (router include) |
| 7. 사업개요 카드 | `company_profile/domain/value_object/business_overview.py`<br>`company_profile/application/port/out/business_overview_port.py`<br>`company_profile/application/port/out/business_overview_cache_port.py`<br>`company_profile/adapter/outbound/external/openai_business_overview_client.py`<br>`company_profile/adapter/outbound/cache/business_overview_cache.py`<br>`agent/application/response/agent_business_overview.py` | `agent/application/usecase/process_agent_query_usecase.py`<br>`agent/application/response/agent_query_response.py`<br>`agent/application/response/frontend_agent_response.py`<br>`agent/application/port/llm_synthesis_port.py`<br>`agent/adapter/outbound/external/openai_synthesis_client.py`<br>`agent/adapter/inbound/api/agent_router.py`<br>`disclosure/application/port/rag_chunk_repository_port.py` (`find_business_chunks_by_corp_code` 메서드 추가) |

### 8.2 프론트엔드 신규 / 수정

- `features/company-profile/` — domain / application / infrastructure / ui 4계층 신규
- 메인 에이전트 결과 페이지에 사업개요 카드 / 회사 기본정보 카드 렌더링
- US 종목 표시 — ticker 형식별 라벨 분기 (KR/US 표시)

---

## 9. 설정 (env) 한눈에 보기

`app/infrastructure/config/settings.py:121-137`:

```python
# US market support
enable_us_tickers: bool = False
sec_edgar_user_agent: str = "Antelligen research@example.com"

# Source tier weighting
enable_source_tier_weighting: bool = False
tier_multiplier_high: float = 1.0
tier_multiplier_medium: float = 0.7
tier_multiplier_medium_low: float = 0.5
tier_multiplier_low: float = 0.3
```

운영 점진 활성화 순서:
1. 머지 후 `enable_us_tickers=False`, `enable_source_tier_weighting=False` 로 배포 (기존 동작 유지)
2. 회귀 검증 (KR 기존 8종목 + 신규 KRX 종목 + AAPL/TSLA 등)
3. `enable_us_tickers=True` 로 단계적 활성화
4. 안정화 후 `enable_source_tier_weighting=True` — 가중치 효과 모니터링
5. 가중치 수치는 env 로 튜닝 가능

---

## 10. 검증 시나리오 / Acceptance Criteria

| # | 시나리오 | 기대 |
|---|---------|------|
| 1 | `POST /api/v1/agent/query { ticker: "000270" }` (기아, 기존 8종목 외) | 뉴스 시그널 정상 산출, 응답에 회사정보·사업개요 카드 부착 |
| 2 | `POST /api/v1/agent/query { ticker: "AAPL" }` (US 종목) | 영어 뉴스 + yfinance 분기 EPS + SEC 8-K/10-Q filing 리스트, US 회사명 카드 |
| 3 | `POST /api/v1/agent/query { ticker: "352820" }` (HYBE, 엔터) | YouTube/X 출처 기사가 LOW 가 아닌 MEDIUM 가중으로 종합 시그널에 더 강하게 반영 |
| 4 | 동일 종목 동시 5개 요청 (`AAPL` on-demand 공시) | 1개만 DART API 호출, 나머지는 락 대기 후 동일 결과 공유 |
| 5 | 24h 내 두 번 서버 재시작 | `refresh_company_list` 두 번째엔 스킵 로그 |
| 6 | 4h 내 hot-reload | 매크로 스냅샷이 Redis 에서 복원 (LLM 호출 0회) |
| 7 | `GET /api/v1/company-profile/AAPL` | SEC 회사명 기반 합성 profile + LLM-only 사업개요 카드 |
| 8 | `GET /api/v1/company-profile/SPY` | asset_type=ETF 경로 → ETF 설명 카드 |
| 9 | 동일 종목 종합분석 1시간 내 재요청 | Postgres 캐시 hit → 시그널은 캐시본, 사업개요는 7일 Redis 에서 별도 hit |

---

## 11. 추후 (Phase 2) 후보

- 국내 IB 리포트 세분화 (산업 vs 레이팅 — 현재 일괄 MEDIUM_LOW)
- 엔터 외 섹터 오버라이드 (게임 Roblox, 바이오 clinical trial, 밈주 AMC/GME) — `_SECTOR_OVERRIDE` 구조에 행만 추가하면 끝
- `SourceCredibilityRegistry` 를 CSV/DB 로 이관 → 운영 중 무재배포 튜닝
- SEC 10-K/10-Q 본문 파싱 (현재 메타데이터까지)
- DART 잠정실적 본문 숫자 추출 강화 (현재 best-effort)
- 월가 애널리스트 PDF 리포트 직접 수집 (현재는 언론 매체 URL 기반)
- On-demand 락의 토큰 기반 ownership (동일 corp_code 라도 락 보유자만 해제 가능 — 현재는 단순 SET/DEL)

---

이 문서는 코드 내 실제 구현된 내용을 1:1 로 매핑한 것이며, 본인 담당 7개 작업의 PR 단위·검증 포인트·후속 과제까지 포함한다. 도메인별 세부 비즈니스 로직(LLM 프롬프트, 잠정실적 파싱 휴리스틱, 분산 락 토큰화 등)은 각 파일 본문 참조.
