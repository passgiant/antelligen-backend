# Antelligen — AI Multi-Agent 투자 인텔리전스 플랫폼

> 3·4차 프로젝트 발표 자료
> 발표일: 2026-05-02

---

## Slide 1 — 표지

### Antelligen

**AI Multi-Agent 기반 투자 인텔리전스 플랫폼**

> "AI가 대신 투자하는 시대가 아니라,
> AI의 판단을 사람이 검증하고 통제하는 구조"

- 발표일: 2026-05-02
- 팀: Antelligen (7인)

---

---

# Part 1. 문제 인식 (Problem)

---

## Slide 2 — 서비스 개발 동기

### 왜 우리는 멀티 에이전트인가

**단일 LLM 서비스의 구조적 한계**

- 단일 LLM은 **복잡한 문제를 체계적으로 분해**하기 어렵다
- 데이터 수집·분석·의사결정이 **하나의 모델에 과도 의존**
- 다양한 도메인(주식·뉴스·SNS·재무) 통합 반영 불가
- 확장성·유지보수에서 **구조적 한계** 발생

**현실의 의사결정은 협업 구조**

- 정보 수집 → 분석 → 판단 → 추천
- 여러 전문가의 협업 형태로 이루어짐
- 기존 AI 시스템은 이를 반영 못 함

→ **"역할별 AI 에이전트가 협업하는 구조"** 가 필요

---

## Slide 3 — 서비스 개발 목적

### Antelligen의 5가지 목표

1. **구조적 AI 시스템 구축** — 데이터 수집·분석·의사결정 에이전트 협업
2. **확장 가능한 아키텍처** — 새 기능 추가 시 기존 시스템 영향 최소화
3. **현실적 협업 흐름 반영** — 사람의 업무 방식 그대로 AI 협업으로 구현
4. **사용자 맞춤형 분석** — 개인 성향·관심 종목 기반 개인화
5. **자동화·효율성 향상** — 반복 분석 자동화, 실시간 데이터 반영

### 한 줄 결론

> **"AI 간 협업을 통해 문제를 해결하는 새로운 서비스 구조"**

---

## Slide 4 — TAM·SAM·SOM (시장 규모)

### Total Addressable Market (TAM)

**글로벌 AI 에이전트 시장**

- 2025년: 약 76억 달러
- 2033년: 약 **1,820억 달러 (≈ 240조 원)**
- 연평균 성장률: **약 50%**

**글로벌 예측 분석·의사결정 시장**

- 2030년: 약 823억 5천만 달러

### Serviceable Addressable Market (SAM)

- 국내 AI 시장 — 2024년 54.7억 달러 → 2032년 538.7억 달러
- BFSI(은행·금융·보험) — AI 도입 비중 가장 높은 산업군
- 주요 활용: 알고리즘 트레이딩 / 사기 탐지 / 위험 관리

### Serviceable Obtainable Market (SOM)

- 국내 금융 AI SW 비중 48.5% / 클라우드 성장률 34.9%
- **타겟 — 중소기업(SME) + 개인 투자자**
- 클라우드 기반 AI 웹서비스가 핵심 수익 모델

---

## Slide 5 — 고객의 핵심 Pain Points

### MAS 도입 고객의 3대 문제

**① 가시성 / 디버깅 (Observability)**

- 멀티 에이전트 = 블랙박스화 / 실패 원인 파악 어려움
- 요구: Tracing · 의사결정 시각화 · Tool 사용 로그

**② 비용 통제 (Cost Control)**

- 토큰 비용 급증(Runaway Cost) / 비효율 에이전트 루프
- 요구: 비용 추적 · 예산 관리 · 작업 최적화

**③ 거버넌스 / 보안 (Governance)**

- 금융 데이터 민감성 / PII 유출 / Prompt Injection
- 요구: 데이터 마스킹 · 정책 필터링 · Audit Trail

### 핵심 인사이트

> **"신뢰와 통제가 없는 AI는 금융에서 실패한다"**

