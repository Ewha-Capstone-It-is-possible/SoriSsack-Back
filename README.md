# SoriSsack Backend

무발화 자폐 아동을 위한 AAC 서비스 **소리싹(SoriSsack)** 의 백엔드 API 서버입니다.  
이 서버는 프론트엔드와 AI 서버 사이의 중간 계층으로 동작하며, 카드 조회, 단어 추천, 사용 로그 저장, 문장 생성 결과 저장, 설정, 리포트, 감정일기, 보상, 보호자 인증 기능을 제공합니다.

### 프로젝트 저장소 구성 (3개 저장소)

소리싹 프로젝트는 다음 3개 저장소로 구성됩니다.

- **SoriSsack-Back** (이 저장소) — 백엔드 API 서버 (FastAPI, 포트 8000)
- **SoriSsack-AI** — AI 추론 서버 (FastAPI, 포트 8001). 추천·멀티모달·리포트 생성을 담당하며 백엔드가 내부 호출합니다.
- **SoriSsak-FE** — 프론트엔드 앱 (React Native / Expo)

프론트는 백엔드만 호출하고, 백엔드가 AI 서버를 내부 호출하는 구조입니다.


## 1. Project Description

소리싹 프로젝트의 목표는 무발화 자폐 아동이 그림 카드 기반으로 의사를 표현하고, 선택 기록을 바탕으로 다음 단어 추천과 문장 생성까지 이어지는 AAC 서비스를 제공하는 것입니다.

이 백엔드는 다음 역할을 담당합니다.

- 아동별 카드/카테고리 데이터 제공
- 프론트엔드의 카드 선택 로그 저장
- AI 추천 서버와의 연동
- 문장 생성 결과 저장
- 보호자 설정 및 부모 모드용 PIN 관리
- 사용 기록 기반 리포트/보상 데이터 제공
- 보호자 회원가입/로그인/세션 API 제공


## 2. Source Code Description

### 디렉터리 구조

```txt
Backend/
├── app/
│   ├── core/
│   │   └── config.py              # 환경 변수 및 설정
│   ├── routers/                   # API 라우터
│   │   ├── auth.py                # 보호자 회원가입/로그인/로그아웃/PIN 확인
│   │   ├── health.py              # 헬스 체크
│   │   ├── children.py            # 아동 정보 조회
│   │   ├── cards.py               # 카드 조회/추가/수정/즐겨찾기
│   │   ├── categories.py          # 카테고리 조회
│   │   ├── recommendations.py     # 다음 단어 추천
│   │   ├── logs.py                # 카드 선택 로그 저장
│   │   ├── expressions.py         # 문장 저장/멀티모달 생성
│   │   ├── settings.py            # 아동 설정 저장/조회
│   │   ├── mypage.py              # 마이페이지 요약
│   │   ├── reports.py             # 리포트/PDF 다운로드
│   │   └── rewards.py             # 포인트/배지 조회
│   ├── services/
│   │   └── ai_client.py           # AI 서버 호출 및 mock fallback
│   ├── db.py                      # DB 연결
│   ├── models.py                  # SQLAlchemy 모델
│   ├── schemas.py                 # Pydantic 스키마
│   └── main.py                    # FastAPI 엔트리포인트
├── scripts/
│   ├── seed_sample_data.py        # 데모용 DB 시드 적재
│   └── seed_data.json             # 샘플 카드/카테고리/아동 데이터
├── docs/
│   ├── API_SPEC.md                # 백엔드 API 설명
│   └── FRONTEND_API_SPEC.md       # 프론트 협업용 명세
├── run_dev.sh                     # 로컬 3-tier 개발 스택 실행 스크립트
├── requirements.txt               # Python 의존성
├── schema_mvp_postgres.sql        # PostgreSQL 스키마 예시
├── RUN_BACKEND.md                 # 실행 가이드
├── FRONTEND_API_HANDOFF.md        # 프론트 연결용 API 요약
└── FRONT_API_CHECKLIST.md         # Swagger 테스트 순서
```

### 주요 구현 기능

- 보호자 인증
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `GET /api/v1/auth/me`
  - `POST /api/v1/auth/logout`
  - `POST /api/v1/auth/verify-pin`

