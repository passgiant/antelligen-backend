# Antelligen — AI Multi-Agent 투자 인텔리전스 플랫폼

> 3·4차 프로젝트 발표 자료 (팀원별 기여 중심)
> 발표일: 2026-05-02

---

## Slide 1 — 표지

### Antelligen

**AI Multi-Agent 기반 투자 인텔리전스 플랫폼**

> "AI가 대신 투자하는 시대가 아니라,
> AI의 판단을 사람이 검증하고 통제하는 구조"

- 발표일: 2026-05-02
- 팀: Antelligen (5인)

---

---

# Part 1. 프로젝트 개요

---

## Slide 2 — Antelligen이란?

### 한 줄 요약

> 뉴스·공시·재무·SNS·거시경제 데이터를 **5개의 전문 AI 에이전트**가 분담 분석하고,
> 종목의 투자 시그널과 가격 변동 원인을 **검증 가능한 근거**와 함께 제공하는 플랫폼

### 핵심 문제 의식

| 기존 서비스의 한계 | Antelligen의 접근 |
|---|---|
| 단일 LLM에 모든 것 위임 → 블랙박스 | 역할별 에이전트가 협업 → 추적 가능 |
| 뉴스 8종목만 분석 가능 | 전 KRX 2,500+ / 미국 종목 확장 |
| 출처 무관 단순 평균 | 출처 신뢰도(DART > Bloomberg > SNS) 가중치 |
| 시그널만 있고 맥락 없음 | 사업개요 카드 + 인과관계 분석 동시 제공 |
| 비용 통제 불가 | 다층 캐시 + 조건부 실행으로 LLM 비용 통제 |

---

## Slide 3 — 팀 구성 & 역할 분담

### 5인 역할 분담

| 팀원 | 담당 영역 | 핵심 키워드 |
|---|---|---|
| **김영진** | 데이터 인프라 확장 · 신뢰도 가중치 · 에이전트 통합 | TickerKeywordResolver · SourceTier · On-demand 분산락 |
| **김세진** | 감정 분석 에이전트 전체 구축 | sentiment 도메인 신설 · Reddit/네이버 수집 · GPT 감정분석 |
| **문우성** | 거시 경제 현황판 | 금리·유가·환율 자동수집 · Risk-ON/OFF 판단 |
| **김민규** | 히스토리 · 인과관계 에이전트 & 대시보드 | LangGraph · 이상치 탐지 · 타임라인 시각화 |
| **이민영** | 개인화 · 스마트머니 시스템 | watchlist · KRX 수집 · SEC 13F 글로벌 포트폴리오 |

### 에이전트 협업 구조

```
사용자 입력 (종목 코드)
        │
        ▼
┌───────────────────────────────────────────┐
│          메인 에이전트 (김영진 통합)        │
│                                           │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐    │
│  │뉴스  │ │공시  │ │재무  │ │감정  │    │
│  │에이전│ │에이전│ │에이전│ │에이전│◄── 김세진
│  │트    │ │트    │ │트    │ │트    │    │
│  └──────┘ └──────┘ └──────┘ └──────┘    │
│                    +                      │
│  ┌────────────────┐  ┌────────────────┐  │
│  │거시경제 에이전트│  │히스토리 에이전트│  │
│  │(문우성)        │  │(김민규)        │  │
│  └────────────────┘  └────────────────┘  │
└───────────────────────────────────────────┘
        │
        ▼
SourceTier 가중치 적용 → 종합 시그널 산출
```

---

---

# Part 2. 팀원별 개발 내용

---

---

## 👤 김영진 — 데이터 인프라 확장 · 신뢰도 시스템 · 에이전트 통합

---

## Slide 4 — 김영진 (1/3): 전 종목 지원 + 미국 주식 확대

### Before vs After

| 항목 | Before | After |
|---|---|---|
| 뉴스 분석 가능 종목 | 하드코딩 8개 (삼성전자, SK하이닉스 등) | **전 KRX 2,500+ 종목** |
| 미국 종목 | 미지원 | AAPL, TSLA, NVDA 등 **전 미국 상장주** |
| 재무 데이터 | DART 정기공시만 | DART + **yfinance(US)** + **잠정실적** |
| 공시 데이터 | DART만 | DART + **SEC EDGAR(8-K/10-K/10-Q)** |