---

---

# Part 2. 실현 가능성 (Solution)

---

## Slide 6 — 우리는 어떻게 풀었는가 (1/2)

### 데이터 신뢰도·커버리지 해결

| #   | 문제                   | 해결                                                        |
| --- | ---------------------- | ----------------------------------------------------------- |
| P-1 | 뉴스 8종목 제한        | `TickerKeywordResolver` Port — 전 KRX 2,500+ 종목           |
| P-2 | 미국 종목 미지원       | `MarketRegion` 추상 + SerpAPI / yfinance / SEC EDGAR        |
| P-3 | 잠정실적 누락          | `OpenDartPreliminaryEarningsProvider` — 어닝 갭 윈도우 포착 |
| P-4 | 출처 무관 단순 평균    | `SourceTier`(HIGH/MEDIUM/MEDIUM_LOW/LOW) 가중치             |
| P-5 | 엔터주 SNS 시그널 묻힘 | `_SECTOR_OVERRIDE` — 섹터별 소스 가중 보정                  |

### 핵심 원칙

> **"신호의 양을 늘리되, 신호의 품질을 메타데이터로 표현한다"**

---

## Slide 7 — 우리는 어떻게 풀었는가 (2/2)

### 운영·비용·UX 해결

| #    | 문제                       | 해결                                                    |
| ---- | -------------------------- | ------------------------------------------------------- |
| P-6  | LLM·YouTube quota 폭주     | 다층 캐시 (4h / 7d / 1d / 1h) + 조건부 startup          |
| P-7  | 동시 요청 → DART 중복 호출 | Redis 분산 락 (`SET NX EX`) + 멱등성 가드               |
| P-8  | 응답 지연 5~10초           | 1h Postgres 캐시 + 3-에이전트 병렬 + 사업개요 별도 task |
| P-9  | 시그널만 있고 맥락 없음    | `BusinessOverview` 카드 — RAG → LLM 요약, 7d 캐시       |
| P-10 | 1개 죽으면 전체 실패       | `asyncio.gather(return_exceptions=True)` 부분 실패 허용 |
| P-11 | "왜 이 결론?"              | LangSmith Tracing + 출처 영속화 + Explainable 가중치    |

### 6대 해결 원칙

1. 추상은 도메인에서, 실행은 어댑터에서
2. 시간을 캐시로 사면 LLM 비용은 떨어진다
3. 부분 실패는 기능, 전체 실패는 버그
4. 신호의 품질을 메타데이터로 표현
5. 동시성은 atomic primitive로
6. 거버넌스는 사후가 아닌 사전 설계

---

## Slide 8 — 경쟁사 분석

### 기술 프레임워크 경쟁자

| 프레임워크     | 강점                      | 한계               |
| -------------- | ------------------------- | ------------------ |
| **CrewAI**     | 역할 기반 협업            | 실행 비용 증가     |
| **AutoGen**    | 다중 대화 / Human-in-loop | 설정 복잡          |
| **LangGraph**  | 그래프 오케스트레이션     | 진입 장벽 높음     |
| **LlamaIndex** | RAG 데이터 통합           | 에이전트 제어 제한 |

### 서비스형 플랫폼

- **Lindy** — 노코드 AI 빌더 / 빠른 배포
- **AgentGPT / AutoGPT** — 목표 기반 자동 실행 (프로토타입)
- **기존 금융 도구** — 알고리즘 트레이딩 중심, 보안 강화

### 한 줄 요약

> 시장에는 "AI 빌더" 와 "트레이딩 도구" 는 많지만,
> **"검증 가능한 의사결정 과정"** 을 제공하는 서비스는 적다

---

## Slide 9 — Antelligen 차별화 방안

### 차별화 3축

**① 신뢰성 / 거버넌스 (핵심 경쟁력)**