- 아동/카드/AAC 사용 흐름
  - 아동 정보 조회
  - 카드/카테고리 조회
  - 추천 단어 요청
  - 카드 사용 로그 저장
  - 문장 생성/저장 (멀티모달 — 아동별 선호 색상이 반영된 캐릭터 이미지 + 음성 생성, AI 서버 연동)
  - 부모 단어 추가 시 아동별 개인화 카드 이미지 자동 생성 (`POST /api/v1/cards`, AI 서버 연동)

- 확장 기능
  - 설정 저장/조회
  - 마이페이지 요약
  - 발달 리포트 조회/PDF 다운로드 (통계 + GPT 자연어 해석 + 그래프 PNG 이미지, AI 서버 연동)
  - 감정일기 조회 (`GET /api/v1/reports/{baby_id}/diary` — 그날 사용 기록을 GPT가 일기로 생성)
  - 보상/배지 조회


## 3. How to Build

Python 백엔드이므로 별도의 컴파일 빌드 단계는 없고, 가상환경 생성 후 의존성 설치로 실행 준비를 합니다.

### 요구 환경

- Python 3.9 이상
- `pip`
- macOS / Linux / Windows (Python 가상환경 지원 환경)

### 가상환경 생성

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 의존성 설치

```bash
pip install -r requirements.txt
```


## 4. How to Install

### 4-1. 저장소 준비

```bash
git clone <repo-url>
cd Backend
```

### 4-2. 환경 변수

기본값은 별도 `.env` 없이도 동작합니다.

기본 설정값:

```txt
DATABASE_URL=sqlite:///./sorissack.db
AI_SERVER_URL=http://127.0.0.1:8001
USE_MOCK_AI=true
API_PREFIX=/api/v1
APP_NAME=SoriSsack Backend
```

필요하면 루트에 `.env` 파일을 만들어 아래처럼 설정할 수 있습니다.

```env
DATABASE_URL=sqlite:///./sorissack.db
AI_SERVER_URL=http://127.0.0.1:8001
USE_MOCK_AI=true
```

### 4-3. 샘플 데이터 설치

Swagger 테스트나 데모를 위해 샘플 데이터를 적재합니다.

```bash
python3 -m scripts.seed_sample_data
```

이 스크립트는 다음 데이터를 DB에 생성합니다.

- 공용 카테고리
- 공용 카드 마스터
- 아동 5명
- 아동별 카드
- 카테고리 매핑


## 5. How to Run

### 5-1. 백엔드만 로컬 SQLite로 실행

```bash
uvicorn app.main:app --reload
```

실행 후 접속:

- Swagger: `http://127.0.0.1:8000/docs`
- Base API: `http://127.0.0.1:8000/api/v1`

### 5-2. PostgreSQL 연결 실행

```bash
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:PORT/DBNAME'
uvicorn app.main:app --reload
```

### 5-3. AI 서버 포함 로컬 통합 실행

형제 디렉터리에 AI 서버가 있을 경우 아래 스크립트로 로컬 3-tier 실행이 가능합니다.

```bash
./run_dev.sh
```

이 스크립트는 다음을 순서대로 수행합니다.

- AI 서버 가상환경 확인 및 실행
- 백엔드 가상환경 확인 및 실행
- 샘플 데이터 자동 시드


## 6. How to Test

현재 자동화된 단위 테스트 파일은 포함되어 있지 않으며, **Swagger 기반 수동 테스트**를 기준으로 검증합니다.

### 기본 테스트 절차

1. 서버 실행

```bash
uvicorn app.main:app --reload
```

2. Swagger 접속

```txt
http://127.0.0.1:8000/docs
```

3. 주요 테스트 순서

