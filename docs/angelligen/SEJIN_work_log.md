# Antelligen 프로젝트 — 김세진 작업 내역

> 3차/4차 프로젝트 (2026.04 — 2026.04.29) 단독 작업 기록
> 백엔드 PR #93 + 프론트엔드 PR + 추가 보강 커밋

---

## 1. 작업 개요

### 담당 도메인
- **백엔드**: `app/domains/sentiment/` 신설 (DDD 헥사고날 구조)
- **백엔드**: `app/domains/news/` 미국 주식 확장 (영진님 인프라 위에 보강)
- **프론트엔드**: `features/sentiment/` 신설 + 종목 분석 페이지 통합

### 결과물
- 백엔드 PR #93 (https://github.com/EDDI-RobotAcademy/antelligen-backend/pull/93)
  - 9 commits, +1,727 / -14, 44 files changed
  - 추가 보강 커밋 2개 (한글 디코딩 fix + 자동 collect 캐시)
- 프론트엔드 PR (https://github.com/EDDI-RobotAcademy/antelligen-frontend)
  - 6 files changed, +592 / -5
- 임시 테스트 라우트 (PR 미포함, 로컬 검증용)

### GitHub 브랜치 전략
```
upstream (EDDI-RobotAcademy)  ← 학원 본 리포
   │
   ├── origin (Jojin-gorilla)  ← 본인 포크, PR 베이스
   │
   └── personal (Jojin-gorilla/antelligen-backup) ← 작업 백업용
```

---

## 2. 백엔드 작업 — Sentiment 도메인 신설 (회의록 4번)

### 2.1 신설 도메인 구조 (DDD 헥사고날)

```
app/domains/sentiment/
├── adapter/
│   ├── inbound/
│   │   ├── api/
│   │   │   └── sentiment_router.py          # FastAPI 라우터
│   │   └── dto/
│   │       └── sentiment_dto.py             # Request/Response DTO
│   └── outbound/
│       ├── external/
│       │   ├── reddit_client.py             # Reddit .json 무인증
│       │   ├── naver_finance_discussion_client.py  # 네이버 종목토론 HTML 스크래핑
│       │   ├── toss_community_client.py     # 토스 (stub)
│       │   └── openai_sns_signal_adapter.py # GPT 감정분석
│       ├── persistence/
│       │   ├── sns_post_repository_impl.py
│       │   └── sns_post_orm.py              # SQLAlchemy ORM
│       └── cache/
│           └── sns_signal_cache.py          # Redis 결과 캐시 (추가 커밋)
├── application/
│   ├── port/
│   │   ├── sns_collector_port.py
│   │   ├── sns_signal_analysis_port.py
│   │   ├── sns_post_repository_port.py
│   │   └── ticker_keyword_resolver_port.py
│   └── usecase/
│       ├── collect_sns_posts_usecase.py     # 게시물 수집
│       └── analyze_sns_signal_usecase.py    # 감정분석
└── domain/
    └── model/
        ├── sns_post.py                       # 도메인 엔티티
        ├── sns_signal_result.py              # 응답 DTO
        ├── platform_signal.py
        └── sns_evidence.py
```

**총 19개 파일** (이후 캐시 추가로 21개)

### 2.2 데이터 수집기 3종

#### Reddit 수집기 (`reddit_client.py`)
- **방식**: `https://www.reddit.com/r/{subreddit}/search.json` 무인증 호출
- **이유**: Reddit OAuth 신규 계정 락 우회 (정식 API 권한 미발급 환경 대응)
- **대상 서브레딧**: `wallstreetbets`, `stocks`, `investing`, `Korean_Stocks` 등
- **기술**: httpx 비동기, User-Agent 헤더 박음

#### 네이버 종목토론 수집기 (`naver_finance_discussion_client.py`)
- **방식**: `https://finance.naver.com/item/board.naver?code={ticker}` HTML 정적 스크래핑
- **기술**: BeautifulSoup4 (lxml 의존성 회피, html.parser 사용)
- **인코딩 처리**: EUC-KR → UTF-8 변환 (자세한 내용은 4.2 디버깅 항목)

#### 토스 커뮤니티 수집기 (`toss_community_client.py`)
- **방식**: stub 상태
- **이유**: 토스 SPA 구조 + 봇 탐지로 정적 스크래핑 불가
- **결정**: 인터페이스만 보존, Playwright 도입은 다음 이터레이션

### 2.3 GPT 감정분석 어댑터 (`openai_sns_signal_adapter.py`)

- **모델**: gpt-5-mini (팀 표준)
- **입력**: 게시물 제목/본문 리스트
- **출력**: 게시물별 감정(positive/negative/neutral) + 점수
- **종합 시그널**:
  - `bullish` / `bearish` / `neutral`
  - `confidence` (0~1)
  - `overall_negative_ratio` (VIX 비교용)

#### 밈 티커 가중치
- `TSLA, GME, AMC, PLTR, NVDA, SMCI` 등은 SNS 영향력 큰 종목
- `confidence × 1.35` 부스트

#### 섹터 가중치 (선택적)
- 엔터(JYP/SM/HYBE/YG): ×1.3
- 게임주: ×1.2
- 일반 종목: ×1.0

### 2.4 표준 응답 DTO (`SnsSignalResult`)

다른 sub_agent들과 동일한 형태로 구조화 — 메인 통합 에이전트가 `confidence × source_tier_weight`로 자연스럽게 합산 가능.

```python
{
  "ticker": "005930",
  "signal": "bearish",
  "confidence": 0.40,
  "source_tier": "하",
  "sector_weight_applied": False,
  "overall_negative_ratio": 0.60,
  "total_sample_size": 5,
  "per_platform": [
    {"platform": "naver_finance", "signal": "bearish", "sample_size": 5, ...}
  ],
  "evidence": [...],   # 근거 게시물 top
  "reasoning": "약한 하방 신호가 우세합니다",
  "analyzed_at": "2026-04-28T16:56:05",
  "elapsed_ms": 1850
}
```

### 2.5 데이터베이스 (Alembic 마이그레이션)

**신설 테이블: `sns_posts`**

```sql
CREATE TABLE sns_posts (
  id SERIAL PRIMARY KEY,
  external_id VARCHAR UNIQUE,
  platform VARCHAR NOT NULL,    -- reddit / naver_finance / toss_community
  ticker VARCHAR NOT NULL,
  title TEXT,
  body TEXT,
  author VARCHAR,
  url VARCHAR,
  posted_at TIMESTAMP,
  collected_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sns_posts_ticker_platform ON sns_posts(ticker, platform);
CREATE INDEX idx_sns_posts_posted_at ON sns_posts(posted_at);
```

Alembic 마이그레이션 스크립트 작성 + 적용.

### 2.6 라우터 + Pydantic Body 컨벤션

기존 일부 라우터가 Query 파라미터 사용 중이었음 → 팀 표준이 Pydantic Body라 Query → Body로 리팩토링.

```python
# Before
@router.post("/analyze")
async def analyze(ticker: str = Query(...), lookback_limit: int = Query(100)):

# After  
class AnalyzeSnsSignalRequest(BaseModel):
    ticker: str
    lookback_limit: int = 100

@router.post("/analyze")
async def analyze(request: AnalyzeSnsSignalRequest):
```

---

## 3. 백엔드 작업 — News 도메인 미장 확장 (회의록 1번)

### 3.1 화이트리스트 확장

`_SYNONYM_OVERRIDES` 딕셔너리 5개 → **34개**

추가 종목:
- **미국 NASDAQ 14개**: AAPL, MSFT, GOOGL, GOOG, AMZN, NVDA, TSLA, META, AMD, INTC, AVGO, NFLX, ADBE, COST
- **미국 NYSE 2개**: BRK-B, JPM
- **국장 동의어 18개**: HYBE(하이브), SM엔터(에스엠), JYP(JYP엔터), EcoPro(에코프로) 등

### 3.2 라우터 DI 버그 수정

`news_router.py`의 `AnalyzeNewsSignalUseCase` 의존성 주입 시 `keyword_resolver` 누락 발견.

```python
# Before
usecase = AnalyzeNewsSignalUseCase(repository=repo)  # keyword_resolver 누락

# After
usecase = AnalyzeNewsSignalUseCase(
    repository=repo,
    keyword_resolver=TickerKeywordResolver(StockRepositoryImpl()),
)
```

### 3.3 stocks.csv 미국 종목 추가

기존 한국 30종목 → **46종목** (한국 30 + 미국 16).

---

## 4. 백엔드 디버깅 + 트러블슈팅

### 4.1 백엔드 startup hang

**증상**: `await job_collect_news()`가 50개 키워드 × 페이지당 100건 × 10페이지를 동기적으로 순회 → 백엔드 startup이 1~2분 또는 무한 대기

**대응**: 통합 테스트 시 main.py lifespan 임시 주석 → 검증 완료 후 `git checkout main.py`로 원상복구

### 4.2 네이버 종목토론 한글 깨짐 (EUC-KR 디코딩)

**증상**: DB의 `sns_posts.title`에 한글이 깨져 저장됨 (예: `@@@ ��ш꼍遺� ��κ�����`)

**원인**: 기존 코드가 `errors='replace'`로 EUC-KR 디코딩 → 파싱 불가 바이트를 `U+FFFD`(?)로 치환

```python
# Before — 깨짐 발생
content = resp.content.decode("euc-kr", errors="replace")
soup = BeautifulSoup(content, "html.parser")

# After — 정상
soup = BeautifulSoup(resp.content, "html.parser", from_encoding="euc-kr")
```

**검증**: 코드포인트 직접 확인
```
0xb9e4 = 매
0xb3c4 = 도
0xc0ac = 사
0xc774 = 이
0xb4dc = 드
0xce74 = 카
→ "매도사이드카" 정상 한글 ✓
```

PowerShell 콘솔이 cp949로 깨서 보여주는 게 별도 문제고, **DB는 UTF-8 정상 저장**이었음 확인.

### 4.3 Reddit 신규 계정 OAuth 락

**증상**: 정식 OAuth로 접근 시 `Forbidden` 에러

**대응**: `.json` 엔드포인트는 인증 없이 접근 가능 → URL에 `.json` 붙여서 우회

```
https://www.reddit.com/r/wallstreetbets/search.json?q=TSLA&limit=10
```

### 4.4 Docker postgres 포트 충돌

기본 포트 5432가 호스트 다른 프로세스와 충돌 → 5433 매핑으로 우회 (docker-compose.yml + 환경변수 조정).

### 4.5 Alembic 환경 정비

- `alembic.ini` ASCII 인코딩으로 통일 (Windows cp949 콘솔 호환)
- `env.py`에서 sync/async 엔진 분리 (alembic은 sync, FastAPI는 async)

---

## 5. 백엔드 추가 보강 — 자동 collect + Redis 캐시

### 5.1 발견된 운영 이슈

PR 머지 직후 영진님이 본인 환경에서 분석 시도:
- 결과: "분석할 SNS 게시물 없음"
- 원인: `analyze` 엔드포인트가 DB만 조회하는 구조 → 빈 DB 환경에서는 결과 0건

영진님 추가 의견: "캐시 없이 매번 GPT 호출하면 비용 부담"

### 5.2 해결 방안 (추가 커밋)

**1) `SnsSignalResultCache` 신설** (`adapter/outbound/cache/sns_signal_cache.py`)
- Redis 기반 ticker별 분석 결과 캐시
- TTL 600초 (10분)
- `RedisError` + `JSONDecodeError` 방어

