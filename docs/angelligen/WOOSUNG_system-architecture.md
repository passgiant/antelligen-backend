# Antelligen Backend — System Architecture

> FastAPI + Hexagonal Architecture + DDD 기반 멀티 에이전트 투자 분석 백엔드

---

## 0. Clean Architecture 핵심 개념

클린 아키텍처는 소프트웨어의 **관심사 분리**를 극대화한 구조이며, 가장 큰 특징은 **의존성 규칙(Dependency Rule)** 입니다.
**모든 의존성은 외부에서 내부(도메인)로 향해야 합니다.**

```
   ┌──────────────────────────────────────────────┐
   │  Frameworks & Drivers (React, Axios, DB, …)  │  ← 가장 바깥
   │  ┌────────────────────────────────────────┐  │
   │  │  Interface Adapters (Controller, …)    │  │
   │  │  ┌──────────────────────────────────┐  │  │
   │  │  │  Use Cases (애플리케이션 로직)    │  │  │
   │  │  │  ┌────────────────────────────┐  │  │  │
   │  │  │  │  Entities (핵심 비즈니스)   │  │  │  │  ← 가장 안쪽
   │  │  │  └────────────────────────────┘  │  │  │
   │  │  └──────────────────────────────────┘  │  │
   │  └────────────────────────────────────────┘  │
   └──────────────────────────────────────────────┘
                의존성 방향: 바깥 → 안쪽
```

### 핵심 계층 구조

| 계층 | 역할 | 예시 |
|------|------|------|
| **Entities** | 핵심 비즈니스 모델 및 규칙 | `User`, `Product` 객체 정의 |
| **Use Cases** | 애플리케이션 고유의 비즈니스 로직 | "로그인하기", "장바구니 담기" 흐름 |
| **Interface Adapters** | 외부 데이터 ↔ 내부 형식 변환 | API 응답을 UI 모델로 매핑, Presenter |
| **Frameworks & Drivers** | 가장 바깥쪽 기술 도구 | React, Vue, Axios, LocalStorage |

### Frontend 관점의 이점

- **프레임워크로부터 독립**
  비즈니스 로직이 특정 라이브러리(React, Vue)에 종속되지 않습니다.
  예: React → Next.js로 전환해도 UI 컴포넌트만 교체하면 끝, 핵심 로직(Use Cases)은 그대로 재사용.

- **요구사항 변경에 유연한 대응**
  백엔드 API 명세가 바뀌거나(DB 변경), UI 디자인이 완전히 갈아엎어져도 Use Case 계층은 수정 불필요.
  어댑터나 컴포넌트만 수정하면 됩니다.

- **코드의 가독성과 협업 효율성**
  기능별로 역할이 명확히 나뉘어 팀 협업과 신규 인원 온보딩이 쉬워집니다.

---

## 1. Hexagonal Architecture 개념

### Hexagonal Architecture란?

- 클린 아키텍처를 구현하는 **가장 대표적인 모델**
- 애플리케이션의 **핵심을 중심**에 두고, 외부 시스템(UI, DB, API, 파일 시스템 등)과의 연결을 **포트(Port)와 어댑터(Adapter)** 로 분리하는 구조

```
              ┌──────────────────────────┐
   HTTP ─────▶│  Inbound Adapter (API)   │──┐
              └──────────────────────────┘  │
                                            ▼
              ┌──────────────────────────────────┐
              │           Inbound Port           │
              ├──────────────────────────────────┤
              │                                  │
              │      Core Domain (UseCase)       │
              │   — 외부 기술을 전혀 알지 못함 —  │
              │                                  │
              ├──────────────────────────────────┤
              │           Outbound Port          │
              └──────────────────────────────────┘
                                            │
              ┌──────────────────────────┐  │
   DB    ◀───│ Outbound Adapter (Repo)  │◀─┤
   API   ◀───│ Outbound Adapter (HTTP)  │◀─┘
              └──────────────────────────┘
```

### 왜 필요한가? — 기존 계층형의 한계

- **강한 결합도(Tight Coupling)**
  비즈니스 로직이 특정 DB나 프레임워크에 종속.
  → DB를 바꾸면 핵심 로직도 수정해야 하는 상황 발생.

- **테스트의 어려움**
  순수 비즈니스 로직만 테스트하고 싶지만, DB나 외부 API가 연결되어 있어야만 테스트 가능한 경우가 많음.

- **중심의 실종**
  애플리케이션의 핵심인 '비즈니스 로직'이 아닌 '데이터베이스'가 설계의 중심이 되기 쉬움.