- `GET /api/v1/health`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/cards/{baby_id}`
- `POST /api/v1/recommendations`
- `POST /api/v1/logs`
- `POST /api/v1/expressions/generate`
- `GET /api/v1/reports/{baby_id}`
- `GET /api/v1/reports/{baby_id}/diary`
- `GET /api/v1/mypage/{baby_id}`
- `GET /api/v1/rewards/{baby_id}`

자세한 테스트 순서는 [FRONT_API_CHECKLIST.md](./FRONT_API_CHECKLIST.md)에 정리되어 있습니다.

### 문법 검증

간단한 문법 검증은 아래와 같이 수행할 수 있습니다.

```bash
PYTHONPYCACHEPREFIX=/tmp/codex-pycache python3 -m compileall app
```


## 7. Description of Sample Data

샘플 데이터는 `scripts/seed_data.json` 과 `scripts/seed_sample_data.py` 로 제공됩니다.

### 포함 데이터

- `categories`
  - 감정, 음식/음료, 놀이 등 카테고리 정보
- `card_master`
  - 공용 카드 단어 사전
- `card_category_map`
  - 카드-카테고리 매핑 정보
- `babies`
  - 데모용 아동 정보
- `baby_cards`
  - 아동별 카드 데이터

### 목적

- Swagger에서 바로 테스트 가능
- 프론트엔드와 추천 결과의 ID 네임스페이스를 맞춤
- 발표/데모에서 동일한 카드 ID와 추천 결과를 재현 가능


## 8. Database or Data Used

### 실제 운영 DB (배포 환경)

- **AWS RDS PostgreSQL** — 배포(EC2) 환경에서 **백엔드와 AI 서버가 동일한 RDS 인스턴스를 공유**합니다.
  실제 아동·카드·로그·문장 데이터가 이 RDS에 저장되며, 두 서버는 같은 데이터를 바라봅니다.
- DB 접속 정보는 `DATABASE_URL` 환경변수로 주입하며, 보안상 저장소에는 포함하지 않습니다.

### 재현/채점용 기본 DB (DB 없이 동작)

- **SQLite** (`sorissack.db`) — 별도 DB 서버 없이 clone 후 바로 실행할 수 있도록 기본값으로 제공합니다.
  채점자는 RDS 접근 권한 없이도 `seed_sample_data`로 샘플 데이터를 적재해 전체 흐름을 재현할 수 있습니다.
- PostgreSQL 스키마 예시: `schema_mvp_postgres.sql` (RDS와 동일 구조 재구성용)

> 즉 **운영은 공유 RDS(PostgreSQL), 재현은 로컬 SQLite + 샘플 데이터**로 동작합니다.
> (RDS 비밀번호는 공개 저장소에 올릴 수 없으므로, 재현 가능성을 위해 DB 없이 도는 기본 모드를 함께 제공합니다.)

### 주요 테이블

- `baby_basic_information`
- `card_master`
- `baby_card`
- `category_master`
- `card_category_map_master`
- `baby_category`
- `baby_card_category_map`
- `baby_vocab_log`
- `sentence_master`
- `baby_app_settings`
- `parent_account`
- `parent_session`


## 9. Description of Used Open Source

이 프로젝트에서 사용한 주요 오픈소스는 아래와 같습니다.

- **FastAPI**
  - REST API 서버 프레임워크
- **Uvicorn**
  - ASGI 서버
- **SQLAlchemy**
  - ORM 및 DB 모델링
- **Pydantic**
  - 요청/응답 스키마 검증
- **httpx**
  - 내부 AI 서버 호출
- **python-dotenv**
  - `.env` 환경 변수 로딩
- **psycopg**
  - PostgreSQL 드라이버

의존성 목록은 `requirements.txt` 에 포함되어 있습니다.


## 10. Additional Documents

- [RUN_BACKEND.md](./RUN_BACKEND.md)
  - 실행 방법 요약
- [docs/API_SPEC.md](./docs/API_SPEC.md)
  - API 명세
- [FRONTEND_API_HANDOFF.md](./FRONTEND_API_HANDOFF.md)
  - 프론트 협업용 API 문서
- [FRONT_API_CHECKLIST.md](./FRONT_API_CHECKLIST.md)
  - Swagger 테스트 체크리스트


## 11. Quick Start

가장 빠른 로컬 실행 순서는 아래와 같습니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m scripts.seed_sample_data
uvicorn app.main:app --reload
```

이후 브라우저에서 아래 주소로 접속하면 됩니다.

```txt
http://127.0.0.1:8000/docs
```