- **Tracing** — LangSmith로 모든 LLM 입출력·latency 추적
- **Source Tier 가중치** — DART × 1.0 / Bloomberg × 0.7 / SNS × 0.3
- **Audit Trail** — `integrated_analysis_orm`에 sub_results JSON 영속화

**② 고도화된 데이터 통합**

- 심층 RAG (DART 사업보고서 → 사업개요 LLM 요약)
- 멀티 에이전트 (News / Disclosure / Finance / Sentiment / Macro)
- 한국 공시 + 미국 SEC + yfinance + 잠정실적 통합

**③ UX 차별화**

- 사업개요 카드 — "이 회사 본질" 즉시 파악
- 부분 실패 표시 — "공시는 못 받았지만 뉴스+재무로 BULLISH"
- 한국·미국 종목 동일 UI/UX

### 핵심 메시지

> **"투자 결과가 아니라, 검증 가능한 의사결정 과정과
> 안전한 실행 구조를 제공하는 서비스가 시장 승자가 된다"**

---

---

# Part 3. 성장 전략 (Scale Up)

---

## Slide 10 — 시장 진입 전략

### 🎯 목표 고객

**1차 — 개인 투자자**

- "이 종목이 오늘 왜 떨어졌지?"를 검색하는 사용자
- 차트 + 사건 + 원인 분석을 한 화면에서

**2차 — 데이터 기반 판단을 원하는 사용자**

- 신입 애널리스트 / 투자 콘텐츠 크리에이터 / 학생 투자 동아리

**가격 차별화**

- 블룸버그 월 200만 원+ → **한국 공시 중심 + 합리적 가격**

### 🌐 진입 채널 — 웹 중심

```
초기: 웹사이트  →  PWA(홈 화면 추가)  →  모바일 앱 출시
```

### 🚀 사용자 확보

1. **SEO** — 종목별 "왜 떨어졌나" 페이지 자동 생성
2. **커뮤니티** — 디스코드 / 네이버 종목 카페 / 주식 갤러리
3. **인플루언서** — 투자 유튜버 협업 / 분석 데이터 콘텐츠

---

## Slide 11 — 목표 성과 (KPI)

### 📊 사용량 (Engagement)

| 지표         | 초기    | 확장     |
| ------------ | ------- | -------- |
| MAU          | 30~50명 | 10,000명 |
| 7일 재방문율 | 30%     | 40%      |

### 🎯 품질 (Quality)

| 지표                  | 초기 | 확장 |
| --------------------- | ---- | ---- |
| 사용자 만족도 (5점)   | 4.0  | 4.5  |
| "자신 있는 분석" 비율 | 30%  | 45%  |

### ⚡ 비용 효율 (Efficiency)

| 지표             | 초기  | 확장 |
| ---------------- | ----- | ---- |
| 응답 속도        | 8초   | 3초  |
| 종목당 분석 비용 | 200원 | 50원 |

### 💰 사업성 (Business)

- **유료 전환율 3%**
- **월 매출 100만 원** (1차 마일스톤)
- 앱 스토어 출시 (iOS / Android)

---

## Slide 12 — 서비스 확장 방안

### 🌍 방향 1 — 시장·자산 확장

- **시장**: 일본(니케이) / 유럽 / 신흥국
- **자산**: 암호화폐 / 원자재 / 채권 / 리츠
- **대안 데이터**: 커뮤니티 / 위성 / 카드 소비

### 🧩 방향 2 — 기능 확장

- 포트폴리오 분석 / 실시간 알림 / 백테스트
- 일일 리포트 / 주간 인사이트 / 종목 비교

### 🧠 방향 3 — 분석 모듈 확장

- 감정 분석 / 실적 발표 / 거시경제 / 내부자 거래

### 💼 방향 4 — 수익 모델

| 모델          | 가격                |
| ------------- | ------------------- |
| 무료 플랜     | 0원                 |
| 개인 프로     | 월 9,900원          |
| 개인 프리미엄 | 월 29,000원         |
| API 서비스    | 호출당 과금         |
| 기업 전용     | 월 500만~5,000만 원 |