### 포트 / 어댑터의 필요성

| 구성 요소 | 역할 |
|----------|------|
| **핵심 도메인 (Core)** | 본질적인 비즈니스 규칙. 외부 기술을 전혀 알지 못함. UI / DB / 외부 서비스를 교체해도 변경 불필요 |
| **포트 (Ports)** | 핵심 로직으로 들어오거나 나가는 '통로'. 주로 **인터페이스(Interface)** 로 정의. 핵심 로직은 외부 기술의 상세 구현을 몰라도 되므로 결합도 ↓, 유지보수 ↑ |
| **어댑터 (Adapters)** | 포트에 연결되는 실제 구현. DB나 외부 API를 **부품을 갈아 끼우듯** 교체·확장 가능 |

---

## 2. Antelligen 시스템 개요

Antelligen Backend는 위 원칙을 따라 **23개 도메인**으로 구성된 모듈형 백엔드로, 한국·미국 주식 시장에 대한 다음 기능을 제공합니다.

- 시세 / 일봉 / 거시지표 자동 수집
- 공시 · 뉴스 · 유튜브 콘텐츠 RAG 분석
- LLM 기반 멀티 에이전트 통합 분석 (`agent` 도메인)
- 거시 리스크 판정, 이벤트 임팩트 분석, 종목 추천

핵심 특징:

| 항목 | 내용 |
|------|------|
| 아키텍처 | Hexagonal (Ports & Adapters) + DDD |
| 동시성 | 전 라우트 `async def`, asyncpg / httpx 비동기 I/O |
| 백그라운드 | APScheduler 기반 7종 정기 작업 |
| 데이터 | PostgreSQL 16 + pgvector, Redis 캐시 |
| LLM | OpenAI · Anthropic · LangChain · LangGraph |

---

## 3. 기술 스택

### Runtime
- **Python 3.13** (`python:3.13-slim`, uv 패키지 매니저)
- **FastAPI ≥ 0.115** / **Uvicorn ≥ 0.34** (포트 33333)

### Data
- SQLAlchemy 2.0 (async) + Alembic
- asyncpg + pgvector
- Redis 5.x (asyncio)

### AI / LLM
- OpenAI ≥ 1.75 (GPT-4o, GPT-4o Mini, o1)
- Anthropic ≥ 0.40 (Claude)
- LangChain ≥ 0.3 / LangGraph ≥ 0.3 / LangSmith ≥ 0.2

### Market & NLP
- yfinance, pykrx, holidays
- kiwipiepy (한국어 형태소 분석)
- youtube-transcript-api, beautifulsoup4

### Infrastructure
- APScheduler 3.10 (스케줄링)
- python-jose + cryptography (JWT)

---

## 4. 헥사고날 + DDD 레이어 적용

```
┌─────────────────────────────────────────────────┐
│                Adapter (Inbound)                │
│   FastAPI Router  →  Request DTO                │
└─────────────────────────────────────────────────┘
                       │
┌─────────────────────────────────────────────────┐
│                Application                      │
│   UseCase  ←→  Port (Interface)                 │
└─────────────────────────────────────────────────┘
                       │
┌─────────────────────────────────────────────────┐
│                  Domain                         │
│   Entity · Value Object · Domain Service        │
│   (순수 Python — FastAPI / SQLAlchemy 금지)     │
└─────────────────────────────────────────────────┘
                       │
┌─────────────────────────────────────────────────┐
│        Adapter (Outbound) + Infrastructure      │
│   Repository Impl · External Client · ORM       │
└─────────────────────────────────────────────────┘
```

### 레이어별 MUST 규칙

| 레이어 | 허용 | 금지 |
|--------|------|------|
| Domain | 순수 Python | FastAPI · SQLAlchemy · Redis · Pydantic · HTTP Client · ORM Model · env |
| Application | UseCase, Port 호출 | FastAPI · ORM 직접 사용 · Redis · External API Client 직접 호출 |
| Adapter (Inbound) | Router, DTO 변환 | 비즈니스 로직 작성 |
| Adapter (Outbound) | Repository / External Client 구현 | 도메인 규칙 침범 |
| Infrastructure | DB Session · ORM · Redis · env | — |

### 디렉토리 패턴

```
app/domains/<domain>/
├── domain/           # entity, value_object, service
├── application/      # usecase, request, response
├── adapter/
│   ├── inbound/api/  # FastAPI Router
│   └── outbound/     # repository, external client
└── infrastructure/   # orm, mapper
```

