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

## Slide 2 — 서비스 개발 동기 및 목적

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

### Antelligen의 5가지 목표

1. **구조적 AI 시스템 구축** — 데이터 수집·분석·의사결정 에이전트 협업
2. **확장 가능한 아키텍처** — 새 기능 추가 시 기존 시스템 영향 최소화
3. **현실적 협업 흐름 반영** — 사람의 업무 방식 그대로 AI 협업으로 구현
4. **사용자 맞춤형 분석** — 개인 성향·관심 종목 기반 개인화
5. **자동화·효율성 향상** — 반복 분석 자동화, 실시간 데이터 반영

> **"AI 간 협업을 통해 문제를 해결하는 새로운 서비스 구조"**

---

## Slide 3 — TAM · SAM · SOM (목표 시장 및 고객 요구 사항)

### Total Addressable Market (TAM)

**글로벌 AI 에이전트 시장**

- 2025년: 약 76억 달러
- 2033년: 약 **1,820억 달러 (≈ 240조 원)** — 연평균 성장률 약 50%

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

## Slide 4 — 고객의 핵심 Pain Points

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

## Slide 5 — 서비스 개발 및 문제점 해결 방안 (1/2)

### 데이터 신뢰도·커버리지 해결

| #   | 문제                   | 해결                                                        |
| --- | ---------------------- | ----------------------------------------------------------- |
| P-1 | 뉴스 8종목 제한        | `TickerKeywordResolver` Port — 전 KRX 2,500+ 종목           |
| P-2 | 미국 종목 미지원       | `MarketRegion` 추상 + SerpAPI / yfinance / SEC EDGAR        |
| P-3 | 잠정실적 누락          | `OpenDartPreliminaryEarningsProvider` — 어닝 갭 윈도우 포착 |
| P-4 | 출처 무관 단순 평균    | `SourceTier` (HIGH/MEDIUM/MEDIUM_LOW/LOW) 가중치            |
| P-5 | 엔터주 SNS 시그널 묻힘 | `_SECTOR_OVERRIDE` — 섹터별 소스 가중 보정                  |

> **"신호의 양을 늘리되, 신호의 품질을 메타데이터로 표현한다"**

---

## Slide 6 — 서비스 개발 및 문제점 해결 방안 (2/2)

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

## Slide 7 — 경쟁사 분석

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

> 시장에는 "AI 빌더"와 "트레이딩 도구"는 많지만,
> **"검증 가능한 의사결정 과정"** 을 제공하는 서비스는 적다

---

## Slide 8 — 서비스 차별화 방안

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

> **"투자 결과가 아니라, 검증 가능한 의사결정 과정과
> 안전한 실행 구조를 제공하는 서비스가 시장 승자가 된다"**

---

---

# Part 3. 성장 전략 (Scale Up)

---

## Slide 9 — 시장 진입 전략 및 사용자 확보

### 목표 고객

**1차 — 개인 투자자**

- "이 종목이 오늘 왜 떨어졌지?"를 검색하는 사용자
- 차트 + 사건 + 원인 분석을 한 화면에서

**2차 — 데이터 기반 판단을 원하는 사용자**

- 신입 애널리스트 / 투자 콘텐츠 크리에이터 / 학생 투자 동아리

**가격 차별화**

- 블룸버그 월 200만 원+ → **한국 공시 중심 + 합리적 가격**

### 진입 채널 및 사용자 확보

```
초기: 웹사이트  →  PWA(홈 화면 추가)  →  모바일 앱 출시
```

1. **SEO** — 종목별 "왜 떨어졌나" 페이지 자동 생성
2. **커뮤니티** — 디스코드 / 네이버 종목 카페 / 주식 갤러리
3. **인플루언서** — 투자 유튜버 협업 / 분석 데이터 콘텐츠

---

## Slide 10 — 목표 성과 (KPI)

### 사용량 (Engagement)

| 지표         | 초기    | 확장     |
| ------------ | ------- | -------- |
| MAU          | 30~50명 | 10,000명 |
| 7일 재방문율 | 30%     | 40%      |

### 품질 (Quality)

| 지표                  | 초기 | 확장 |
| --------------------- | ---- | ---- |
| 사용자 만족도 (5점)   | 4.0  | 4.5  |
| "자신 있는 분석" 비율 | 30%  | 45%  |

### 비용 효율 (Efficiency)

| 지표             | 초기  | 확장 |
| ---------------- | ----- | ---- |
| 응답 속도        | 8초   | 3초  |
| 종목당 분석 비용 | 200원 | 50원 |

### 사업성 (Business)

- **유료 전환율 3%**
- **월 매출 100만 원** (1차 마일스톤)
- 앱 스토어 출시 (iOS / Android)

---

## Slide 11 — 서비스 확장 방안

### 방향 1 — 시장·자산 확장

- **시장**: 일본(니케이) / 유럽 / 신흥국
- **자산**: 암호화폐 / 원자재 / 채권 / 리츠
- **대안 데이터**: 커뮤니티 / 위성 / 카드 소비

### 방향 2 — 기능 확장

- 포트폴리오 분석 / 실시간 알림 / 백테스트
- 일일 리포트 / 주간 인사이트 / 종목 비교

### 방향 3 — 수익 모델

| 모델          | 가격                |
| ------------- | ------------------- |
| 무료 플랜     | 0원                 |
| 개인 프로     | 월 9,900원          |
| 개인 프리미엄 | 월 29,000원         |
| API 서비스    | 호출당 과금         |
| 기업 전용     | 월 500만~5,000만 원 |

### 방향 4 — 데이터 네트워크 효과

> **"1년만 운영하면, 후발주자는 따라잡기 매우 어려운 구조"**

성장 플라이휠: 사용자 행동 → 검증 사례 → 규칙 개선 → 정확도 ↑ → 만족도 ↑ → 재방문 ↑

---

---

# Part 4. 시스템 아키텍처 소개

---

## Slide 12 — 기술 스택 한눈에

### Backend

- **Python 3.13** / **FastAPI ≥ 0.115** / Uvicorn (port 33333)
- **PostgreSQL 16** (asyncpg + pgvector) / **SQLAlchemy 2.0 async** / Alembic
- **Redis 5.x** (asyncio) / **APScheduler 3.10** (20+ 정기 작업)
- **Docker Compose** (app + postgres + redis)