**2) `AnalyzeSnsSignalUseCase` 자동 collect 트리거**
- `count_by_ticker(ticker)` 5건 미만 시 → `CollectSnsPostsUseCase.execute()` 호출
- 자동 수집 실패해도 분석 계속 진행 (graceful degradation)

**3) `sentiment_router.py` 캐시 통합**
```
analyze 엔드포인트 흐름:
  1. cache.get(ticker) → hit이면 즉시 반환 (GPT 호출 X)
  2. miss → collectors 조립 + UseCase 호출
  3. 결과를 cache.set(ticker, dict, ex=600)
  4. 응답 반환
```

### 5.3 아키텍처 결정

**캐시는 라우터 레벨에 배치** (UseCase는 인프라 의존성 모름)

이유:
- DDD/헥사고날 원칙 준수 (UseCase 순수성)
- 도메인 DTO에 `from_dict()` 메서드 추가 불필요
- 라우터 흐름이 자연스러움

---

## 6. 프론트엔드 작업

### 6.1 신설 도메인 구조 (DDD)

```
features/sentiment/
├── domain/
│   └── model/
│       └── snsSignal.ts                      # 16개 필드 타입
├── infrastructure/
│   └── api/
│       └── sentimentApi.ts                   # API 호출 + 매퍼
├── application/
│   ├── atoms/
│   │   └── snsSignalAtom.ts                  # Jotai discriminated union state
│   └── hooks/
│       └── useSnsSignal.ts                   # 커스텀 훅
└── ui/
    └── components/
        └── SnsSignalCard.tsx                 # 4상태 렌더링
```

