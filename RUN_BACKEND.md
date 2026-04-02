# 실행 방법

## 1. 의존성 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. 샘플 데이터 넣기

```bash
python3 -m scripts.seed_sample_data
```

## 3. 서버 실행

```bash
uvicorn app.main:app --reload
```

## 4. 기본 확인

- Swagger: `http://127.0.0.1:8000/docs`
- Health: `GET /api/v1/health`

## 5. 환경 변수

기본값:

- `DATABASE_URL=sqlite:///./sorissack.db`
- `AI_SERVER_URL=http://127.0.0.1:8001`
- `USE_MOCK_AI=true`

실제 AI 서버를 붙이려면:

```bash
export USE_MOCK_AI=false
export AI_SERVER_URL=http://127.0.0.1:8001
```

RDS를 붙일 때는:

```bash
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:PORT/DBNAME'
```