### AI / LLM

- **OpenAI** (GPT-4o, gpt-5-mini, o1)
- **LangChain / LangGraph / LangSmith**

### Market & Data

- **yfinance · pykrx · FRED · Finnhub · GDELT**
- **DART · SEC EDGAR · SerpAPI · YouTube Data API**
- **kiwipiepy** (한국어 형태소) / **BeautifulSoup4**

### Frontend

- **Next.js 16** (App Router, Turbopack) / **React 19** / **TypeScript 5.9**
- **Jotai 2** / **Tailwind CSS v4** / **lightweight-charts · recharts**

---

## Slide 13 — Hexagonal + DDD 아키텍처

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

## Slide 14 — 도메인 맵 & 데이터 흐름

### 도메인 맵 (24개)

**사용자·인증**: `account` / `auth` / `kakao_auth` / `authentication`

**시장 데이터**: `stock` / `stock_theme` / `dashboard` / `smart_money` / `company_profile`

**콘텐츠·분석**: `news` / `disclosure` / `market_video` / `macro` / `history_agent` / `causality_agent` / `sentiment`

**통합 에이전트**: `agent` (메인 오케스트레이터)

### 요청 처리 흐름

```
HTTP Request
   ▼
FastAPI Router (Inbound Adapter)
   ▼
UseCase 실행 (Application)
   ▼
Port 호출
   ├─▶ Repository → SQLAlchemy → PostgreSQL
   ├─▶ External Client → OpenAI / DART / yfinance / SEC
   └─▶ Cache Adapter → Redis
   ▼
Domain Entity 조작 (순수 Python)
   ▼
Response DTO 변환 → HTTP Response
```

### 백그라운드 스케줄러 (주요)

| Job                       | 주기                   |
| ------------------------- | ---------------------- |
| 뉴스 수집                 | 매일 06:00 KST         |
| 투자자 순매수 (KRX)       | 매 영업일 16:30 KST    |
| SEC 13F 글로벌 포트폴리오 | 분기 (2·5·8·11월 15일) |
| DART 국내 포트폴리오      | 매월 1일 03:00 KST     |

---

---

# Part 5. AI Multi-Agent 구성 소개

---

## Slide 15 — 멀티 에이전트 오케스트레이션

### 메인 → 서브 에이전트 협업 구조

```
                ┌─────────────────────────┐
   User Query ─▶│   agent (오케스트레이터) │
                └────────────┬────────────┘
                             │ asyncio.gather (병렬)
   ┌──────────┬──────────────┼──────────────┬──────────┐
   ▼          ▼              ▼              ▼          ▼
┌──────┐ ┌─────────┐  ┌──────────┐  ┌──────────┐ ┌────────┐
│ News │ │Disclosure│  │ Finance  │  │Sentiment │ │ Macro  │
│Agent │ │  Agent  │  │  Agent   │  │  Agent   │ │ Agent  │
│SERP  │ │DART+RAG │  │yfinance  │  │SNS+GPT   │ │YouTube │
│+LLM  │ │+LLM     │  │+DART     │  │+Reddit   │ │+LLM    │
└──────┘ └─────────┘  └──────────┘  └──────────┘ └────────┘
                             │
                   SourceTier 가중치 적용
                             ▼
                 LangGraph → 통합 시그널 합성
                             ▼
                     LangSmith Tracing
                             ▼
             Bullish / Neutral / Bearish + Confidence
```

---

## Slide 16 — Source Tier 가중치 시스템

### 4단계 출처 신뢰도

| 등급           | 가중치 | 포함 도메인                                                    |
| -------------- | ------ | -------------------------------------------------------------- |
| **HIGH**       | × 1.0  | DART · SEC · 1군 IB 공식 리포트(미국) · 기업 IR                |
| **MEDIUM**     | × 0.7  | Bloomberg · Reuters · WSJ · FT · 한경 · 매경 · 월가 애널리스트 |
| **MEDIUM_LOW** | × 0.5  | 국내 IB 공식 리포트 (buy-bias 보정)                            |
| **LOW**        | × 0.3  | SNS · 일반 뉴스 · 커뮤니티 (Naver · Reddit)                    |

### 섹터 오버라이드

```python
_SECTOR_OVERRIDE = {
    Sector.ENTERTAINMENT: ({"youtube.com", "x.com", "instagram.com"}, SourceTier.MEDIUM)
}
# HYBE / SM / JYP / YG 분석 시 YouTube·X → LOW(0.3) → MEDIUM(0.7) 자동 승격
```

### 종합 시그널 산출

```
news      → confidence × 0.7 (MEDIUM)
disclosure → confidence × 1.0 (HIGH)
finance   → confidence × 1.0 (HIGH)
sentiment → confidence × 0.3 (LOW)
                  ↓
         weighted_score 합산
    > 0.2 → bullish / < -0.2 → bearish / else → neutral
```

---

## Slide 17 — 캐시·동시성·복원력

### 다층 캐시

| 캐시                          | TTL        | 근거                           |
| ----------------------------- | ---------- | ------------------------------ |
| 매크로 스냅샷                 | **4시간**  | 거시 위험은 분 단위로 안 변함  |
| 회사 프로필 (DART)            | **1일**    | 기업개황 거의 안 변함          |
| 사업 개요 (LLM)               | **7일**    | 비즈니스 모델 + LLM 비용 절약  |
| 통합 분석                     | **1시간**  | 시그널은 뉴스 흐름에 따라 갱신 |
| `refresh_company_list` 쿨다운 | **24시간** | DART 회사 마스터 갱신 주기     |

### Redis 분산 락

```python
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
```

---

---

# Part 6. 팀 구성

---

## Slide 18 — 팀원 구성 및 테크 역량

### Antelligen 팀 (5인)