### 핵심 구현 — TickerKeywordResolverPort

```
기존 문제:
  TICKER_TO_KEYWORDS = {"005930": ["삼성전자", ...], ...}
  → 8개 외 종목: 키워드 없음 → 시그널 산출 불가

해결:
  TickerKeywordResolverPort.resolve(ticker) → list[str]
  → DB에서 stock_name 동적 조회 + 동의어(alias) 결합
  → "000270" (기아) 입력 → ["기아", "기아차", "KIA"] 자동 생성
```

### MarketRegion — KR/US 분기의 기반

```python
class MarketRegion(Enum):
    KR_KOSPI / KR_KOSDAQ / KR_KONEX
    US_NYSE / US_NASDAQ / UNKNOWN

# ticker 형식으로 자동 추론
# 6자리 숫자 → KR,  AAPL (1~5 알파벳) → US_NASDAQ
```

- 뉴스: KR → 네이버 뉴스, US → **SerpAPI (gl=us, hl=en)**
- 재무: KR → DART, US → **yfinance 분기 EPS**
- 공시: KR → DART, US → **SEC EDGAR**

---

## Slide 5 — 김영진 (2/3): 출처 신뢰도 가중치 시스템

### 4단계 SourceTier

| 티어 | 대표 출처 | 가중치 |
|---|---|---|
| **HIGH** | DART 공시, SEC EDGAR, 기업 IR | 1.0 |
| **MEDIUM** | Bloomberg, Reuters, WSJ, 한경, 매경 | 0.7 |
| **MEDIUM_LOW** | 국내 증권사 리포트 (buy-bias 보정) | 0.5 |
| **LOW** | SNS, 유튜브, 커뮤니티, 일반 뉴스 | 0.3 |

### 엔터테인먼트 섹터 — SNS 가중치 보정

```python
_SECTOR_OVERRIDE = {
    Sector.ENTERTAINMENT: ({"youtube.com", "x.com", "instagram.com"}, SourceTier.MEDIUM)
}
# HYBE / SM / JYP / YG 종목 분석 시
# YouTube·X 기사가 LOW(0.3) → MEDIUM(0.7) 으로 자동 승격
```

> 엔터·밈주처럼 SNS가 핵심 시그널인 섹터는 SNS 가중치를 올려야 정확한 분석이 가능

### 종합 시그널 산출 — 가중 평균

```
각 서브에이전트 결과
  └─ news agent   → source_tier = MEDIUM  → confidence × 0.7
  └─ disclosure   → source_tier = HIGH    → confidence × 1.0
  └─ finance      → source_tier = HIGH    → confidence × 1.0
  └─ sentiment    → source_tier = LOW     → confidence × 0.3
                                                ↓
                           weighted_score 합산 → bullish/bearish/neutral
```

---

## Slide 6 — 김영진 (3/3): 운영 안정성 — On-demand 공시 + 조건부 Startup

### On-demand 공시 수집 + Redis 분산 락

```
문제: 스케줄러 batch 수집 → 방금 본 종목의 최신 공시가 다음 배치까지 없음
     동일 종목 동시 5개 요청 → DART API 5중 호출 → quota 낭비

해결: Redis SET NX EX (atomic) 분산 락
  요청 A ──→ 락 획득 → DART 5개 유형 병렬 fetch → DB upsert → 락 해제
  요청 B ──→ 락 대기 (최대 30초) → DB에 결과 있으면 즉시 공유
  요청 C ──┘

보장: TTL 60초 → 프로세스 죽어도 deadlock 없음
     Redis 장애 시 graceful degrade (락 없이 진행)
```

### 조건부 Startup 잡 — 비용 절약

