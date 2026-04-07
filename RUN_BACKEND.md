# 실행 방법

## 1. 의존성 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. 로컬 SQLite로 빠르게 테스트할 때

기본값은 SQLite다.

```bash
python3 -m scripts.seed_sample_data
uvicorn app.main:app --reload
```

## 3. PostgreSQL RDS에 연결할 때

팀원이 준 RDS 접속 정보를 받은 뒤 아래처럼 환경 변수를 설정한다.

```bash
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:PORT/DBNAME'
export USE_MOCK_AI=false
export AI_SERVER_URL='http://127.0.0.1:8001'
uvicorn app.main:app --reload
```

예시:

```bash
export DATABASE_URL='postgresql+psycopg://postgres:password@localhost:5432/sorissack'
```

## 4. 서버 실행

로컬 SQLite 테스트:

```bash
uvicorn app.main:app --reload
```

PostgreSQL RDS 연결:

```bash
uvicorn app.main:app --reload
```

## 5. 기본 확인

- Swagger: `http://127.0.0.1:8000/docs`
- Health: `GET /api/v1/health`

## 6. 환경 변수

기본값:

- `DATABASE_URL=sqlite:///./sorissack.db`
- `AI_SERVER_URL=http://127.0.0.1:8001`
- `USE_MOCK_AI=true`

실제 AI 서버를 붙이려면:

```bash
export USE_MOCK_AI=false
export AI_SERVER_URL=http://127.0.0.1:8001
```

PostgreSQL RDS를 붙일 때는:

```bash
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:PORT/DBNAME'
```