### 🔥 방향 5 — 데이터 네트워크 효과

> **"1년만 운영하면, 후발주자는 따라잡기 매우 어려운 구조"**

성장 플라이휠: 사용자 행동 → 검증 사례 → 규칙 개선 → 정확도 ↑ → 만족도 ↑ → 재방문 ↑

---

---

# Part 4. 시스템 아키텍처

---

## Slide 13 — 기술 스택 한눈에

### Runtime

- **Python 3.13** (uv) / **FastAPI ≥ 0.115** / Uvicorn (port 33333)

### Data

- **PostgreSQL 16** (asyncpg + pgvector) / **SQLAlchemy 2.0 async** / Alembic
- **Redis 5.x** (asyncio)

### AI / LLM

- **OpenAI** (GPT-4o, gpt-5-mini, o1)
- **Anthropic** (Claude)
- **LangChain / LangGraph / LangSmith**

### Market & NLP

- **yfinance · pykrx · holidays**
- **kiwipiepy** (한국어 형태소)
- **youtube-transcript-api · BeautifulSoup4**

### Infrastructure

- **APScheduler 3.10** (7종 정기 작업)
- **python-jose + cryptography** (JWT)
- **Docker Compose** (app + postgres + redis)

### Frontend

- **Next.js 16** (App Router, Turbopack) / **React 19** / **TS 5.9**
- **Jotai 2** / **Tailwind CSS v4** / **lightweight-charts · recharts**

---

## Slide 14 — Hexagonal + DDD 아키텍처

### Clean Architecture 의존성 규칙

```
   ┌──────────────────────────────────────────────┐
   │  Frameworks & Drivers (FastAPI · DB · Redis)  │
   │  ┌────────────────────────────────────────┐  │
   │  │  Interface Adapters (Router · Repo)    │  │
   │  │  ┌──────────────────────────────────┐  │  │
   │  │  │  Use Cases (Application)         │  │  │
   │  │  │  ┌────────────────────────────┐  │  │  │
   │  │  │  │  Entities (Domain)         │  │  │  │
   │  │  │  └────────────────────────────┘  │  │  │
   │  │  └──────────────────────────────────┘  │  │
   │  └────────────────────────────────────────┘  │
   └──────────────────────────────────────────────┘
                의존성 방향: 바깥 → 안쪽
```

### 레이어별 MUST 규칙

| 레이어                 | 허용                   | 금지                                          |
| ---------------------- | ---------------------- | --------------------------------------------- |
| **Domain**             | 순수 Python            | FastAPI · SQLAlchemy · Redis · Pydantic · ORM |
| **Application**        | UseCase / Port         | FastAPI · ORM 직접 / Redis 직접               |
| **Adapter (Inbound)**  | Router · DTO 변환      | 비즈니스 로직                                 |
| **Adapter (Outbound)** | Repo · External Client | 도메인 규칙 침범                              |
| **Infrastructure**     | DB · ORM · Redis · env | —                                             |

---

## Slide 15 — 도메인 맵 (24개)

### 사용자·인증

`account` / `auth` / `kakao_auth` / `authentication`

### 시장 데이터

`stock` / `stock_theme` / `dashboard` / `smart_money` / `company_profile`

### 콘텐츠·분석

`news` / `disclosure` / `market_video` / `market_analysis`
`macro` / `history_agent` / `causality_agent` / `schedule`
`study` / `investment` / `sentiment`

### 통합 에이전트

`agent` (메인 오케스트레이터) / `api_schema`

### 커뮤니티

`board` / `post`

### 외부 연동 (11종)

- OpenAI · Anthropic (LLM)
- DART · SEC EDGAR · Finnhub (공시)
- yfinance · pykrx · FRED (시세·거시)
- SerpAPI · Naver · YouTube Data API (콘텐츠)
- LangSmith (관측)

---

## Slide 16 — 데이터 흐름

### 요청 처리 시퀀스