---

## 5. 도메인 맵 (23개)

### 사용자 · 인증
| 도메인 | 설명 |
|--------|------|
| `account` | 사용자 계정, 관심 종목 (Watchlist) |
| `auth` | JWT 토큰 발급 / 검증 |
| `kakao_auth`, `authentication` | Kakao OAuth2 소셜 로그인 |

### 시장 데이터
| 도메인 | 설명 |
|--------|------|
| `stock` | 주식 기본정보, 인기 종목 (yfinance) |
| `stock.market_data` | 일봉, 이벤트 임팩트 메트릭 |
| `stock_theme` | 테마 기반 종목 추천 (LLM) |
| `dashboard` | NASDAQ 선물, 테크 바로미터 |
| `smart_money` | 기관 / 외국인 자금 흐름, 글로벌·국내 포트폴리오 |
| `company_profile` | 기업 프로필 |

### 콘텐츠 · 분석
| 도메인 | 설명 |
|--------|------|
| `news` | 뉴스 검색·수집·분석 (SERP, Naver) |
| `disclosure` | DART 공시 수집 + RAG 청킹 + LLM 분석 |
| `market_video` | 투자 유튜브 영상 수집 |
| `market_analysis` | 시장 분석 리포트 |
| `macro` | 거시 리스크 판정 (YouTube + LLM) |
| `history_agent` | 역사적 주가 타임라인 · 인과관계 |
| `schedule` | 경제 일정 (FRED), 이벤트 임팩트 |
| `study` | 학습 콘텐츠 생성 |
| `investment` | 투자 콘텐츠 로깅 |

### 통합 에이전트
| 도메인 | 설명 |
|--------|------|
| `agent` | News · Disclosure · Finance 서브에이전트 통합 분석 |
| `api_schema` | 에이전트용 API 스키마 노출 |

### 커뮤니티
| 도메인 | 설명 |
|--------|------|
| `board`, `post` | 게시판 · 게시글 · 댓글 |

---

## 6. 인프라 레이어

`app/infrastructure/`

| 모듈 | 역할 |
|------|------|
| `config/settings.py` | Pydantic BaseSettings — DB · Redis · API 키 · LLM 모델 · feature flag |
| `config/logging_config.py` | 표준 로깅 |
| `config/langsmith_config.py` | LangSmith 추적 |
| `database/database.py` | AsyncEngine, AsyncSessionLocal (PostgreSQL + asyncpg) |
| `database/vector_database.py` | pgvector 초기화 |
| `cache/redis_client.py` | Redis async 싱글톤 |
| `external/openai_llm_client.py` | OpenAI 래퍼 |
| `external/langchain_llm_client.py` | LangChain ChatOpenAI 래퍼 |
| `external/openai_responses_client.py` | OpenAI o1 reasoning 모델 |
| `external/serp_client.py` | SERP API |
| `external/yahoo_ticker.py` | yfinance 정규화 |
| `scheduler/*.py` | APScheduler 작업 정의 |
| `agent/`, `langgraph/`, `nlp/` | 에이전트 오케스트레이션, 한국어 NLP |

---

## 7. 외부 연동

| 외부 시스템 | 용도 |
|------------|------|
| OpenAI / Anthropic | LLM 분석 · 요약 · 추천 |
| FRED | 미국 거시지표 (release_id 기반 호출) |
| yfinance | 미국·한국 주식 시세 |
| pykrx | 한국 거래소 데이터 |
| Open DART | 한국 기업 공시 |
| SERP API | 글로벌 뉴스 검색 |
| Naver | 한국 뉴스 크롤링 |
| YouTube Data API | 영상 메타데이터, 자막 |
| LangSmith | LLM 호출 추적 |
| PostgreSQL + pgvector | 메인 DB + RAG 임베딩 |
| Redis | 캐시 · 매크로 스냅샷 (TTL 4h) |

---

## 8. 라우팅 (`/api/v1`)

```
/api/v1/
 ├ account/                관심종목, 계정
 ├ auth/                   JWT 인증
 ├ kakao-authentication/   Kakao OAuth
 ├ stock/  · stocks/themes 시세, 테마
 ├ stock-theme/            테마 추천
 ├ news/  · news/collect   뉴스
 ├ disclosure/             공시
 ├ youtube/                영상
 ├ market-analysis/        시장 분석
 ├ macro/                  거시 리스크
 ├ history-agent/          역사적 분석
 ├ schedule/               경제 일정 / 이벤트 임팩트
 ├ company-profile/        기업 프로필
 ├ smart-money/            자금 흐름
 ├ dashboard/              나스닥, 테크 바로미터
 ├ agent/  · agent-schema  통합 에이전트
 ├ board/  · post/         커뮤니티
 ├ study/                  학습 콘텐츠
 ├ investment/             투자 콘텐츠
 └ health/                 헬스체크
```