| 이름       | 담당 영역                                     | 테크 역량                                         |
| ---------- | --------------------------------------------- | ------------------------------------------------- |
| **김영진** | 통합 에이전트 / 데이터 인프라 / 신뢰도 시스템 | Python · DDD · Hexagonal · LangChain · Redis      |
| **김세진** | Sentiment 에이전트 전체 / 미국 주식 뉴스 보강 | Python · DDD · BS4 · OpenAI · Next.js · Jotai     |
| **문우성** | 거시 경제 현황판 / 시스템 아키텍처 정립       | 시스템 설계 · Hexagonal · LLM · YouTube API       |
| **김민규** | History Agent / Causality Agent / Dashboard   | Python · LangGraph · Next.js · lightweight-charts |
| **이민영** | 개인화 시스템 / Smart Money 대시보드          | Next.js · React · Playwright · Jotai · DDD        |

### 팀원별 담당 영역 한눈에

```
┌─────────────────────────────────────────────────────────┐
│                  Antelligen 플랫폼                       │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  김영진 — 메인 에이전트 + 데이터 인프라            │   │
│  │  (뉴스·공시·재무 서브에이전트 통합 / US 확대 /     │   │
│  │   SourceTier 가중치 / 분산 락 / 사업개요 카드)     │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   김세진     │  │   문우성     │  │   김민규     │  │
│  │  감정분석    │  │  거시경제    │  │  히스토리·   │  │
│  │  에이전트    │  │  현황판      │  │  인과관계    │  │
│  │  (SNS·Reddit │  │  (금리·유가· │  │  에이전트 +  │  │
│  │   GPT 분석)  │  │   환율·      │  │  Dashboard   │  │
│  │              │  │   Risk판단)  │  │  UI          │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  이민영 — 개인화 시스템 + Smart Money 대시보드     │   │
│  │  (관심종목 watchlist → 뉴스·유튜브 개인화 /        │   │
│  │   KRX 순매수 수집 / SEC 13F 19명 / DART 10명)     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

---

## 김영진 — 데이터 인프라 확장 · 신뢰도 시스템 · 에이전트 통합

---

## Slide 19 — 김영진 (1/3): 전 KRX 종목 지원 + 미국 주식 확대

### Before vs After

| 항목                | Before          | After                                  |
| ------------------- | --------------- | -------------------------------------- |
| 뉴스 분석 가능 종목 | 하드코딩 8개    | **전 KRX 2,500+ 종목**                 |
| 미국 종목           | 미지원          | **전 미국 상장주 (AAPL, TSLA 등)**     |
| 재무 데이터         | DART 정기공시만 | DART + **yfinance(US)** + **잠정실적** |
| 공시 데이터         | DART만          | DART + **SEC EDGAR (8-K/10-K/10-Q)**   |

### TickerKeywordResolverPort — 종목 제한 해제

```
기존 문제:
  TICKER_TO_KEYWORDS = {"005930": ["삼성전자"], ...}  ← 8개 외 키워드 없음
  → 시그널 산출 불가, 레이어 위반(use case 내부 상수 직접 import)

해결:
  Port.resolve(ticker) → DB에서 stock_name 동적 조회 + alias 결합
  → "000270" (기아) → ["기아", "기아차", "KIA"] 자동 생성
  → 전 KRX 2,500+ 종목 정상 동작
```

### MarketRegion — KR/US 분기 기반 인프라

```python
class MarketRegion(Enum):
    KR_KOSPI / KR_KOSDAQ / KR_KONEX
    US_NYSE / US_NASDAQ / UNKNOWN

# ticker 형식으로 자동 추론
# 6자리 숫자 → KR / 1~5 알파벳 → US_NASDAQ
```

| 영역 | KR 경로                    | US 경로                   |
| ---- | -------------------------- | ------------------------- |
| 뉴스 | 네이버 뉴스                | SerpAPI (gl=us, hl=en)    |
| 재무 | DART 분기보고서 + 잠정실적 | yfinance 분기 EPS         |
| 공시 | DART                       | SEC EDGAR (8-K/10-K/10-Q) |

---

## Slide 20 — 김영진 (2/3): Source Tier 가중치 + 종합 시그널 반영

### 4단계 SourceTier

```python
class SourceTier(str, Enum):
    HIGH       = "HIGH"        # DART, SEC, 미국 IB 공식 리포트
    MEDIUM     = "MEDIUM"      # Bloomberg, Reuters, WSJ, 한경, 매경
    MEDIUM_LOW = "MEDIUM_LOW"  # 국내 IB 공식 리포트 (buy-bias 보정)
    LOW        = "LOW"         # SNS, 일반 뉴스, 커뮤니티

_DEFAULT_WEIGHTS = { HIGH: 1.0, MEDIUM: 0.7, MEDIUM_LOW: 0.5, LOW: 0.3 }
```

### 엔터테인먼트 섹터 — SNS 가중치 보정

```python
_SECTOR_OVERRIDE = {
    Sector.ENTERTAINMENT: ({"youtube.com", "x.com", "instagram.com"}, SourceTier.MEDIUM)
}
# HYBE(352820) / SM(041510) / JYP(035900) / YG(122870)
# YouTube·X·Instagram → LOW(0.3) → MEDIUM(0.7) 자동 승격
# → 엔터주 분석 시 팬덤 SNS 반응이 시그널에 제대로 반영됨
```

### 메인 에이전트 종합 시그널 산출

```python
for r in results:
    tier = r.source_tier or _AGENT_DEFAULT_TIER.get(r.agent_name)
    multiplier = default_multiplier(tier)
    confidence = r.confidence * multiplier      # 티어 보정 적용
    weighted_score += signal_score * confidence
    confidence_total += confidence

avg_score = weighted_score / confidence_total
# > 0.2 → bullish / < -0.2 → bearish / else → neutral
```

> 가중치 수치(HIGH/MEDIUM/MEDIUM_LOW/LOW)는 env로 노출 → 운영 중 튜닝 가능

---

## Slide 21 — 김영진 (3/3): On-demand 분산 락 + 조건부 Startup + 사업개요 카드

### On-demand 공시 수집 + Redis 분산 락

```
문제: 동일 종목 동시 5개 요청 → DART API 5중 호출 → quota 낭비

해결:
  요청 A → Redis SET NX EX 락 획득
            → DART 5개 유형 병렬 fetch (A/B/C/D/E)
            → DB upsert → 락 해제
  요청 B → 락 대기 (최대 30초) → DB에 결과 보이면 즉시 공유
  요청 C ┘