```
HTTP Request
   ▼
FastAPI Router (Inbound Adapter)
   ▼
Request DTO 파싱 (Pydantic)
   ▼
UseCase 실행 (Application)
   ▼
Port 호출
   ├─▶ Repository (Outbound) ─▶ SQLAlchemy ─▶ PostgreSQL
   ├─▶ External Client       ─▶ OpenAI / DART / yfinance / SEC
   └─▶ Cache Adapter         ─▶ Redis
   ▼
Domain Entity 조작 (순수 Python)
   ▼
Response DTO 변환
   ▼
HTTP Response (BaseResponse 표준)
```

### 백그라운드 작업 (APScheduler 7종)

| Job                          | 주기                   |
| ---------------------------- | ---------------------- |
| 공시 수집·처리·회사목록 갱신 | 분 단위 + bootstrap    |
| 뉴스 수집                    | 매일 06:00 KST         |
| 투자자 순매수 (KRX)          | 매 영업일 16:30 KST    |
| NASDAQ 지수 / 종목 일봉      | 일 1회                 |
| 거시 리스크 스냅샷           | 4h Redis TTL           |
| SEC 13F 글로벌 포트폴리오    | 분기 (2·5·8·11월 15일) |
| DART 국내 포트폴리오         | 매월 1일 03:00 KST     |

---

---

# Part 5. AI Multi-Agent 구성

---

## Slide 17 — 멀티 에이전트 오케스트레이션

### 메인 → 서브 에이전트 협업 구조

```
                ┌──────────────────────┐
   User Query ─▶│   agent (오케스트레이터)│
                └──────────┬───────────┘
                           │
   ┌───────────────────────┼───────────────────────┐
   ▼            ▼          ▼          ▼            ▼
┌──────┐   ┌────────┐  ┌──────┐  ┌─────────┐  ┌────────┐
│ News │   │Disclosure│ │Finance│ │Sentiment│  │ Macro  │
│ Agent│   │  Agent  │  │ Agent│  │  Agent  │  │ Agent  │
│ SERP │   │  DART   │  │yfinance│ │SNS+GPT │  │YouTube │
│+LLM  │   │+RAG+LLM │  │+pykrx │  │+Reddit │  │+LLM    │
└──┬───┘   └───┬────┘  └──┬───┘  └────┬────┘  └────┬───┘
   │           │          │           │            │
   └───────────┴────┬─────┴───────────┴────────────┘
                    ▼
        LangGraph 노드 → 통합 시그널 합성
                    ▼
              LangSmith Tracing
                    ▼
        Bullish / Neutral / Bearish + Confidence
```

### 핵심 설계

- **병렬 실행**: `asyncio.gather(return_exceptions=True)` — 부분 실패 허용
- **이중 캐시**: Postgres 1h (시그널) + Redis 7d (사업개요)
- **분산 락**: Redis `SET NX EX` — 동시 요청 멱등성
- **Source Tier 가중**: 출처 신뢰도가 confidence에 직접 반영

---

## Slide 18 — Source Tier 가중치 시스템

### 4단계 출처 신뢰도

| 등급           | 가중치 | 포함 도메인                                                    |
| -------------- | ------ | -------------------------------------------------------------- |
| **HIGH**       | × 1.0  | DART · SEC · 1군 IB 공식 리포트(미국) · IR 자료                |
| **MEDIUM**     | × 0.7  | Bloomberg · Reuters · WSJ · FT · 한경 · 매경 · 월가 애널리스트 |
| **MEDIUM_LOW** | × 0.5  | 국내 IB 공식 리포트 (buy-bias 보정)                            |
| **LOW**        | × 0.3  | SNS · 일반 뉴스 · 커뮤니티 (Naver · Reddit · DC)               |

### 섹터 오버라이드 — 도메인 특수성 반영

```python
_SECTOR_OVERRIDE: dict[Sector, tuple[set[str], SourceTier]] = {
    Sector.ENTERTAINMENT: (_SOCIAL_DOMAINS, SourceTier.MEDIUM),
}
```

