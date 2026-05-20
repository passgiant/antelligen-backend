# Antelligen — 전체 개발 내용 분석 보고서

> 분석 대상
> - `D:\Documents\simsys\ai_agent_edu_dev\antelligen-backend` (FastAPI / Python)
> - `D:\Documents\simsys\ai_agent_edu_dev\antelligen-frontend` (Next.js 16 / React 19 / TypeScript)
>
> 분석 기준일: 2026-04-28

---

## 1. 한 줄 요약

**Antelligen** 은 한국·미국 주식 종목에 대해 **뉴스 / 공시 / 재무 / 사업개요 / SNS 감성 / Smart Money(외국인·기관 흐름) / 거시 환경 / 잠정실적 / 이벤트 인과관계** 를 다중 LLM 서브에이전트로 병렬 분석해 **통합 투자 시그널(Bullish / Neutral / Bearish + Confidence)** 을 산출하는 풀스택 투자 인텔리전스 플랫폼이다.

- **백엔드**: FastAPI + DDD/Hexagonal + Postgres(+pgvector) + Redis + APScheduler + LangGraph + OpenAI/Anthropic
- **프론트엔드**: Next.js 16 (App Router) + React 19 + TypeScript 5(strict) + Tailwind 4 + Jotai + lightweight-charts / recharts

---

## 2. 시스템 아키텍처

### 2.1 백엔드 — Hexagonal + DDD

```
app/
├─ adapter/inbound/api/             # /api/v1 메인 라우터 집합
│   ├─ v1_router.py                 # 모든 도메인 라우터 등록
│   └─ health_router.py
├─ domains/<domain>/
│   ├─ domain/                      # 순수 Python (Entity / VO / Service)
│   │   ├─ entity/
│   │   ├─ value_object/
│   │   └─ service/
│   ├─ application/                 # UseCase + Port + Request/Response DTO
│   │   ├─ usecase/
│   │   ├─ port/                    # 외부 의존성 인터페이스
│   │   ├─ request/
│   │   └─ response/
│   ├─ adapter/
│   │   ├─ inbound/api/             # FastAPI 라우터
│   │   └─ outbound/                # Persistence / External / Cache
│   │       ├─ persistence/
│   │       ├─ external/
│   │       └─ cache/
│   └─ infrastructure/              # ORM Model / Mapper
│       ├─ orm/
│       └─ mapper/
└─ infrastructure/                  # 전역 인프라 (DB / Redis / Scheduler / LLM)
    ├─ config/
    ├─ database/
    ├─ cache/
    ├─ scheduler/
    ├─ langgraph/
    └─ external/
```

레이어 의존성 규칙(`CLAUDE.md` 명시):
- `Adapter → Application → Domain` (단방향)
- `Domain` 레이어는 FastAPI / SQLAlchemy / Redis / Pydantic / HTTP / ENV 일체 import 금지 — pure Python
- `Application` 은 Port 만으로 외부 시스템에 접근 (직접 import 금지)
- `Infrastructure → Adapter / Application` (역방향)

### 2.2 프론트엔드 — Feature-based DDD

```
features/<feature>/
├─ domain/          # model / state / intent (pure types)
├─ application/     # atoms (Jotai) / selectors / commands / hooks
├─ infrastructure/  # api 호출 (fetch via httpClient)
└─ ui/              # Dumb Components 만 (비즈니스 로직 금지)

ui/                  # 공통 컴포넌트 (Navbar 등)
infrastructure/      # httpClient / env config
app/                 # Next.js App Router (entry point — Application Hook 호출만)
```

---

## 3. 백엔드 도메인 전수 매핑

총 **24개 도메인** + 인증/공통 인프라.