### 6.2 타입 시스템

```typescript
// snsSignal.ts
type SnsSignal = "bullish" | "bearish" | "neutral";
type SnsSentimentLabel = "positive" | "negative" | "neutral";
type SnsSourceTier = "상" | "중" | "중하" | "하";

interface SnsSignalResult {
  ticker: string;
  signal: SnsSignal;
  confidence: number;
  sourceTier: SnsSourceTier;
  // ... 16개 필드
}
```

### 6.3 API 어댑터 — snake_case ↔ camelCase 매핑

영진님이 만든 `stockAnalysisApi` 패턴 그대로 따름:

```typescript
// Raw 인터페이스 (백엔드 응답 그대로)
interface RawSnsSignalResult {
  ticker: string;
  signal: string;
  source_tier: string;
  // ...
}

// 매퍼 함수
function mapRawToSnsSignalResult(raw: RawSnsSignalResult): SnsSignalResult {
  return {
    ticker: raw.ticker,
    signal: raw.signal,
    sourceTier: raw.source_tier,  // snake → camel
    // ...
  };
}

// httpClient<ApiResponse<RawSnsSignalResult>> 패턴
```

### 6.4 상태 관리 (Jotai)

discriminated union으로 4가지 상태 표현:

```typescript
type SnsSignalState =
  | { status: "IDLE" }
  | { status: "LOADING"; ticker: string }
  | { status: "SUCCESS"; ticker: string; result: SnsSignalResult }
  | { status: "ERROR"; ticker: string; error: string };
```