→ **HYBE / SM / JYP / YG** 의 YouTube · X · Instagram 글:
LOW(0.3) → **MEDIUM(0.7)** 으로 자동 승격

### 종합 시그널 산출

```python
weighted_score += score * confidence * tier_multiplier
final_signal = "bullish"  if weighted_score > 0.2
              "bearish"  if weighted_score < -0.2
              "neutral"  otherwise
```

---

## Slide 19 — 캐시·동시성·복원력 (운영 안정성)

### 다층 캐시 — TTL은 도메인 진실성

| 캐시                          | TTL        | 근거                                          |
| ----------------------------- | ---------- | --------------------------------------------- |
| 매크로 스냅샷                 | **4시간**  | 거시 위험은 분 단위로 안 변함                 |
| 회사 프로필 (DART)            | **1일**    | 기업개황 거의 안 변함                         |
| 사업 개요 (LLM)               | **7일**    | 비즈니스 모델은 분기에도 안 변함 + LLM 비용 ↑ |
| 통합 분석                     | **1시간**  | 시그널은 뉴스 흐름에 따라 갱신                |
| `refresh_company_list` 쿨다운 | **24시간** | DART 회사 마스터 갱신 주기                    |

### Redis 분산 락 — `SET NX EX`

```python
lock_key = f"lock:disclosure:on_demand:{corp_code}"
acquired = await redis.set(lock_key, "1", nx=True, ex=60)
# atomic single-shot — race condition 0
# TTL 60초 — 프로세스 죽어도 자동 해제
# Redis 다운 시 True 반환 (가용성 우선)
```

### 부분 실패 허용

```python
results = await asyncio.gather(
    news.analyze(...), disclosure.analyze(...), finance.analyze(...),
    return_exceptions=True,
)
# 1개 죽어도 나머지로 시그널 산출
# result_status: SUCCESS / PARTIAL_SUCCESS / FAILURE
```

---

---

# Part 6. 팀 구성 및 작업 분배

---

## Slide 20 — 팀원 구성 및 작업 분배 (7인)

### Antelligen 팀

| 이름            | 담당 영역                             | 핵심 작업                                                                                                                               | 테크 역량                                         |
| --------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| 🧠 **김영진**   | 통합 에이전트 / 데이터 신뢰도         | 뉴스 8종목 제한 해제, US 확대(SerpAPI·yfinance·SEC), Source Tier 가중치, 조건부 startup, Redis 분산 락, 회사 프로필·사업개요 카드       | Python · DDD · Hexagonal · LangChain · Redis      |
| 📊 **김세진**   | Sentiment / 미국 주식 보강            | `sentiment` 도메인 신설(DDD), Reddit·네이버·토스 수집기, GPT-5-mini 감정분석, 자동 collect + Redis 캐시, FE `features/sentiment/` 4계층 | Python · DDD · BS4 · OpenAI · Next.js · Jotai     |
| 🌍 **문우성**   | 거시 경제 / 아키텍처                  | 데일리 거시 경제 현황판, 금리·유가·환율·경제일정 자동 수집, Risk-ON/OFF 판단(LLM), 시스템 아키텍처 정립                                 | 시스템 설계 · Hexagonal · LLM · YouTube API       |
| 🕰 **김민규**   | History / Causality / 성장 전략       | History Agent + Causality Agent(양방향 인과), 이상치 봉 자동 탐지 + LLM 원인 추론, `/dashboard` 2열 4:1, KPI/시장 진입 설계             | Python · LangGraph · Next.js · lightweight-charts |
| 👤 **이민영**   | 개인화 / Smart Money                  | 관심종목(뉴스·유튜브 개인화), 외국인/기관/개인 순매수 랭킹, 13F 글로벌 포트폴리오 19명, DART 국내 10명, Playwright + KRX                | Next.js · React · Playwright · Jotai · DDD        |
| 🤝 **이지은**   | 팀 의견 수렴                          | 외부 시점 피드백                                                                                                                        | —                                                 |
| 🤝 **정우진**   | 팀 의견 수렴                          | 외부 시점 피드백                                                                                                                        | —                                                 |