| 잡 | 조건 | 절약 효과 |
|---|---|---|
| `refresh_company_list` | 24시간 이내 성공 이력 있으면 **스킵** | KRX 전종목 재호출 방지 |
| `process_documents` | 미처리 공시가 1건이라도 있을 때만 실행 | 불필요한 LLM 처리 방지 |
| `refresh_market_risk` | Redis에 4시간 이내 스냅샷 있으면 **복원** | **YouTube quota + LLM 비용 최대 절약** |

### 사업개요 카드 — 메인 에이전트 답변 강화

```
기존: 시그널(bullish/bearish)만 반환
개선: 사업개요 카드 동시 제공
  - asyncio.create_task → 병렬 fetch (latency 거의 0)
  - RAG (DART 사업보고서 본문) → LLM 요약 → 7일 캐시
  - LLM 합성 답변 컨텍스트에도 주입 → 답변 품질 향상
```

---

---

## 👤 김세진 — 감정 분석 에이전트 전체 구축

---

## Slide 7 — 김세진 (1/2): Sentiment 도메인 신설 (DDD 헥사고날)

### 담당 범위: 백엔드 21개 파일 신규, +1,727 lines / 프론트엔드 5개 파일 신규, +592 lines

### 새로 만든 감정 분석 파이프라인

```
SNS 수집 (3개 채널)
  ├── Reddit — wallstreetbets, stocks, Korean_Stocks
  │     └── .json 무인증 엔드포인트 (신규 계정 OAuth 락 우회)
  ├── 네이버 종목토론 — HTML 스크래핑 (BeautifulSoup4)
  │     └── EUC-KR 디코딩 버그 직접 발견·수정
  └── 토스 커뮤니티 — 인터페이스 보존 (SPA 봇 탐지로 stub)
         ↓
GPT 감정분석 (openai_sns_signal_adapter)
  - 게시물별 positive/negative/neutral 분류
  - bullish/bearish/neutral 종합 시그널
  - confidence + overall_negative_ratio (VIX 비교용)
         ↓
SnsSignalResult 표준 DTO
  → 메인 에이전트가 confidence × source_tier_weight 로 자연스럽게 합산
```

### 밈 티커 · 섹터별 가중치

| 종목 유형 | 가중치 | 이유 |
|---|---|---|
| TSLA, GME, AMC, NVDA 등 밈 티커 | confidence × **1.35** | SNS 반응이 실제 가격에 직접 영향 |
| 엔터(JYP/SM/HYBE/YG) | × **1.3** | 아티스트 SNS가 핵심 알파 소스 |
| 게임주 | × **1.2** | 커뮤니티 여론이 출시 성과와 연동 |
| 일반 종목 | × 1.0 | 기본값 |

### DB 신설 — `sns_posts` 테이블

```sql
-- 김세진이 직접 Alembic 마이그레이션 작성·적용
CREATE TABLE sns_posts (
  id SERIAL PRIMARY KEY,
  platform VARCHAR NOT NULL,  -- reddit / naver_finance / toss_community
  ticker VARCHAR NOT NULL,
  title TEXT, body TEXT, author VARCHAR, url VARCHAR,
  posted_at TIMESTAMP, collected_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_sns_posts_ticker_platform ON sns_posts(ticker, platform);
```

---

## Slide 8 — 김세진 (2/2): 운영 이슈 자체 해결 + 프론트엔드

### 자체 발견·수정한 버그 및 이슈

#### 1) 네이버 한글 깨짐 (EUC-KR 디코딩 버그)

```python
# Before — DB에 한글이 깨져 저장됨 (예: "@@@ ��ш꼍遺�")
content = resp.content.decode("euc-kr", errors="replace")

# After — 정상 한글 저장
soup = BeautifulSoup(resp.content, "html.parser", from_encoding="euc-kr")
```

#### 2) 라우터 DI 버그 수정

```python
# 뉴스 라우터에서 keyword_resolver 누락 발견 → 직접 수정
# Before: AnalyzeNewsSignalUseCase(repository=repo)  ← keyword_resolver 없음
# After:  AnalyzeNewsSignalUseCase(repository=repo, keyword_resolver=TickerKeywordResolver(...))
```

#### 3) Redis 캐시 + 자동 collect 트리거 추가