### 6.5 UI 컴포넌트 (`SnsSignalCard.tsx`)

4상태별 렌더링 + SUCCESS 시 풍부한 시각화:
- 시그널 배지 (상승/하락/중립, 색상 차별)
- 신뢰도 바
- 데이터 등급 표시
- 섹터 가중치 적용 시 배지
- 긍정/중립/부정 누적 비율 바
- 플랫폼별 결과 (한국어 라벨링)
- 근거 게시물 top 3 (감정 색상별)
- AI 한국어 요약
- 분석 시각

### 6.6 기존 페이지 통합 (`StockAnalysisView.tsx`)

영진님 종목 분석 결과 페이지에 자연스럽게 추가:

```tsx
// SUCCESS 분기에서 ticker 확정 후 SnsSignalCard 자동 fetch
const ticker = data.success ? data.result.ticker : "";
const { fetchSignal } = useSnsSignal();

useEffect(() => {
  if (ticker) fetchSignal(ticker);
}, [ticker, fetchSignal]);

// 오른쪽 패널: 다른 sub_agent 카드 + SnsSignalCard 같이
{agentResults.map(...)}
{ticker && <SnsSignalCard ticker={ticker} />}
```

**React Hooks 규칙 준수**:
- 컴포넌트 최상위에서 hook 호출 (조건부 분기 안 X)
- ticker는 삼항 연산자로 파생

**크로스 피처 의존성 회피**:
- `features/stock-recommendation`의 SignalBadge/ConfidenceBar UI 컴포넌트 import 안 함
- `features/sentiment` 안에 인라인 정의로 자급자족

---

## 7. 통합 검증

### 7.1 환경
- 백엔드: localhost:33333 (uvicorn)
- 프론트: localhost:3000 (Next.js dev)
- Postgres: 5433 (Docker)
- Redis: 6379 (Docker)

### 7.2 카카오 인증 우회

종목 분석 페이지에 영진님이 `useRequireAuth` 가드 박아둠 → 카카오 로그인 필요. 로컬 환경에서 카카오 콘솔에 redirect URL 미등록 → KOE101 에러.