| 도메인 | API Prefix | 역할 |
|--------|-----------|------|
| `agent` | `/api/v1/agent` | **메인 에이전트 오케스트레이터** — 뉴스·공시·재무 3개 서브에이전트를 병렬 호출 후 통합 시그널 산출 (`/query`, `/history`, `/finance-analysis`) |
| `api_schema` | `/api/v1/agent-schema` | 에이전트 스키마 메타데이터 |
| `account` | `/api/v1/account`, `/api/v1/users` | 계정 / 회원가입 / 관심종목(watchlist) CRUD |
| `auth` | `/api/v1/auth` | 로컬 로그인 / 세션 관리 (Redis 세션 토큰) |
| `authentication` | `/authentication` | `/me` 엔드포인트 (user_token + temp_token 양쪽 허용) |
| `kakao_auth` | `/api/v1/kakao-authentication` | 카카오 OAuth — `temp_token` → `user_token` 전환 |
| `board` | `/api/v1/board` | 게시판 (CRUD) |
| `post` | `/api/v1/post` | 포스트 |
| `news` | `/api/v1/news`, `/api/v1/news/collect` | 뉴스 검색 / 저장 / 분석 / 관심기사 / 워치리스트 피드 / Naver·SerpAPI 수집 |
| `disclosure` | `/api/v1/disclosure` | DART 공시 / 회사 정보 / RAG chunk / SEC EDGAR (US) / 잠정실적 수집 / 핵심공시 처리 |
| `stock` | `/api/v1/stock` | 종목 마스터 / 재무 비율(DART) / 잠정실적 페처 / 벡터 임베딩 / 일봉 / 인기종목 / 이벤트 임팩트 |
| `stock_theme` | `/api/v1/stock-theme`, `/api/v1/stocks` | 테마 시드 / 테마별 종목 / 추천 / 방위산업 시드 |
| `dashboard` | `/api/v1/dashboard` | 메인 대시보드 — Nasdaq 일봉 / 거시 데이터 / 경제 이벤트 / 주식 일봉 / 자산 타입 |
| `history_agent` | `/api/v1/history-agent` | **이상치 감지(Anomaly) → 인과관계 추론** — 일봉 이상치 탐지 + 거시 이벤트 매칭 + LLM 타이틀 생성 |
| `macro` | `/api/v1/macro` | **시장 위험도 판단** — YouTube 댓글 + LLM + Redis 4h 캐시 영속화 |
| `market_analysis` | `/api/v1/market-analysis` | 시장 질문 분석 (LLM 기반 Q&A) |
| `market_video` | `/api/v1/youtube` | 유튜브 비디오/댓글 수집 + 키워드 추출(kiwipiepy) + 워치리스트 피드 |
| `investment` | `/api/v1/investment` | 투자 의사결정 (YouTube 영상/댓글/뉴스 기반) |
| `schedule` | `/api/v1/schedule` | 경제 이벤트 / 잠정실적 일정 / 알림 |
| `sentiment` | `/api/v1/sentiment` | SNS 게시물 수집 + 감성 분석 |
| `smart_money` | `/api/v1/smart-money` | **외국인·기관 자금흐름** — 글로벌 포트폴리오(13F) + KR 포트폴리오 + 집중매수 + investor_flow 트렌드 |
| `company_profile` | `/api/v1/company-profile` | 회사 프로필 — DART 회사 정보 + RAG 사업 개요(LLM 요약) + SEC company name + 자산 타입 |
| `study` | `/api/v1/study` | 학습 영상 |
| `causality_agent` | (내부) | history_agent 내부에서 사용되는 macro 인과관계 추론 |

### 3.1 핵심 모듈: `agent` 도메인 (가장 무거운 도메인)

`/agent/query` (POST) 흐름 — `app/domains/agent/application/usecase/process_agent_query_usecase.py`:

```
1. 요청 수신 (ticker, query, session_id)
2. 회사 사업개요 fetch (asyncio.create_task) — 7일 Redis 캐시
3. PostgreSQL 1시간 캐시 조회 (IntegratedAnalysisRepository)
   └─ HIT  → 캐시 결과 + overview 즉시 반환
   └─ MISS → 4번 진행
4. 3개 서브에이전트 병렬 호출 (asyncio.gather, return_exceptions=True)
   ├─ NewsSubAgent       : Naver/SerpAPI 뉴스 → LLM signal 추론 (KR/US 분기)
   ├─ DisclosureSubAgent : DART 공시 / SEC EDGAR 8-K·10-K·10-Q → LLM 분석
   └─ FinanceSubAgent    : DART 재무비율 + 잠정실적 / yfinance(US) → LLM 분석
5. _aggregate_signals() — Source Tier 가중 평균
   └─ HIGH(1.0) / MEDIUM(0.7) / MEDIUM_LOW(0.5) / LOW(0.3) 멀티플라이어
   └─ 기본 티어: news=MEDIUM, disclosure=HIGH, finance=HIGH
   └─ feature flag: enable_source_tier_weighting (env)
6. LLM Synthesis (OpenAI) — 4개 결과 + 사업개요를 컨텍스트로 종합 답변/key_points 생성
7. Postgres 저장 (전체 성공 시) — IntegratedAnalysisRepository
8. AgentQueryResponse 반환 → FrontendAgentResponse 로 변환
```