보장: TTL 60초 deadlock 방지 / Redis 장애 시 graceful degrade
```

### 조건부 Startup 잡

| 잡                     | 조건                                 | 절약 효과                              |
| ---------------------- | ------------------------------------ | -------------------------------------- |
| `refresh_company_list` | 24h 이내 성공 이력 있으면 **스킵**   | KRX 전종목 재호출 방지                 |
| `process_documents`    | 미처리 공시 1건이라도 있을 때만 실행 | 불필요한 LLM 처리 방지                 |
| `refresh_market_risk`  | Redis 4h 이내 스냅샷 있으면 **복원** | **YouTube quota + LLM 비용 최대 절약** |

### 사업개요 카드 — 메인 에이전트 답변 강화

```
asyncio.create_task → 병렬 fetch (latency 거의 0)
DART 사업보고서 RAG (최대 5청크 / 3,000자)
→ LLM 사업개요 요약 → Redis 7일 캐시
→ (1) LLM 합성 컨텍스트로 주입 → 답변 품질 향상
→ (2) 응답 페이로드에 카드 DTO로 부착
```

---

---

## 김세진 — Sentiment 에이전트 전체 구축

---

## Slide 22 — 김세진 (1/3): Sentiment 도메인 신설 (DDD 헥사고날)

### 담당 범위: 백엔드 21개 파일 신규 (+1,727줄) / 프론트엔드 5개 파일 신규 (+592줄)

### 신설 도메인 구조

```
app/domains/sentiment/
├── adapter/
│   ├── inbound/api/
│   │   └── sentiment_router.py
│   └── outbound/
│       ├── external/
│       │   ├── reddit_client.py          ← Reddit 무인증 수집
│       │   ├── naver_finance_discussion_client.py  ← HTML 스크래핑
│       │   ├── toss_community_client.py  ← stub (차기 이터레이션)
│       │   └── openai_sns_signal_adapter.py  ← GPT 감정분석
│       ├── persistence/sns_post_repository_impl.py
│       └── cache/sns_signal_cache.py    ← Redis TTL 10분
├── application/
│   ├── port/ (수집·분석·저장 Port 4개)
│   └── usecase/
│       ├── collect_sns_posts_usecase.py
│       └── analyze_sns_signal_usecase.py
└── domain/model/
    ├── sns_post.py        ← 도메인 엔티티
    └── sns_signal_result.py  ← 표준 응답 DTO
```

### SNS 수집기 3종

| 수집기              | 방식                         | 특이사항                                 |
| ------------------- | ---------------------------- | ---------------------------------------- |
| **Reddit**          | `.json` 무인증 엔드포인트    | 신규 계정 OAuth 락 우회                  |
| **네이버 종목토론** | BeautifulSoup4 HTML 스크래핑 | EUC-KR 디코딩 버그 직접 발견·수정        |
| **토스 커뮤니티**   | stub (인터페이스만 보존)     | SPA 봇 탐지 → Playwright 차기 이터레이션 |

---

## Slide 23 — 김세진 (2/3): GPT 감정분석 + 밈/섹터 가중치 + DB 설계

### GPT 감정분석 어댑터

```
입력: 게시물 제목/본문 리스트
  ↓
GPT-5-mini (팀 표준 모델)
  ↓
게시물별 감정 분류 (positive / negative / neutral)
  ↓