```
analyze 엔드포인트 흐름 (보강 후):
  1. Redis cache.get(ticker) → HIT이면 즉시 반환 (GPT 호출 X, 비용 절약)
  2. DB에 게시물 5건 미만 → CollectSnsPostsUseCase 자동 호출
  3. GPT 분석 → 결과를 Redis TTL 600초 캐시에 저장
```

### 프론트엔드 — SnsSignalCard 컴포넌트

```
SnsSignalCard 4가지 상태 렌더링:
  IDLE → LOADING → SUCCESS / ERROR

SUCCESS 시 시각화 요소:
  ▸ 시그널 배지 (상승↑ / 하락↓ / 중립 — 색상 차별)
  ▸ 신뢰도 게이지 바
  ▸ 긍정/중립/부정 누적 비율 바
  ▸ 플랫폼별 결과 (Reddit / 네이버 한국어 라벨)
  ▸ 근거 게시물 top 3 (감정 색상 마킹)
  ▸ AI 한국어 요약
```

> 김영진의 `StockAnalysisView` 페이지에 SnsSignalCard 자연스럽게 통합
> — 다른 sub_agent 카드들과 동일 패널에 나란히 표시

---

---

## 👤 문우성 — 거시 경제 현황판

---

## Slide 9 — 문우성: 데일리 거시경제 현황판 + Risk-ON/OFF 판단

### 담당 기능 한눈에

```
매일 자동 수집 → 저장 → 판단
  ├── 금리 (기준금리, 국채 금리)
  ├── 유가 (WTI, 브렌트)
  ├── 환율 (USD/KRW, DXY)
  └── 주요 경제 일정 (FOMC, CPI 발표 등)
         ↓
  전일 대비 등락 자동 계산
         ↓
  Risk-ON / Risk-OFF 판단
  + 핵심 변수 기반 근거 자동 생성
```

### Risk-ON / Risk-OFF 자동 판단

| 판단 | 의미 | 근거 예시 |
|---|---|---|
| **Risk-ON** | 위험자산 선호 심리 강화 | "금리 하락 + 달러 약세 → 성장주 매수 환경" |
| **Risk-OFF** | 위험자산 회피 심리 강화 | "VIX 급등 + 달러 강세 → 안전자산 선호" |

### 메인 에이전트와의 연결

> 문우성의 거시경제 현황판 데이터는 **김영진이 통합**하여 메인 에이전트 종합 시그널 산출에 반영
> → 거시 환경이 불안정할 때 전체 confidence가 하향 조정

---

---

## 👤 김민규 — 히스토리 · 인과관계 에이전트 & 대시보드

---

## Slide 10 — 김민규 (1/2): History Agent — 8단계 타임라인 생성 파이프라인

### 핵심 기능

> 종목 코드 하나를 입력하면, **8개 외부 소스**에서 데이터를 모아
> "시점이 명확한 사건만" 골라 **한 줄 타임라인**을 자동 생성

### 8단계 파이프라인

```
Step 0  ticker 정규화 + 자산 유형(EQUITY/INDEX/ETF) 자동 판별
   ↓
Step 1  Redis 캐시 HIT? → 즉시 반환 (~50ms)
   ↓ MISS
Step 2  4개 소스 비동기 병렬 수집 (asyncio.gather)
        ├── yfinance  OHLCV 가격 데이터
        ├── DART + yfinance  기업 이벤트 (실적·배당)
        ├── SEC + DART  공시
        └── Finnhub → GDELT → Naver  뉴스
   ↓
Step 3  Jaccard 유사도 ≥ 0.8 공시 중복 제거
        (같은 사건이 DART + SEC + Yahoo 에서 동시 들어올 때)
   ↓
Step 4  DB에서 기존 enrichment 로드 → title/causality 즉시 주입
   ↓
Step 5  신규 이벤트 병렬 enrichment
        ├── SURGE/PLUNGE 상위 3건 → Causality Agent 호출
        ├── 가격 이벤트 제목 생성
        ├── 기타 이벤트 제목 생성
        └── 공시 한글 요약
   ↓
Step 6  EventClassifier v2 + importance_score 산정
   ↓
Step 7  DB upsert (event_enrichments, detail_hash PK)
   ↓
Step 8  Redis setex 3600s TTL → 응답 반환
```