서브에이전트 어댑터:
- `news_sub_agent_adapter.py` — KR 은 `NaverNewsClient`, US 는 SerpAPI 라우팅
- `finance_sub_agent_adapter.py` — KR 은 DART(`opendart_financial_data_provider`) + 잠정실적, US 는 yfinance(`yfinance_financial_data_provider`)
- `disclosure_sub_agent_adapter.py` — KR 은 DART, US 는 SEC EDGAR (CIK 매핑 + `submissions/CIK*.json`)
- `langgraph_finance_agent_provider.py` — LangGraph 기반 RAG 재무 분석 (벡터 DB chunk 검색 → LLM 추론)
- `openai_synthesis_client.py` — 통합 답변 합성 LLM

도메인 VO:
- `source_tier.py` — `SourceTier(HIGH/MEDIUM/MEDIUM_LOW/LOW)` + `default_multiplier()` (env tunable)
- `sector.py` — `Sector(ENTERTAINMENT/TECH/FINANCE/BIO/...)` + `SectorOverride` (엔터 SNS 승격용)

### 3.2 데이터 영속화

#### PostgreSQL (`AsyncSession` + SQLAlchemy 2.x)
주요 ORM 테이블 (`main.py` 에서 일괄 import 후 `Base.metadata.create_all`):

- 계정/관심종목: `account_orm`, `user_watchlist_orm`
- 뉴스: `saved_article_orm`, `user_saved_article_orm`, `article_content_orm`, `collected_news_orm`, `investment_news_orm`
- 게시판: `board_orm`, `post_orm`
- 주식: `stock_vector_document_orm`, `stock_theme_orm`, `daily_bar_orm`, `popular_stock_ticker_orm`, `event_impact_metric_orm`
- 공시: `company_orm`, `company_data_coverage_orm`, `disclosure_orm`, `disclosure_document_orm`, `collection_job_orm`, `collection_job_item_orm`, `rag_document_chunk_orm`
- 에이전트: `integrated_analysis_orm` (1시간 캐시)
- 인베스트먼트: `investment_youtube_log_orm`, `investment_youtube_video_orm`, `investment_youtube_video_comment_orm`, `investment_news_content_orm`
- 스케줄/매크로: `economic_event_orm`, `nasdaq_bar_orm`, `event_enrichment_orm`
- 스마트머니: `investor_flow_orm`, `global_portfolio_orm`, `kr_portfolio_orm`

#### pgvector (별도 Vector DB)
- `VectorBase` + `vector_engine` — `CREATE EXTENSION IF NOT EXISTS vector` 자동 설치
- 종목 벡터 / RAG chunk 임베딩 (OpenAI embedding)

#### Redis
- 세션 토큰 (`session:`, `temp_token:` prefix) — `agent_router._require_auth`
- 매크로 스냅샷 4시간 영속화 (`MACRO_SNAPSHOT_REDIS_KEY`)
- 회사 사업개요 7일 캐시 (`RedisBusinessOverviewCache`)
- 회사 프로필 캐시 (`RedisCompanyProfileCache`)
- 자산 타입 캐시 (`CachedAssetTypeAdapter`)
- 재무 분석 결과 캐시 (`RedisFinanceAnalysisCache`)

### 3.3 백그라운드 스케줄러 (APScheduler — `disclosure_scheduler.py`)

`lifespan` 부트스트랩 시 다음 잡들이 등록되어 주기 실행:

| 잡 | 모듈 | 트리거 | 역할 |
|----|------|--------|------|
| `bootstrap` | `disclosure_jobs` | startup once | 빈 companies 테이블 초기 적재 |
| `collect_news` | `disclosure_jobs` | startup once | 뉴스 부트스트랩 |
| `incremental_collect` | `disclosure_jobs` | cron | DART 신규 공시 증분 수집 |
| `refresh_company_list` | `disclosure_jobs` | 24h cron | DART 회사 마스터 갱신 |
| `process_documents` | `disclosure_jobs` | cron | 미처리 공시 본문 처리 + RAG chunk 적재 |
| `bootstrap_nasdaq` | `nasdaq_jobs` | startup | 나스닥 일봉 적재 |
| `bootstrap_stock_bars` | `stock_bars_jobs` | startup | 종목 일봉 적재 |
| `refresh_market_risk` | `macro_jobs` | startup + cron | 거시 위험도 (YouTube + LLM) |
| `refresh_corp_earnings` | `corp_earnings_jobs` | 분기 + 주간 | 잠정실적 일정 수집 |
| `ar_calculation_jobs` | `ar_calculation_jobs` | cron | Abnormal Return 계산 |
| `macro_timeline_jobs` | `macro_timeline_jobs` | cron | 거시 타임라인 |
| `smart_money_jobs` | `smart_money_jobs` | cron | 외국인·기관 자금흐름 |

총 **20+ 개 add_job** 등록.

### 3.4 외부 API / SDK 연동

| 카테고리 | 클라이언트 |
|---------|----------|
| LLM | OpenAI (`openai_llm_client`, `openai_responses_client`), Anthropic (`anthropic`), LangChain (`langchain_llm_client`), LangGraph 그래프 |
| 검색 | SerpAPI (`serp_client`) |
| 뉴스(KR) | Naver Open API |
| 공시(KR) | DART OpenAPI (`opendart_*`, `dart_company_info_client`, `corp_code_mapper`) |
| 공시(US) | SEC EDGAR (`sec_edgar_api_client` — CIK + submissions, User-Agent 필수) |
| 시세(KR) | pykrx |
| 시세(US) | yfinance (`yfinance_financial_data_provider`, `yahoo_finance_daily_bar_fetcher`) |
| 자산타입 | Yahoo Finance (`yahoo_finance_asset_type_client`) |
| 거시 | FRED (`fred_investment_info_client`) |
| 비디오 | YouTube + youtube-transcript-api (자막 기반 분석) |
| NLP | kiwipiepy (한국어 명사 추출) |
| 휴일 | holidays |
| 트레이싱 | LangSmith (`langsmith_config`, env tunable) |

### 3.5 인증/세션 모델

- **temp_token**: 카카오 OAuth 첫 콜백 시 발급 (가입 전 임시) — `kakao_auth/usecase/issue_temp_token_usecase.py`
- **user_token**: 정식 회원가입 후 (signup 완료) — `auth/usecase/login_usecase.py` 또는 `kakao_auth/usecase/issue_user_token_usecase.py`
- **세션 저장**: Redis (`session:{token}` / `temp_token:{token}`)
- **인증 체크**: `agent_router._require_auth()` — 양쪽 토큰을 모두 허용해 401 UX 일관성 확보 (쿠키 + Bearer 헤더 모두 지원)

### 3.6 캐시 계층

| 계층 | TTL | 대상 |
|------|-----|------|
| Redis 세션 | settings.session_ttl | user_token, temp_token |
| Redis 매크로 | 4h | 시장 위험도 스냅샷 (YouTube quota 절약) |
| Redis 사업개요 | 7d | 회사 사업개요 (LLM 요약 결과) |
| Redis 회사프로필 | settings | DART 회사 정보 + 자산 타입 |
| Redis 재무분석 | settings.finance_analysis_cache_ttl_seconds | LangGraph 재무 분석 결과 |
| PostgreSQL 통합분석 | 1h | `integrated_analysis_orm` (ProcessAgentQueryUseCase) |
| In-memory store | process lifetime | `MarketRiskSnapshotStore` (Redis 복원 후 채움) |

---

## 4. 백엔드 핵심 기능 상세

### 4.1 통합 에이전트 분석 (`POST /api/v1/agent/query`)

**입력**: `{ ticker: string, query?: string, session_id?: string }`