라우터 통합점: `app/adapter/inbound/api/v1_router.py`

---

## 9. 백그라운드 작업 (APScheduler)

`main.py` lifespan에서 시작·종료, 부트스트랩과 catch-up 로직 포함.

| Job | 모듈 | 주기 |
|-----|------|------|
| 공시 수집 / 처리 / 회사목록 갱신 | `disclosure_jobs.py` | 분 단위 + bootstrap |
| 뉴스 수집 | `disclosure_jobs.py::job_collect_news` | 정기 |
| NASDAQ 지수 수집 | `nasdaq_jobs.py` | 일 1회 |
| 종목별 일봉 수집 | `stock_bars_jobs.py` | 일 1회 |
| 거시 리스크 스냅샷 | `macro_jobs.py` | 4h Redis TTL |
| 기업 실적 캘린더 | `corp_earnings_jobs.py` | 일 1회 |
| 경제 이벤트 동기화 | `schedule` 도메인 | 일 1회 |

---

## 10. LLM · 멀티 에이전트 오케스트레이션

```
                ┌──────────────────────┐
   User Query ─▶│   agent (통합)       │
                └──────────┬───────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  News SubAgent     Disclosure SubAgent   Finance SubAgent
  (SERP+LLM)        (DART RAG+LLM)        (yfinance+pykrx)
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                LangGraph 노드 → 최종 응답
                LangSmith 추적
```

- LLM 공급자 추상화: `llm_client_port.py` (Port) + `llm_client_provider.py` (Factory)
- OpenAI / Anthropic 환경변수로 스위치
- 거시 도메인 출처 표기 규칙: 모든 응답을 **Antelligen AI 자체 분석**으로 표기, 월가 IB 페르소나·존댓말

---

## 11. 데이터 흐름 (요청 처리)

```
HTTP Request
   ▼
FastAPI Router (Inbound Adapter)
   ▼
Request DTO 파싱
   ▼
UseCase 실행 (Application)
   ▼
Port 호출
   ├─▶ Repository (Outbound Adapter) ─▶ SQLAlchemy ─▶ PostgreSQL
   ├─▶ External Client                  ─▶ OpenAI / FRED / yfinance / DART
   └─▶ Cache Adapter                    ─▶ Redis
   ▼
Domain Entity 조작
   ▼
Response DTO 변환
   ▼
HTTP Response (BaseResponse 표준 포맷)
```

전역 예외 처리: `app/common/exception/global_exception_handler.py`
응답 표준: `app/common/response/base_response.py`

---

## 12. 명명 규칙 (ADR-0001)

| 의미 | 파라미터 | 허용 값 |
|------|---------|---------|
| 봉 단위 (candle interval) | `chart_interval` / `chartInterval` | `1D`, `1W`, `1M`, `1Q` |
| 조회 기간 (lookback) | `lookback_range` / `lookbackRange` | `1M`, `3M`, `6M`, `1Y`, `5Y`, `10Y` |

- `period`는 신규 코드에서 사용 금지 (deprecated alias만 유지)
- `1Y` chart_interval은 deprecated → 내부에서 `1Q`로 매핑 (yfinance 연봉 미지원)

---

## 13. 배포 · 운영

- **Dockerfile**: `python:3.13-slim` + uv 캐시 마운트
- **docker-compose.yml**: app + postgres + redis
- **Alembic**: `alembic/versions/` — 모든 ORM 변경은 마이그레이션 동반
- **헬스체크**: `/api/v1/health/` — DB · Redis ping
- **로깅**: stdout JSON, LangSmith로 LLM 트레이스 전송

---

## 14. 요약

- **23 도메인** · **11종 외부 API** · **7종 정기 작업** · **2종 LLM 공급자**
- 헥사고날 + DDD 규칙 강제: Domain은 순수 Python, 외부 의존성은 Port 통과
- 멀티 에이전트는 LangGraph로 조합, LangSmith로 관측
- 데이터 영속성: PostgreSQL (관계 + pgvector RAG) + Redis (캐시)