### 자산 유형별 파이프라인 분기

| 자산 유형 | 예시 | 파이프라인 |
|---|---|---|
| **EQUITY** | AAPL, 005930 | 기업 이벤트 + 공시 + 뉴스 + 거시 컨텍스트 |
| **INDEX** | ^GSPC, ^KS11 | 지수별 맞춤 매크로 이벤트 + 인과 규칙 |
| **ETF** | SPY, QQQ | 자산 클래스 매크로 + 상위 5개 보유 종목 분해 |

---

## Slide 11 — 김민규 (2/2): Causality Agent + Dashboard UI

### Causality Agent — "왜 이 날 이 종목이 급등/급락했는가"

```
이상치 봉(Anomaly Bar) 자동 탐지
  └─ 가격 변동이 통계적으로 비정상인 봉 자동 식별
         ↓
사용자가 차트 마커 클릭 (lazy 호출)
         ↓
LangGraph StateGraph 4노드 워크플로우
  Node 1: 날짜 주변 뉴스·공시·거시지표 병렬 수집
  Node 2: LLM Tool Use (8개 도구 자동 선택·호출)
  Node 3: 가설 생성 + 신뢰도 평가
  Node 4: 환각 방지 후처리 + 출처 검증
         ↓
가설 DB 영구 저장 (detail_hash PK)
  → 동일 봉에 대한 두 번째 요청부터 ~50ms 응답
```

### Dashboard UI — `/dashboard`

```
┌──────────────────────────────┬──────────────┐
│  NasdaqChart                 │ StockSearch  │
│  + 이상치 봉 마커 자동 표시  │              │
│  (SURGE/PLUNGE/VIX_SPIKE 등) ├──────────────┤
│                              │AssetProfile  │
├──────────────────────────────┤Panel         │
│  HistoryPanel                │              │
│  (타임라인 카드 목록)        │              │
│  카드 클릭 → 차트 봉 하이라이│              │
└──────────────────────────────┴──────────────┘
상태: Jotai 2.19 (atomWithStorage — localStorage 영속)
```

### SSE 스트리밍 API

```
GET /api/v1/history-agent/timeline/stream

이벤트 타입:
  progress → 처리 중인 단계 실시간 표시
  done     → 완성된 타임라인 데이터
  error    → 에러 메시지

효과: 사용자는 4~8초 로딩 대기 화면 대신 진행 상황을 실시간으로 확인
```

---

---

## 👤 이민영 — 개인화 시스템 & 스마트머니 대시보드

---

## Slide 12 — 이민영 (1/2): 관심종목 기반 개인화

### 담당 기능 구조

```
로그인 사용자
    │
    ▼
/settings/watchlist — 관심종목 등록·수정
  ├── 테마 그룹별 종목 버튼 (반도체 / 자동차 / 바이오 / ...)
  ├── 버튼 클릭으로 토글
  └── 현재 선택 개수 실시간 표시

    │ 관심종목 등록 완료
    ├─→ /news 뉴스 페이지 개인화
    │     - 등록 종목명으로 DB 뉴스 필터링
    │     - 종목당 최대 10건, URL 기준 중복 제거
    │     - 미등록 시: 전체 최신 뉴스 100건 기본 제공
    │
    └─→ /youtube 유튜브 페이지 개인화
          - 관심종목명 최대 5개를 YouTube 검색 키워드로 사용
          - 병렬 검색 → 중복 영상 제거 → 최신순 9개
          - 미등록 시: 일반 주식 투자 키워드 5개로 대체
```

### 인증 방식

- Redis 세션 기반 (쿠키 `user_token` 또는 `Authorization: Bearer` 모두 지원)
- 미로그인 사용자는 기본 콘텐츠, 로그인 사용자는 개인화 콘텐츠

---

## Slide 13 — 이민영 (2/2): 스마트머니 대시보드