**출력**: `FrontendAgentResponse`
- `session_id`, `result_status`, `answer` (요약), `agent_results[]` (3개), `business_overview`, `total_execution_time_ms`

**핵심 로직** (Stage A~D 플랜이 모두 머지 완료):
- **Stage A**: 티커 키워드 하드코딩 8종목 → `TickerKeywordResolver` 동적 조회 (모든 KRX 종목 지원)
- **Stage B**: KR/US 시장 분기 (`MarketRegion`) — 뉴스/재무/공시 모두 라우팅
  - US 뉴스: SerpAPI `gl=us, hl=en`
  - US 재무: yfinance (`fetch_financial_ratios`, `fetch_recent_earnings`)
  - US 공시: SEC EDGAR (`8-K`, `10-K`, `10-Q` filing 리스트)
- **Stage C**: 잠정실적 페처 (`fetch_preliminary_earnings_usecase`) — DART `report_nm` 에 "영업(잠정)실적" 필터, 최근 120일 desc 정렬
- **Stage D**: 4단계 소스 티어 가중치 (HIGH/MEDIUM/MEDIUM_LOW/LOW) — 기사별(뉴스) + 에이전트 고정(공시·재무 = HIGH) 혼합. 섹터 오버라이드(엔터 → SNS 승격)

### 4.2 회사 프로필 + 사업개요 (`GET /api/v1/company-profile/{ticker}`)

- DART `corpInfo` + RAG chunk 기반 OpenAI 요약 (사업개요 LLM 추출)
- 7일 Redis 캐시
- US 종목은 SEC EDGAR 회사명 매핑 (`SecCompanyNameAdapter`)
- 자산 타입(`stock`/`etf`/...) 은 yfinance + Redis 캐시

### 4.3 History Agent — 이상치 → 인과관계 (`/api/v1/history-agent/*`)

1. `detect_anomaly_bars_usecase` — 일봉 이상치(가격/거래량 z-score) 탐지
2. `collect_important_macro_events_usecase` — 동일 시점 거시 이벤트(FOMC, CPI 등) 수집
3. `get_anomaly_causality_usecase` — 이상치 ↔ 거시 이벤트 매칭
4. `generate_titles_usecase` — LLM 으로 이벤트 제목/요약 생성
5. `history_agent_usecase` — 위 단계 통합 오케스트레이션
6. 결과: `event_enrichment_orm` 에 영속화

### 4.4 Smart Money — 자금 흐름 (`/api/v1/smart-money/*`)

- **글로벌**: 13F filings 기반 `global_portfolio_orm` — 워런 버핏 등 헤지펀드 보유 비중
- **KR**: 한국 외국인·기관 보유 비중 `kr_portfolio_orm`
- **investor_flow**: 일별 외국인/기관 순매수 트렌드 + 랭킹
- **집중매수**: KR/US 집중매수 종목 추출

### 4.5 Macro — 시장 위험도 (`/api/v1/macro/*`)

- YouTube 거시 채널 영상 자막 + 댓글 → LLM (`judge_market_risk_usecase`)
- 결과: `MarketRiskJudgementResponse` — 위험도 점수 + 핵심 이슈
- Redis 4h 영속화 + 메모리 store — hot-reload 시에도 LLM 재호출 회피

### 4.6 Investment — 투자 의사결정 (`/api/v1/investment/*`)

- YouTube 영상 + 댓글 + 뉴스 통합 분석 → LLM 투자 의사결정 (`investment_decision_usecase`)
- 일별 로그 적재 (`investment_youtube_log_orm`)

### 4.7 News — 다층 뉴스 파이프라인 (`/api/v1/news/*`)

- 검색: `search_news_usecase` (Naver / SerpAPI)
- 수집: `collect_naver_news_usecase` + `news_collect_router`
- 시그널: `analyze_news_signal_usecase` — 동적 키워드 해석 + LLM signal
- 저장: `save_article_usecase`, `save_user_article_usecase`, `save_interest_article_usecase`
- 워치리스트 피드: `get_watchlist_news_feed_usecase`
- 본문 분석: `analyze_article_usecase`

### 4.8 Disclosure — DART + SEC + RAG (`/api/v1/disclosure/*`)