### 협업 방식

- **GitHub Fork & PR 워크플로우** — main 직접 푸시 금지, Merge commit 보존
- **레이어 규칙 강제** — `CLAUDE.md` 로 도메인 규약 공유
- **Slack 일일 진척 공유**

---

---

# Part 7. 실제 업무 진행

---

## Slide 21 — Github · OKR · Slack

### Github 커밋 컨벤션

```
upstream (EDDI-RobotAcademy)  →  origin (개인 fork)  →  PR  →  Merge commit
```

- **main 직접 푸시 금지** — 항상 PR / Merge commit (squash 금지 — 원본 SHA 보존)
- **Conventional Commits**: `feat / fix / refactor / docs / chore`
- 실제 PR — #93 sentiment 도메인 신설(+1,727/-14, 44 files), #106/#107 자동 collect + Redis 캐시

### OKR 관리

**Objective**: AI 멀티 에이전트 투자 인텔리전스 MVP 완성

| KR                                                    | 결과 |
| ----------------------------------------------------- | ---- |
| 메인 에이전트 통합 분석 (News · Disclosure · Finance) | ✅   |
| 한국 + 미국 시장 동일 UI/UX                           | ✅   |
| Source Tier 4단계 + 섹터 오버라이드                   | ✅   |
| Sentiment 에이전트 신설 + 메인 통합                   | ✅   |
| 거시 경제 현황판 + 시장 위험도                        | ✅   |
| 히스토리·인과관계 대시보드                            | ✅   |
| Watchlist + Smart Money                               | ✅   |

문서화: `CLAUDE.md` · `WOOSUNG_system-architecture.md` · 팀원별 작업 보고서 7종

### Slack 협업

- 채널: `#general` `#dev-backend` `#dev-frontend` `#design-architecture` `#bugs`
- 실제 사례 — "영진 sentiment 빈 결과 공유 → 김세진 자동 collect + 캐시 추가 커밋으로 즉시 해결"

---

---

# Part 8. 서비스 기능 소개

---

## Slide 22 — 주요 기능 한눈에

### 1️⃣ 종합 종목 분석 (`/agent/query`)

- 한 번의 요청 → 5개 에이전트 병렬 분석
- 결과: Bullish / Neutral / Bearish + Confidence
- 사업 개요 카드 + 출처 신뢰도 분포 시각화
- 한국·미국 동일 UI/UX

### 2️⃣ 히스토리·인과관계 대시보드 (`/dashboard`)

- 종목 일봉 + 이상치 봉(anomaly) 자동 탐지
- LLM 원인 추론 ("왜 이 날 떨어졌는가")
- 거시 이벤트 매칭 + 마커 6종

### 3️⃣ Smart Money — 자금 흐름 (`/smart-money`)

- 외국인 / 기관 / 개인 순매수 랭킹
- 집중 매수 종목 (3일 / 5일 / 10일)
- 해외(미국) — SEC 13F 기반 19명 글로벌 투자자
- 국내 — DART 대량보유 10명

### 4️⃣ 글로벌 포트폴리오 (`/smart-money/global-portfolio`)

- Warren Buffett · Michael Burry · Cathie Wood …
- 신규편입 / 비중확대 / 비중축소 / 청산 배지
- 국내 — 국민연금 · 미래에셋 · 박현주 등

---

## Slide 23 — 주요 기능 한눈에 (계속)

### 5️⃣ Sentiment 분석 — SNS 감정

- Reddit + 네이버 종목토론 + 토스 (stub)
- GPT-5-mini 감정 점수화 (positive / negative / neutral)
- 밈 티커 부스트 (TSLA · GME · NVDA × 1.35)
- 부정 비율 vs VIX 비교