### 스마트머니란?

> 개인 투자자보다 정보력·자본력이 높은 **외국인·기관·저명 투자자**의 거래 흐름을 추적해
> 어디에 "큰 돈"이 들어오고 있는지 파악하는 투자 분석

### 3개 섹션 구성

#### ① 국내 스마트머니 집중 매수 종목 (KRX 데이터)

```
수집: 매 영업일 16:30 KST 자동 수집
      KRX → KOSPI + KOSDAQ 전 종목 → 외국인/기관합계/개인 순매수 저장

집중도 점수 계산:
  외국인 점수 = 내 순매수 ÷ 전체 최대값 (0~1 정규화)
  기관 점수   = 내 순매수 ÷ 전체 최대값 (0~1 정규화)
  집중도 점수 = (외국인 점수 + 기관 점수) ÷ 2 × 100

→ 외국인과 기관이 "동시에" 산 종목만 교집합으로 추출
```

#### ② 해외 스마트머니 (SEC 13F 공시 — 19명 글로벌 투자자)

```
수집 대상: Warren Buffett, Michael Burry, Ray Dalio,
          Cathie Wood, Bill Ackman, George Soros 등 19명

수집 주기: 분기별 (2·5·8·11월 15일 09:00 KST)

처리:
  SEC EDGAR 13F-HR XML 파싱
  → OpenFIGI API로 CUSIP → 티커 변환
  → 직전 분기와 비교 → 신규편입/비중확대/비중축소/청산 배지 자동 생성
```

#### ③ 국내 저명 투자자 포트폴리오 (DART 대량보유보고 — 10명)

```
수집 대상: 국민연금, 미래에셋, 삼성, KB운용, 박현주, 강방천 등 10명
수집 주기: 매월 1일 03:00 KST

처리:
  DART corp_code XML → 상장주 상위 800종목
  → 동시 10개 병렬 API 요청 → 5% 이상 대량보유 매칭
```

### 투자자별 순매수 추이 차트

```
행 클릭 → 해당 종목 최근 30일 추이 펼침
  X축: 날짜
  Y축: 순매수금액 (억 원)
  라인 3개: 외국인(파랑) / 기관(초록) / 개인(노랑)
  캐시: Redis TTL 10분
```

---

---

# Part 3. 통합 기술 아키텍처

---

## Slide 14 — 전체 시스템 아키텍처

### 레이어 구조

```
외부 데이터 소스 (10종)
  ├── 한국: DART, KRX, 네이버 뉴스
  ├── 미국: SEC EDGAR, yfinance, SerpAPI, Finnhub, GDELT, FRED, OpenFIGI
  └── SNS: Reddit, 네이버 종목토론
                    │
                    ▼
antelligen-backend (FastAPI + DDD 헥사고날 아키텍처)
  ├── 도메인: agent / news / disclosure / finance / sentiment / history_agent
  │           causality_agent / company_profile / smart_money / user
  ├── 캐시: Redis (1h/10m/4h/7d 다층 TTL)
  ├── DB: PostgreSQL + pgvector (RAG, event_enrichments)
  ├── 스케줄러: APScheduler (20+ cron job)
  └── LLM: OpenAI GPT (LangChain Tool Use + LangGraph StateGraph)
                    │ REST API + SSE
                    ▼
antelligen-frontend (Next.js 16 App Router)
  ├── 상태 관리: Jotai 2 (atomWithStorage)
  ├── 차트: lightweight-charts (캔들) + Recharts (보조)
  └── 스타일: Tailwind CSS 4
```

### 핵심 비기능 요건 달성

| 요건 | 달성 방법 |
|---|---|
| **성능** | 3-에이전트 병렬 + Redis 1h 캐시 → 재요청 ~50ms |
| **비용 통제** | 조건부 startup + 다층 TTL + 분산 락 멱등성 |
| **부분 실패 허용** | `asyncio.gather(return_exceptions=True)` |
| **투명성** | SourceTier 가중치 수치 노출 + LangSmith Tracing |
| **확장성** | Port/Adapter 패턴 → 새 데이터 소스 추가 시 기존 코드 무수정 |