- `refresh_company_list_usecase` — DART 회사 코드 마스터
- `incremental_collect_usecase` / `seasonal_collect_usecase` / `collect_top300_companies_usecase` / `on_demand_collect_usecase` — 다양한 수집 모드
- `process_disclosure_documents_usecase` — 본문 다운로드 + 파싱
- `store_rag_chunks_usecase` + `batch_store_documents_usecase` — RAG chunk 적재 (pgvector)
- `analyze_company_usecase` — 회사 종합 분석
- `cleanup_expired_data_usecase` — 만료 데이터 정리
- `detect_uncovered_companies_usecase` — 커버리지 모니터링

### 4.9 Schedule — 경제 이벤트 + 알림 (`/api/v1/schedule/*`)

- `sync_economic_events_usecase` — FRED 기반 경제 이벤트 동기화
- `run_event_impact_analysis_usecase` — 이벤트 임팩트 분석
- `list_schedule_notifications_usecase` / `mark_schedule_notification_read_usecase` — 알림

### 4.10 Sentiment — SNS 감성 (`/api/v1/sentiment/*`)

- `collect_sns_posts_usecase` — SNS 게시물 수집
- `analyze_sns_signal_usecase` — 감성 + 시그널 추출

### 4.11 Market Video — YouTube 분석 (`/api/v1/youtube/*`)

- `collect_and_save_videos_usecase` / `collect_defense_video_usecase` — 영상 수집
- `collect_video_comments_usecase` — 댓글 수집
- `extract_nouns_usecase` / `extract_comment_nouns_usecase` — kiwipiepy 한국어 명사 추출
- `get_watchlist_youtube_feed_usecase` — 워치리스트 종목 영상 피드

---

## 5. 프론트엔드 분석

### 5.1 라우트 구조 (Next.js 16 App Router)

| 라우트 | 역할 |
|--------|------|
| `/` | Home — 통합 대시보드 / 진입 페이지 |
| `/login` | 로컬 로그인 |
| `/auth-callback` | 카카오 OAuth 콜백 |
| `/account/signup` | 회원가입 (temp_token → user_token) |
| `/dashboard` | 메인 대시보드 (Nasdaq + 거시 + 경제 이벤트) |
| `/stock` | 종목 검색/선택 |
| `/stock-recommendation` | 추천 종목 |
| `/news` | 뉴스 메인 |
| `/news/article/[id]` | 기사 상세 |
| `/news/saved` | 저장한 기사 |
| `/board`, `/board/create`, `/board/edit/[id]`, `/board/read/[id]` | 게시판 CRUD |
| `/company-profile` | 회사 프로필 + 사업개요 카드 |
| `/smart-money` | Smart Money 대시보드 |
| `/smart-money/global-portfolio` | 글로벌 13F 포트폴리오 |
| `/youtube` | YouTube 분석 |
| `/settings/watchlist` | 관심종목 관리 |
| `/terms`, `/terms/service`, `/terms/privacy`, `/terms/child-protection` | 약관 |

### 5.2 Feature 모듈 (9개)

| Feature | 역할 | 주요 의존 백엔드 API |
|---------|------|---------------------|
| `auth` | 로그인 / 콜백 / 세션 관리 | `/auth/login`, `/authentication/me`, `/kakao-authentication/*` |
| `board` | 게시판 | `/board/*` |
| `company-profile` | 회사 프로필 + 사업개요 | `/company-profile/{ticker}` |
| `dashboard` | 메인 대시보드 | `/dashboard/*` (nasdaq, macro, events) |
| `news` | 뉴스 | `/news/*`, `/news/collect`, 사용자 기사 |
| `smart-money` | 자금흐름 | `/smart-money/*` (글로벌·KR 포트폴리오, investor flow) |
| `stock-recommendation` | 종목 추천 | `/stocks?theme=`, `/stock-theme/*` |
| `watchlist` | 관심종목 | `/users/me/watchlist`, `/account/*` |
| `youtube` | 유튜브 분석 | `/youtube/*` (영상/댓글/명사) |

각 feature 는 `domain/`(pure types) → `application/`(Jotai atoms + hooks) → `infrastructure/`(httpClient API) → `ui/`(Dumb Components) 4계층.

### 5.3 상태 관리