### 6️⃣ 거시 경제 현황판 (`/macro`)

- 금리 / 유가 / 환율 / 경제 일정 자동 수집
- Risk-ON / Risk-OFF 자동 판단 + LLM 근거
- 4h Redis 캐시로 실시간성 + 비용 균형

### 7️⃣ 관심 종목 + 개인화 (`/settings/watchlist`)

- 테마별 종목 토글 등록
- 뉴스 페이지 — 등록 종목명으로 자동 필터
- 유튜브 페이지 — 종목명으로 YouTube 병렬 검색

### 8️⃣ 회사 프로필 (`/company-profile/{ticker}`)

- DART 회사 마스터 + SEC EDGAR (US)
- DART 사업보고서 RAG → LLM 사업 개요 (7일 캐시)
- ETF / INDEX 종목도 동일 카드 형식

### 9️⃣ 카카오 OAuth — temp_token / user_token 분리

- 가입 전 사용자도 핵심 기능 시연 가능 → 전환율 ↑

---

---

# Part 9. 라이브 시연

---

## Slide 24 — Live Demo

### 시연 시나리오

**① 종목 분석 — 한국 종목 (삼성전자 005930)**

- 5개 에이전트 병렬 분석
- 통합 시그널 + 사업개요 카드
- Source Tier 분포 확인

**② 종목 분석 — 미국 종목 (AAPL)**

- 영어 뉴스 + yfinance 분기 EPS + SEC 8-K filing
- 동일 UI/UX 로 동일하게 표시

**③ 엔터 섹터 — HYBE (352820)**

- YouTube · X · Instagram 출처가 MEDIUM 으로 승격
- 섹터 오버라이드가 시그널에 반영

**④ Smart Money 대시보드**

- 외국인 + 기관 집중 매수 종목 카드
- Warren Buffett 포트폴리오 변동 (신규편입 / 비중확대)

**⑤ 히스토리·인과관계 대시보드**

- NASDAQ 차트 + 이상치 마커
- 원인 가설 자동 생성 (LLM)

**⑥ 동시 요청 데모 — Redis 분산 락**

- 동일 종목 동시 5개 요청 → DART 1회만 호출

---

---

# Part 10. 프로젝트 소감 & 마무리

---

## Slide 25 — 학습한 사항 및 개인 소감

| 팀원            | 소감            |
| --------------- | --------------- |
| 🧠 **김영진**   | `[ 직접 작성 ]` |
| 📊 **김세진**   | `[ 직접 작성 ]` |
| 🌍 **문우성**   | `[ 직접 작성 ]` |
| 🕰 **김민규**   | `[ 직접 작성 ]` |
| 👤 **이민영**   | `[ 직접 작성 ]` |
| 🤝 **이지은**   | `[ 직접 작성 ]` |
| 🤝 **정우진**   | `[ 직접 작성 ]` |

---

## Slide 26 — 최종 마무리하며 하고 싶은 말

| 팀원            | 마무리 한마디   |
| --------------- | --------------- |
| 🧠 **김영진**   | `[ 직접 작성 ]` |
| 📊 **김세진**   | `[ 직접 작성 ]` |
| 🌍 **문우성**   | `[ 직접 작성 ]` |
| 🕰 **김민규**   | `[ 직접 작성 ]` |
| 👤 **이민영**   | `[ 직접 작성 ]` |
| 🤝 **이지은**   | `[ 직접 작성 ]` |
| 🤝 **정우진**   | `[ 직접 작성 ]` |

---

## Slide 27 — Thank You

### Antelligen

> **"투자 결과가 아니라,
> 검증 가능한 의사결정 과정과 안전한 실행 구조"**

### Q & A

- GitHub
  - antelligen-backend — `EDDI-RobotAcademy/antelligen-backend`
  - antelligen-frontend — `EDDI-RobotAcademy/antelligen-frontend`

### 감사합니다 🙇

---