---

## Slide 15 — 팀원 간 협업 포인트

### 서로의 코드가 맞닿는 지점

| 연결 | 내용 |
|---|---|
| **김영진 ↔ 김세진** | 김세진이 만든 `SnsSignalResult` DTO를 김영진의 메인 에이전트가 `source_tier_weight`로 가중합산 |
| **김영진 ↔ 문우성** | 문우성의 거시경제 스냅샷을 김영진의 lifespan이 Redis에서 복원·관리 |
| **김영진 ↔ 김민규** | 김민규의 History Agent 타임라인 데이터가 김영진의 회사 프로필 카드와 동일 응답에 합쳐짐 |
| **김영진 ↔ 이민영** | 이민영의 watchlist 기반 개인화 페이지에서 김영진의 메인 에이전트 분석 결과 활용 |
| **김세진 ↔ 이민영** | 이민영의 뉴스 개인화 피드에 김세진이 수정한 뉴스 DI 버그 픽스가 적용됨 |

### 공통 설계 원칙

1. **Port/Adapter** — 도메인 레이어에 외부 의존성 Zero
2. **asyncio.gather** — I/O 병렬화로 지연 최소화
3. **DTO 표준화** — 모든 서브에이전트가 동일한 응답 형태 → 통합 용이
4. **Feature Flag** — 새 기능은 `enable_xxx: bool = False`로 배포 후 단계적 활성화

---

---

# Part 4. 성과 & 결론

---

## Slide 16 — 개발 성과 요약

### 팀원별 핵심 숫자

| 팀원 | 신규 파일 | 핵심 성과 |
|---|---|---|
| **김영진** | 40+ 파일 (7개 작업) | KRX 2,500+ 종목 + 미국 주식 + 출처 가중치 시스템 |
| **김세진** | 백엔드 21 + 프론트 5 = 26개 | Sentiment 도메인 + 1,727 lines + 한글 디코딩 버그 수정 |
| **문우성** | - | 거시경제 현황판 + Risk-ON/OFF 자동 판단 |
| **김민규** | - | History/Causality Agent + Dashboard (8단계 파이프라인) |
| **이민영** | - | watchlist 개인화 + KRX + SEC 13F 19명 + DART 10명 |

### 기술적 성취

- **8종 외부 데이터 소스** 통합 (DART, SEC EDGAR, yfinance, KRX, SerpAPI, Finnhub, GDELT, FRED)
- **5개 전문 에이전트** 협업 (뉴스, 공시, 재무, 감정, 거시경제, 히스토리, 인과관계)
- **DDD + 헥사고날 아키텍처** 전 도메인 일관 적용
- **운영 비용 통제** — 다층 캐시 + 조건부 startup으로 LLM/API quota 절약
- **투명한 의사결정** — SourceTier 가중치 + LangSmith Tracing

---

## Slide 17 — 마무리

### Antelligen이 증명한 것

> 5인 팀이 **역할을 명확히 나누고**,
> 각자의 도메인에서 **깊이 있는 구현**을 하면서도
> **공통 인터페이스(Port/DTO)**로 자연스럽게 통합되는
> 멀티 에이전트 시스템을 실제로 만들 수 있다

### Phase 2 후보 (팀원별)

| 팀원 | 다음 단계 |
|---|---|
| 김영진 | SourceTier CSV/DB 이관 → 무재배포 튜닝, US 티커 단계적 활성화 |
| 김세진 | Playwright 기반 토스 커뮤니티 수집기 구현 |
| 문우성 | 거시경제 지표 + VIX 비교 그래프 시각화 |
| 김민규 | ETF 구성 종목 인과관계 분해 고도화 |
| 이민영 | 스마트머니 알림 (관심종목에 기관 순매수 급증 시 push) |

---

> **"AI가 모든 걸 결정하는 게 아니라,
> 각 전문 AI가 맡은 영역을 깊이 파고,
> 사람이 그 과정을 검증할 수 있는 구조 — 그것이 Antelligen"**