- **Jotai** (전역 상태) — 각 feature `application/atoms` 에 atom 정의
- **Selectors / Commands / Hooks** — atom 조작은 hooks 에서만, UI 는 hooks 만 호출
- **Server state** — fetch 직접 호출 (React Query 미사용, infrastructure layer 에서 추상화)

### 5.4 차트/시각화

- `lightweight-charts` ^5.1 — 일봉/주봉 캔들차트 (TradingView 라이브러리)
- `recharts` ^3.8 — 대시보드 라인/바 차트

### 5.5 스타일/타입

- Tailwind CSS 4 + `@tailwindcss/postcss`
- TypeScript 5.9.3 strict 모드
- ESLint 9 + `eslint-config-next` 16
- 경로 별칭 `@/*` → 프로젝트 루트 (`@/features/...`, `@/ui/...`, `@/app/...`)

---

## 6. 환경 / 설정

### 6.1 백엔드 (`requirements.txt`)

```
# Web
fastapi>=0.115.0, uvicorn>=0.34.0, pydantic-settings>=2.7.0
# DB
sqlalchemy>=2.0.0, alembic>=1.14.0, asyncpg>=0.29.0, pgvector>=0.3.0
# Cache
redis>=5.0.0
# Auth
python-jose[cryptography]>=3.3.0, cryptography>=42.0.0
# AI/LLM
openai>=1.75.0, anthropic>=0.40.0, langchain>=0.3.0, langchain-openai>=0.3.0,
langgraph>=0.3.0, langsmith>=0.2.0
# HTTP/Scraping
httpx>=0.27.0, beautifulsoup4>=4.12.0, youtube-transcript-api>=0.6.0
# NLP
kiwipiepy>=0.17.0, numpy>=2.0.0
# Scheduler
apscheduler>=3.10.0
# Market data
yfinance>=0.2.0, pykrx>=1.0.45
# Calendar
holidays>=0.50
```

### 6.2 프론트엔드 (`package.json`)

```json
{
  "dependencies": {
    "jotai": "^2.19.0",
    "lightweight-charts": "^5.1.0",
    "next": "^16.2.4",
    "react": "19.2.3",
    "recharts": "^3.8.1"
  },
  "devDependencies": {
    "tailwindcss": "^4",
    "typescript": "5.9.3",
    "eslint": "^9",
    "eslint-config-next": "16.1.6"
  }
}
```

### 6.3 주요 ENV 키 (`Settings`)

- `openai_api_key`, `anthropic_api_key`
- `openai_finance_agent_model`, `openai_embedding_model`, `finance_rag_top_k`
- `langsmith_tracing`, `langsmith_api_key`, `langsmith_project`, `langsmith_endpoint`
- `sec_edgar_user_agent` (SEC EDGAR 호출 시 필수)
- `enable_us_tickers` (feature flag, 미국 종목 활성화)
- `enable_source_tier_weighting` (feature flag, Stage D 가중치)
- `tier_multiplier_high/medium/medium_low/low` (튜닝)
- `cors_allowed_frontend_url`
- `finance_analysis_cache_ttl_seconds`
- DB / Redis 연결 정보

### 6.4 인프라

- **Docker** — `Dockerfile` + `docker-compose.yml` 백엔드 컨테이너화
- **Alembic** — DB 마이그레이션 관리
- **포트** — 백엔드 33333, 프론트엔드 3000

---

## 7. 운영/개발 워크플로우

### 7.1 Git PR 워크플로우 (`CLAUDE.md` 강제)

- main 직접 푸시 금지
- fork (origin: 사용자 fork, ex: `K-MG-0328/antelligen-backend`) 에 작업 브랜치 생성 후 푸시
- `origin/branch` → `EDDI-RobotAcademy/main` PR 생성
- **merge commit** 으로 머지 (squash 금지 — 원본 SHA 보존)
- 머지 후 fork sync: `git fetch upstream && git merge --ff-only upstream/main && git push origin main`
- 머지된 작업 브랜치는 로컬/원격 양쪽에서 삭제

### 7.2 개발 명령어

```bash
# Backend
uvicorn main:app --reload --host 0.0.0.0 --port 33333
python main.py

# Frontend
npm run dev      # Next.js dev server
npm run build    # 프로덕션 빌드
npm run lint
npm run typecheck
```