**대응**: `app/sentiment-test/page.tsx` 임시 라우트 신설 (PR 미포함, 로컬 검증용)
- 인증 가드 없음
- `?ticker=005930` 쿼리로 SnsSignalCard 단독 렌더링

### 7.3 검증 결과

005930 (삼성전자) 호출:
- 시그널: 하락 (배지 빨강)
- 신뢰도: 40%
- 부정 60% / 중립 40% / 긍정 0%
- 데이터 등급: 하 (표본 5건)
- 플랫폼: 네이버 종목토론 5건
- 근거 게시물 (한글 정상): "내일 5퍼 이상 하락인거고", "매도사이드카", "개웃기네"
- AI 요약: "약한 하방 신호가 우세합니다"

---

## 8. Git 작업 흐름

### 8.1 백엔드 PR #93

브랜치: `Jojin-gorilla:main` → `EDDI-RobotAcademy:main`

커밋 히스토리 (시간순):
1. `feat(sentiment): SNS 도메인 신설 (DDD 헥사고날)`
2. `feat(sentiment): Reddit/Naver/Toss 수집기 구현`
3. `feat(sentiment): OpenAI gpt-5-mini 감정분석 어댑터`
4. `feat(sentiment): alembic sns_posts 테이블 마이그레이션`
5. `feat(news): 미국 주식 화이트리스트 + DI 버그 수정`
6. `refactor(sentiment): use Pydantic Body for POST endpoints`
7. `fix(sentiment): align with team standard model gpt-5-mini`
8. `fix(sentiment): naver finance EUC-KR 디코딩 버그 수정`
9. `feat(sentiment): 자동 collect 트리거 + Redis 결과 캐시` ← (검증 후 push 예정)

### 8.2 프론트엔드 PR

브랜치: `Jojin-gorilla:main` → `EDDI-RobotAcademy:main`

커밋:
1. `feat(sentiment): SNS sentiment analysis card on stock analysis result page`

### 8.3 트러블슈팅

- `git push origin main` 거절 (포크 자동 추가 파일과 충돌) → `--force` 사용 (작업 시작 전이라 안전)
- main.py 임시 주석 작업 시 별도 커밋 분리 (`git checkout main.py`로 원상복구)

---

## 9. 사용 기술 스택

### 백엔드
- **언어**: Python 3.13
- **프레임워크**: FastAPI
- **ORM**: SQLAlchemy (async)
- **마이그레이션**: Alembic
- **DB**: PostgreSQL (pgvector 확장)
- **캐시**: Redis (aioredis)
- **HTTP 클라이언트**: httpx
- **HTML 파서**: BeautifulSoup4
- **AI**: OpenAI gpt-5-mini

### 프론트엔드
- **프레임워크**: Next.js 16 (App Router, Turbopack)
- **UI 라이브러리**: React 19
- **언어**: TypeScript 5.9
- **상태 관리**: Jotai 2
- **스타일**: Tailwind CSS v4

### 개발 환경
- **OS**: Windows 11
- **셸**: PowerShell
- **컨테이너**: Docker Compose
- **버전 관리**: Git + GitHub PR

---

## 10. 작업 통계

| 항목 | 수치 |
|---|---|
| 백엔드 신규 파일 | 21개 (sentiment 19 + cache 2) |
| 백엔드 수정 파일 | 5개 |
| 백엔드 코드 라인 | +1,727 / -14 (PR #93 기준) |
| 프론트엔드 신규 파일 | 5개 |
| 프론트엔드 수정 파일 | 1개 |
| 프론트엔드 코드 라인 | +592 / -5 |
| 작업 기간 | 약 2주 (집중 작업 4월 27~29일) |
| GitHub Pull Request | 백엔드 1개 + 프론트엔드 1개 |

---

## 11. 알려진 제약 / TODO

- 토스 커뮤니티 수집기 미구현 (Playwright 도입 필요)
- DART API 키 미발급 환경에서 일부 기능 제한 (graceful degradation 처리)
- yfinance 한국 종목 일부 delisted 응답 (Yahoo 데이터 제한, 우회 방안 미구현)
- 카카오 콘솔 로컬 redirect URL 미등록 (운영 환경에서는 정상 동작)
- 캐시 무효화(invalidation) 정책 미구현 — 시간 기반 TTL만 (10분)
- 통합 테스트 자동화 미구현 (수동 검증)