종합 시그널: bullish / bearish / neutral
+ confidence (0~1)
+ overall_negative_ratio (VIX 비교용)
```

### 밈 티커 · 섹터별 가중치

| 종목 유형                       | 가중치                | 이유                             |
| ------------------------------- | --------------------- | -------------------------------- |
| TSLA, GME, AMC, NVDA 등 밈 티커 | confidence × **1.35** | SNS 반응이 실제 가격에 직접 영향 |
| 엔터(JYP/SM/HYBE/YG)            | × **1.3**             | 아티스트 SNS가 핵심 알파 소스    |
| 게임주                          | × **1.2**             | 커뮤니티 여론과 출시 성과 연동   |
| 일반 종목                       | × 1.0                 | 기본값                           |

### DB 설계 — `sns_posts` 테이블 (Alembic 마이그레이션 직접 작성·적용)

```sql
CREATE TABLE sns_posts (
  id SERIAL PRIMARY KEY,
  external_id VARCHAR UNIQUE,
  platform VARCHAR NOT NULL,    -- reddit / naver_finance / toss_community
  ticker VARCHAR NOT NULL,
  title TEXT, body TEXT, author VARCHAR, url VARCHAR,
  posted_at TIMESTAMP, collected_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_sns_posts_ticker_platform ON sns_posts(ticker, platform);
CREATE INDEX idx_sns_posts_posted_at ON sns_posts(posted_at);
```

### 표준 응답 DTO — 메인 에이전트 자연 통합

```python
SnsSignalResult {
  ticker, signal, confidence, source_tier,
  overall_negative_ratio,   # VIX 비교용
  per_platform,             # 플랫폼별 결과
  evidence,                 # 근거 게시물 top
  reasoning, analyzed_at
}
# → 메인 에이전트가 confidence × source_tier_weight 로 자연스럽게 합산
```

---

## Slide 24 — 김세진 (3/3): 운영 이슈 직접 수정 + Redis 캐시 + 프론트엔드

### 자체 발견·수정한 버그 및 운영 이슈

**① 네이버 한글 깨짐 (EUC-KR 디코딩 버그)**

```python
# Before — DB에 한글이 깨져 저장됨 ("@@@ ��ш꼍遺�")
content = resp.content.decode("euc-kr", errors="replace")

# After — 정상 한글 저장
soup = BeautifulSoup(resp.content, "html.parser", from_encoding="euc-kr")
```

**② 뉴스 라우터 DI 버그 수정**

```python
# Before: AnalyzeNewsSignalUseCase(repository=repo)  ← keyword_resolver 누락
# After:  AnalyzeNewsSignalUseCase(repository=repo,
#             keyword_resolver=TickerKeywordResolver(...))
```

**③ Redis 캐시 + 자동 collect 트리거 (PR 머지 후 운영 이슈 즉시 해결)**

```
analyze 엔드포인트 흐름:
  1. Redis cache.get(ticker) → HIT이면 즉시 반환 (GPT 호출 X)
  2. DB에 게시물 5건 미만 → CollectSnsPostsUseCase 자동 호출
  3. GPT 분석 → 결과를 Redis TTL 600초 캐시에 저장
  ※ 캐시를 라우터 레벨에 배치 → UseCase 순수성 (DDD 원칙) 유지
```

### 프론트엔드 SnsSignalCard

```
4가지 상태: IDLE → LOADING → SUCCESS / ERROR

SUCCESS 시 시각화:
  ▸ 시그널 배지 (상승↑ / 하락↓ / 중립) + 색상 차별
  ▸ 신뢰도 게이지 바
  ▸ 긍정/중립/부정 누적 비율 바
  ▸ 플랫폼별 결과 (Reddit / 네이버 종목토론 한국어 라벨)
  ▸ 근거 게시물 top 3 (감정 색상 마킹)
  ▸ AI 한국어 요약
```

> 김영진의 StockAnalysisView 페이지에 자연스럽게 통합 — 다른 sub_agent 카드들과 동일 패널에 표시

---

---

## 문우성 — 거시 경제 현황판 + 시스템 아키텍처

---

## Slide 25 — 문우성 (1/3): 거시경제 현황판 데이터 수집 파이프라인

### 데이터 수집 구조

```
매일 자동 수집 → 저장 → 전일 대비 등락 계산
  ├── 금리 (기준금리, 국채 10년물)
  ├── 유가 (WTI, 브렌트)
  ├── 환율 (USD/KRW, DXY)
  └── 주요 경제 일정 (FOMC, CPI, 실업률 발표 등)
```

### 수집 소스 & 스케줄러

| 데이터        | 소스                | 주기        |
| ------------- | ------------------- | ----------- |
| 금리·거시지표 | FRED (12개 시리즈)  | 일 1회      |
| 유가 · 환율   | 연관자산 파이프라인 | 일 1회      |
| VIX           | CBOE / yfinance     | 일 1회      |
| 경제 일정     | 크롤링              | 주 1회 갱신 |

### Redis 스냅샷 관리

```python
# 4시간 이내 스냅샷이 Redis에 있으면 메모리 store로 복원
async def _try_restore_macro_snapshot(max_age_hours: int = 4) -> bool:
    raw = await redis_client.get(MACRO_SNAPSHOT_REDIS_KEY)
    if not raw: return False
    payload = json.loads(raw)
    if datetime.now() - updated_at > timedelta(hours=max_age_hours):
        return False
    get_market_risk_snapshot_store().set(response, updated_at=updated_at)
    return True
# → 서버 재시작·hot-reload 시 LLM 호출 0회 (YouTube quota 보호)
```

---

## Slide 26 — 문우성 (2/3): Risk-ON / Risk-OFF 자동 판단

### 시장 상태 판단 로직

```
핵심 변수 조합 분석
  ├── 금리 방향 (상승 vs 하락)
  ├── 달러 강도 (DXY 방향)
  ├── VIX 수준 (공포 지수)
  └── 유가 방향 (에너지 비용)
           ↓
  LLM 기반 종합 판단
           ↓
  Risk-ON / Risk-OFF 결정 + 근거 자동 생성
```

### Risk-ON / Risk-OFF 출력 예시

| 판단         | 의미                    | 근거 예시                                                       |
| ------------ | ----------------------- | --------------------------------------------------------------- |
| **Risk-ON**  | 위험자산 선호 심리 강화 | "금리 하락 + 달러 약세 → 성장주·신흥국 매수 환경 조성"          |
| **Risk-OFF** | 위험자산 회피 심리 강화 | "VIX 25 돌파 + 달러 강세 → 미 국채·금 선호, 위험자산 매도 압력" |

### 사용자 화면 구성

```
/macro 페이지
  ├── 금리 · 유가 · 환율 카드 (전일 대비 등락 색상)
  ├── 주요 경제 일정 캘린더
  └── Risk-ON / Risk-OFF 배지 + LLM 근거 텍스트
```

---

## Slide 27 — 문우성 (3/3): 메인 에이전트 연결 + 아키텍처 기여

### 거시경제 에이전트 → 메인 에이전트 통합

```
거시경제 에이전트 (문우성)
  └── MarketRiskJudgementResponse 생성
          ↓
  Redis 4h 캐시 저장
          ↓
  메인 에이전트 (김영진 통합) 호출 시
  └── 거시 스냅샷 로드 → 종합 시그널 산출 컨텍스트로 활용
          ↓
  거시 환경 불안정 → 전체 confidence 하향 반영
```

### 시스템 아키텍처 정립 기여

- 전체 DDD · 헥사고날 아키텍처 설계 참여
- 레이어별 의존성 규칙 문서화 (`WOOSUNG_system-architecture.md`)
- 도메인 간 인터페이스 표준화 방향 제시
- 외부 API 공통 Client 패턴 정립

### 기술 스택 (담당 영역)

- YouTube Data API (거시 뉴스·영상 수집)
- FRED API (금리·CPI·실업률 시리즈)
- OpenAI GPT (Risk 판단 LLM)
- APScheduler (거시 데이터 정기 수집 잡)
- Redis (스냅샷 4h 캐시 + 분산 락)

---

---

## 김민규 — History Agent · Causality Agent · Dashboard

---

## Slide 28 — 김민규 (1/3): History Agent — 8단계 타임라인 파이프라인

### 한 줄 요약

> 종목 코드 하나 → 8개 외부 소스에서 데이터 수집 → "시점이 명확한 사건"만 골라 타임라인 자동 생성

### 8단계 파이프라인

```
Step 0  ticker 정규화 + 자산 유형 자동 판별 (EQUITY / INDEX / ETF)
   ↓
Step 1  Redis 캐시 HIT → 즉시 반환 (~50ms)
   ↓ MISS
Step 2  4개 소스 비동기 병렬 수집 (asyncio.gather)
        ├── yfinance  OHLCV + 기업이벤트 (배당·분할)
        ├── DART + yfinance  실적·임원변동·자사주
        ├── SEC EDGAR + DART  공시 (8-K/DART 주요사항)
        └── Finnhub → GDELT → Naver  뉴스
   ↓
Step 3  Jaccard ≥ 0.8 공시 중복 제거
        (같은 사건이 DART + SEC + Yahoo 에서 동시 입수될 때)
   ↓
Step 4  DB에서 기존 enrichment 로드 → title/causality 즉시 주입
   ↓
Step 5  신규 이벤트 병렬 enrichment
        ├── SURGE/PLUNGE 상위 3건 → Causality Agent 호출
        ├── 가격 이벤트 제목 생성
        └── 공시 한글 요약
   ↓
Step 6  EventClassifier v2 + importance_score 산정 (0~1)
   ↓
Step 7  DB upsert (event_enrichments, detail_hash PK)
   ↓
Step 8  Redis setex 3600s TTL → 응답 반환
```

### 자산 유형별 파이프라인 분기

| 자산 유형  | 예시         | 파이프라인                                          |
| ---------- | ------------ | --------------------------------------------------- |
| **EQUITY** | AAPL, 005930 | 기업 이벤트 + 공시 + 뉴스 + 거시 컨텍스트           |
| **INDEX**  | ^GSPC, ^KS11 | 지수별 맞춤 매크로 이벤트 + 인과 규칙               |
| **ETF**    | SPY, QQQ     | 자산 클래스 매크로 + 상위 5개 보유 종목 이벤트 분해 |

---

## Slide 29 — 김민규 (2/3): 이상치 탐지 + 이벤트 분류

### 5중 이상치 탐지기

| 탐지기                 | 트리거 조건                         | 마커 색상             |
| ---------------------- | ----------------------------------- | --------------------- | ----------------------- | --------- |
| **z-score**            | `                                   | 수익률                | > K×σ + floor` (K=2.5)  | 노랑 ★    |
| **cumulative 5d**      | 5일 누적 수익률 `                   | ±10%                  | ` 진입                  | 오렌지 🔻 |
| **cumulative 20d**     | 20일 누적 수익률 `                  | ±15%                  | ` 진입                  | 진홍 📉   |
| **drawdown**           | 60봉 고점 대비 -10% 도달 → -3% 회복 | 보라 🔽 / 에메랄드 🔼 |
| **volatility cluster** | 5거래일 내 `                        | r                     | >5%` 변동 2건 이상 묶음 | 앰버 ⚡   |

> `settings.anomaly_robust_sigma_method`: `"stdev"` / `"stable"` / `"mad"` 선택 가능

### 이벤트 분류 체계

| Category         | 대표 Types                                | 탐지 방법                        |
| ---------------- | ----------------------------------------- | -------------------------------- |
| **CORPORATE**    | EARNINGS, DIVIDEND, STOCK_SPLIT, BUYBACK  | yfinance 코드 매칭 (규칙)        |
| **ANNOUNCEMENT** | MERGER_ACQUISITION, CONTRACT, MAJOR_EVENT | SEC Item 코드 + 본문 LLM 재분류  |
| **MACRO**        | INTEREST_RATE, CPI, VIX_SPIKE, OIL_SPIKE  | FRED 시리즈 + 연관자산 threshold |
| **NEWS**         | (단일 유형)                               | source 필드로 provider 구분      |

### MACRO TYPE_A vs TYPE_B

| 분류       | 정의                                   | reason 필드                              |
| ---------- | -------------------------------------- | ---------------------------------------- |
| **TYPE_A** | 원인 / 발표 자체 (FOMC, CPI 발표)      | 없음 (사실 자체가 사유)                  |
| **TYPE_B** | 결과 / 시장 반응 (VIX 급등, 환율 변동) | **추정 사유 + 신뢰도 (HIGH/MEDIUM/LOW)** |

---

## Slide 30 — 김민규 (3/3): Causality Agent + Dashboard UI + SSE

### Causality Agent — "왜 이 날 급등/급락했는가"

```
이상치 봉(Anomaly Bar) 탐지 → 차트에 마커 자동 표시
         ↓
사용자 마커 클릭 (lazy 호출 — LLM 비용 절약)
         ↓
LangGraph StateGraph 4노드
  Node 1: 날짜 주변 뉴스·공시·거시지표 병렬 수집
  Node 2: LLM Tool Use (8개 도구 자율 선택·호출)
  Node 3: 가설 3~6개 생성 + 신뢰도 평가 (HIGH/MEDIUM/LOW)
  Node 4: 환각 방지 후처리 + 출처 검증
         ↓
event_enrichments DB 영구 저장 (detail_hash PK)
→ 동일 봉 두 번째 요청부터 ~50ms 응답 (캐시 write-through)
```

### Dashboard UI — `/dashboard` 2열 4:1 그리드

```
┌──────────────────────────────┬──────────────────┐
│  NasdaqChart                 │  StockSearch     │
│  + 이상치 봉 마커 6종         │                  │
│    (SURGE/PLUNGE/VIX_SPIKE)  ├──────────────────┤
│  마커 클릭 → Causality 팝업  │  AssetProfile    │
├──────────────────────────────│  Panel           │
│  HistoryPanel                │                  │
│  (타임라인 카드 목록)         │                  │
│  카드 클릭 → 차트 봉 하이라이 │                  │
└──────────────────────────────┴──────────────────┘
상태: Jotai 2.19 (atomWithStorage — localStorage 영속)
```

### SSE 스트리밍 API

```
GET /api/v1/history-agent/timeline/stream

이벤트 타입:
  progress → 처리 중인 단계 실시간 표시
  done     → 완성된 타임라인 데이터 전송
  error    → 에러 메시지

효과: 4~8초 로딩 대신 진행 상황을 사용자가 실시간 확인
```

---

---

## 이민영 — 개인화 시스템 · Smart Money 대시보드

---

## Slide 31 — 이민영 (1/3): 관심종목 기반 개인화

### watchlist 관리 (`/settings/watchlist`)

```
UI: 테마 그룹별 종목 버튼 (반도체 / 자동차 / 바이오 / 엔터 / ...)
    버튼 클릭 → 토글 등록/해제 / 현재 선택 개수 실시간 표시

API: GET /me/watchlist  → 관심종목 전체 조회
     POST /me/watchlist → 종목 추가
     PUT /me/watchlist/{stock_code} → 종목 교체
     DELETE /me/watchlist/{stock_code} → 종목 삭제 (204)

인증: Redis 세션 기반 (쿠키 user_token 또는 Authorization: Bearer 모두 지원)
```

### 뉴스 · 유튜브 개인화 연동

| 페이지     | 관심종목 없을 때            | 관심종목 있을 때                                  |
| ---------- | --------------------------- | ------------------------------------------------- |
| `/news`    | 전체 최신 뉴스 100건        | 등록 종목명으로 DB 뉴스 필터링 (종목당 최대 10건) |
| `/youtube` | 일반 주식 키워드 5개로 검색 | 종목명 최대 5개를 YouTube 병렬 검색 키워드로 사용 |

### 뉴스 개인화 상세 흐름

```
사용자 세션 → 관심종목 목록 조회
  ↓
종목별 stock_name으로 뉴스 DB 제목 검색
  ↓
URL 기준 중복 제거
  ↓
최신순 정렬 후 반환
```

---

## Slide 32 — 이민영 (2/3): 국내 Smart Money (KRX 자동 수집)

### 스마트머니란?

> 개인보다 정보력·자본력이 높은 **외국인·기관·저명 투자자**의 거래 흐름을 추적해
> 어디에 "큰 돈"이 들어오고 있는지 파악하는 투자 분석

### KRX 자동 수집 스케줄러

```
매 영업일 16:30 KST (장 마감 30분 후)
  ↓
KRX → KOSPI + KOSDAQ 전 종목
  ↓
외국인 / 기관합계 / 개인 → 종목별 순매수거래량 + 순매수거래대금
  ↓
DB 저장
```

### 집중 매수 종목 — 집중도 점수 계산

```
외국인 점수 = 내 순매수 ÷ 전체 최대값 (0~1 정규화)
기관 점수   = 내 순매수 ÷ 전체 최대값 (0~1 정규화)
집중도 점수 = (외국인 점수 + 기관 점수) ÷ 2 × 100

→ 외국인·기관이 "동시에" 매수한 종목만 교집합 추출
```

### UI 구성

```
① 스마트머니 집중 매수 종목 카드 (기간: 3일 / 5일 / 10일 선택)
   - 종목명 + 외국인 순매수 금액 + 기관 순매수 금액 + 집중도 게이지 바

② 투자자별 순매수 랭킹 탭 (외국인 / 기관 / 개인)
   - 행 클릭 → 최근 30일 투자자별 추이 차트 펼침
   - 외국인(파랑) / 기관(초록) / 개인(노랑) 3개 라인
   - Redis TTL 10분 캐싱 적용
```

---

## Slide 33 — 이민영 (3/3): 글로벌·국내 저명 투자자 포트폴리오

### 글로벌 포트폴리오 — SEC 13F (19명)

**수집 대상 투자자**

| 분류             | 투자자                                                                          |
| ---------------- | ------------------------------------------------------------------------------- |
| 전설적 투자자    | Warren Buffett, Michael Burry, George Soros, Carl Icahn, Seth Klarman           |
| 헤지펀드 매니저  | Bill Ackman, David Tepper, Ray Dalio, Stan Druckenmiller, Dan Loeb, Steve Cohen |
| 퀀트·대형 운용사 | Ken Griffin, Renaissance Technologies, Two Sigma, D.E. Shaw                     |
| 성장주 중심      | Cathie Wood, Tiger Global                                                       |

**수집 파이프라인**

```
분기별 (2·5·8·11월 15일 09:00 KST)
  ↓
SEC EDGAR 최신 13F-HR 공시 → XML 파싱
  ↓
OpenFIGI API로 CUSIP → 티커 변환
  ↓
직전 분기와 비교 → 신규편입/비중확대/비중축소/청산 배지 자동 생성
  ↓
포트폴리오 비중(%) 계산 → DB 저장
```

### 국내 포트폴리오 — DART 대량보유보고 (10명)

**수집 대상**: 국민연금, 미래에셋, 삼성, KB, 신한, NH-아문디, 박현주, 강방천, 이채원

```
매월 1일 03:00 KST
  ↓
DART corp_code XML → 상장주 상위 800종목 추출
  ↓
동시 10개 병렬 API 요청
  ↓
5% 이상 대량보유 종목 중 수집 대상 투자자 매칭
  ↓
기존 보유와 비교 → 변동 유형 계산 → DB upsert
```

### UI — 변동 배지

| 배지         | 의미                      |
| ------------ | ------------------------- |
| **신규편입** | 이번 분기 처음 매수       |
| **비중확대** | 전 분기 대비 주식 수 증가 |
| **비중축소** | 전 분기 대비 주식 수 감소 |
| **청산**     | 이번 분기에서 제거된 종목 |

---

---

# Part 7. 실제 업무를 어떻게 했는가

---

## Slide 34 — GitHub · OKR · Slack

### GitHub 커밋 컨벤션 & PR 워크플로우

```
upstream (EDDI-RobotAcademy)  →  origin (개인 fork)  →  PR  →  Merge commit
```

- **main 직접 푸시 금지** — 항상 PR 워크플로우
- **Merge commit** (squash 금지 — 원본 커밋 SHA 보존)
- **Conventional Commits**: `feat / fix / refactor / docs / chore`
- 머지 후 fork sync: `git fetch upstream && git merge --ff-only upstream/main`

**실제 PR 사례**

| PR            | 내용                                  | 규모                 |
| ------------- | ------------------------------------- | -------------------- |
| #93 (김세진)  | sentiment 도메인 신설                 | +1,727/-14, 44 files |
| #106 (김세진) | 자동 collect + Redis 캐시             | +592 lines           |
| (김영진)      | US 확대 + Source Tier + On-demand 락  | 40+ files            |
| (김민규)      | History + Causality Agent + Dashboard | 대규모               |
| (이민영)      | watchlist + KRX + 글로벌 포트폴리오   | 대규모               |

### OKR 달성 현황

| Key Result                                            | 결과 |
| ----------------------------------------------------- | ---- |
| 메인 에이전트 통합 분석 (News · Disclosure · Finance) | ✅   |
| 한국 + 미국 시장 동일 UI/UX                           | ✅   |
| Source Tier 4단계 + 섹터 오버라이드                   | ✅   |
| Sentiment 에이전트 신설 + 메인 통합                   | ✅   |
| 거시 경제 현황판 + 시장 위험도                        | ✅   |
| 히스토리·인과관계 대시보드                            | ✅   |
| Watchlist + Smart Money                               | ✅   |

### Slack 협업

- 채널: `#general` `#dev-backend` `#dev-frontend` `#design-architecture` `#bugs`
- **실제 사례** — "영진 sentiment 빈 결과 공유 → 김세진 자동 collect + 캐시 추가 커밋으로 즉시 해결"

---

---

# Part 8. 서비스 전반적인 소개 (기능)

---

## Slide 35 — 주요 기능 한눈에 (1/2)

### 1. 종합 종목 분석 (`/agent/query`)

- 한 번의 요청 → 5개 에이전트 병렬 분석
- 결과: Bullish / Neutral / Bearish + Confidence
- 사업 개요 카드 + 출처 신뢰도 분포 시각화
- 한국·미국 동일 UI/UX

### 2. 히스토리·인과관계 대시보드 (`/dashboard`)

- 종목 일봉 + 이상치 봉(anomaly) 자동 탐지 (5중 탐지기)
- LLM 원인 추론 ("왜 이 날 떨어졌는가") + 가설 신뢰도 (HIGH/MEDIUM/LOW)
- 거시 이벤트 매칭 + 마커 6종

### 3. Sentiment 분석 (`/sentiment`)

- Reddit + 네이버 종목토론 SNS 감정 점수화
- GPT-5-mini 감정 분류 (positive / negative / neutral)
- 밈 티커 부스트 (TSLA · GME · NVDA × 1.35)
- 부정 비율 vs VIX 비교

### 4. 거시 경제 현황판 (`/macro`)

- 금리 / 유가 / 환율 / 경제 일정 자동 수집
- Risk-ON / Risk-OFF 자동 판단 + LLM 근거
- 4h Redis 캐시로 실시간성 + 비용 균형

---

## Slide 36 — 주요 기능 한눈에 (2/2)

### 5. Smart Money — 국내 자금 흐름 (`/smart-money`)

- 외국인 / 기관 / 개인 순매수 랭킹 (당일)
- 집중 매수 종목 (3일 / 5일 / 10일 기간 선택)
- 종목 클릭 → 최근 30일 투자자별 추이 차트

### 6. 글로벌 포트폴리오 (`/smart-money/global-portfolio`)

- Warren Buffett · Michael Burry · Cathie Wood 등 19명 (SEC 13F)
- 신규편입 / 비중확대 / 비중축소 / 청산 배지
- 국내 — 국민연금 · 미래에셋 · 박현주 등 10명 (DART)

### 7. 관심 종목 + 개인화 (`/settings/watchlist`)

- 테마별 종목 토글 등록
- 뉴스 페이지 — 등록 종목명으로 자동 필터링
- 유튜브 페이지 — 종목명으로 YouTube 병렬 검색

### 8. 회사 프로필 (`/company-profile/{ticker}`)

- DART 회사 마스터 + SEC EDGAR (US)
- DART 사업보고서 RAG → LLM 사업 개요 (7일 캐시)
- ETF / INDEX 종목도 동일 카드 형식 제공

### 9. 카카오 OAuth 인증

- temp_token / user_token 분리 → 가입 전 사용자도 핵심 기능 시연 가능

---

---

# Part 9. 라이브 시연

---

## Slide 37 — Live Demo

### 시연 시나리오

**① 종목 분석 — 한국 종목 (삼성전자 005930)**

- 5개 에이전트 병렬 분석
- 통합 시그널 + 사업개요 카드
- Source Tier 분포 확인

**② 종목 분석 — 미국 종목 (AAPL)**

- 영어 뉴스 + yfinance 분기 EPS + SEC 8-K filing
- 동일 UI/UX로 동일하게 표시

**③ 엔터 섹터 — HYBE (352820)**

- YouTube · X · Instagram 출처가 MEDIUM으로 승격
- 섹터 오버라이드가 시그널에 반영

**④ Smart Money 대시보드**

- 외국인 + 기관 집중 매수 종목 카드
- Warren Buffett 포트폴리오 변동 (신규편입 / 비중확대)

**⑤ 히스토리·인과관계 대시보드**

- NASDAQ 차트 + 이상치 마커
- 마커 클릭 → 원인 가설 자동 생성 (LLM)

**⑥ Redis 분산 락 데모**

- 동일 종목 동시 5개 요청 → DART 1회만 호출

---

---

# Part 10. 3·4차 프로젝트 소감

---

## Slide 38 — 학습한 사항 및 개인 소감

| 팀원       | 소감            |
| ---------- | --------------- |
| **김영진** | `[ 직접 작성 ]` |
| **김세진** | `[ 직접 작성 ]` |
| **문우성** | `[ 직접 작성 ]` |
| **김민규** | `[ 직접 작성 ]` |
| **이민영** | `[ 직접 작성 ]` |
| **이지은** | `[ 직접 작성 ]` |
| **정우진** | `[ 직접 작성 ]` |

---

---

# Part 11. 최종 마무리

---

## Slide 39 — 마무리하며 하고 싶은 말

| 팀원       | 마무리 한마디   |
| ---------- | --------------- |
| **김영진** | `[ 직접 작성 ]` |
| **김세진** | `[ 직접 작성 ]` |
| **문우성** | `[ 직접 작성 ]` |
| **김민규** | `[ 직접 작성 ]` |
| **이민영** | `[ 직접 작성 ]` |
| **이지은** | `[ 직접 작성 ]` |
| **정우진** | `[ 직접 작성 ]` |

---

## Slide 40 — Thank You

### Antelligen

> **"투자 결과가 아니라,
> 검증 가능한 의사결정 과정과 안전한 실행 구조"**

### Q & A

- GitHub
  - antelligen-backend — `EDDI-RobotAcademy/antelligen-backend`
  - antelligen-frontend — `EDDI-RobotAcademy/antelligen-frontend`

### 감사합니다

---