### 7.3 ADR 기록

- `docs/adr/0001-period-as-candle-interval.md` — `period` → `chart_interval` / `lookback_range` 명명 분리

---

## 8. 핵심 설계 패턴 요약

1. **Hexagonal + DDD** — Domain 레이어 외부 의존성 0 (FastAPI/SQLAlchemy/Redis 일체 import 금지) → 테스트 용이 + 교체 용이
2. **Port/Adapter** — Application 은 Port (인터페이스) 만 의존, 구현 어댑터는 `adapter/outbound/` — 외부 SDK 변경 시 어댑터만 교체
3. **DI 와이어링** — `main.py` 또는 라우터 레벨에서 `Depends` 로 주입 (글로벌 컨테이너 미사용)
4. **다중 캐시 레이어** — Redis(분 단위) + Postgres(시간 단위) + In-memory(프로세스) 3중 — LLM/외부 API quota 절약 우선
5. **병렬 서브에이전트** — `asyncio.gather(return_exceptions=True)` 로 부분 실패 허용 (한 에이전트가 죽어도 나머지는 살림)
6. **Source Tier 가중** — 4단계 (HIGH=1.0/MEDIUM=0.7/MEDIUM_LOW=0.5/LOW=0.3), env tunable, 섹터 오버라이드 (엔터)
7. **시장 분기 (`MarketRegion`)** — 한 종목 코드로 KR/US 자동 라우팅 (뉴스/재무/공시 모두)
8. **Feature flag** — `enable_us_tickers`, `enable_source_tier_weighting` 으로 점진 롤아웃

---

## 9. 주요 진행 상황 (2026-04-28 기준)

| 단계 | 상태 |
|------|------|
| Stage A — 티커 제한 해제 + MarketRegion 스캐폴딩 | ✅ 완료 |
| Stage B — 미국 종목 지원 (뉴스+재무+공시) | ✅ 완료 |
| Stage C — 잠정실적 페처 (DART) | ✅ 완료 |
| Stage D — 소스 티어 가중치 시스템 | 🟡 진행 중 |
| Business Overview (VO + Port + OpenAI 어댑터 + Redis 캐시 + Frontend UI) | ✅ 완료 |
| US 지원 — 백엔드 | ✅ 완료 |
| US 지원 — 프론트엔드 | 🟡 진행 중 |

---

## 10. 한눈에 보는 데이터 흐름

```
사용자 (브라우저)
   │ Next.js App Router (/dashboard, /stock, ...)
   ▼
프론트엔드 Feature
  features/<f>/ui  →  application/hooks  →  application/atoms (Jotai)
                                          ↓
                                infrastructure/api (httpClient)
                                          ↓
   ┌─────────────────────────────────────────────────────────────┐
   │                  /api/v1/* (FastAPI)                         │
   │  Adapter/inbound  →  Application/UseCase  →  Domain          │
   │                            ↓                                  │
   │                   Application/Port                            │
   │                            ↓                                  │
   │                Adapter/outbound                               │
   │   ┌──────────────────┬───────────────────┬────────────────┐   │
   │   │ Persistence      │ External           │ Cache          │   │
   │   │ (Postgres+vector)│ (DART/SEC/         │ (Redis)        │   │
   │   │                  │  Naver/SerpAPI/    │                │   │
   │   │                  │  yfinance/         │                │   │
   │   │                  │  YouTube/FRED/     │                │   │
   │   │                  │  OpenAI/Anthropic) │                │   │
   │   └──────────────────┴───────────────────┴────────────────┘   │
   │                            ▲                                  │
   │                  Infrastructure/Scheduler                     │
   │                  (APScheduler 20+ jobs)                       │
   └─────────────────────────────────────────────────────────────┘
```

---

이 문서는 두 리포지토리의 코드 구조 / 도메인 / API / 외부 연동 / 캐시 / 스케줄러 / 인증 / 배포 / 운영 워크플로우를 코드 레벨에서 추출한 1차 분석본이며, 세부 비즈니스 로직(예: LLM 프롬프트, 잠정실적 숫자 추출 휴리스틱, 이상치 z-score 임계값)은 각 UseCase 파일 본문 참조.
