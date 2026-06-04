# 소리싹 통합 실행 가이드 (AI ↔ Backend ↔ Frontend)

세 저장소를 **형제 디렉터리**로 두고 함께 띄운다.

```
<parent>/
├── sorisak-ai/        # AI 추론 서버 (FastAPI)  : 추천 회귀 + GPT selector + 멀티모달
├── SoriSsack-Back/    # Backend API (FastAPI)   ← 이 저장소 (hyewon 브랜치)
└── SoriSsak-FE/       # Frontend (Expo / RN)
```

## 아키텍처

```
[Frontend :Expo]
   │  axios, baseURL = http://localhost:8000/api/v1
   ▼
[Backend :8000]  ──(USE_MOCK_AI=false)──▶  [AI :8001]
   │  SQLite (sorissack.db)                   DATA_SOURCE=dummy (외부 키 불필요)
```

- 프론트는 **Backend 6개 엔드포인트만** 호출한다.
- 추천(`POST /recommendations`)을 받으면 Backend 가 내부적으로 AI `/recommend` 를 호출한다.
- AI 가 꺼져 있거나 오류여도 Backend 는 mock 으로 graceful fallback → 화면이 비지 않는다.

## 핵심: 데이터 ID 정합성

Backend 시드(`scripts/seed_data.json`)는 **AI 의 공유 단어 사전(card_master 95개)·아동 5명·
baby_card 100개와 동일한 ID**로 채워진다. 따라서 AI 가 추천으로 돌려준
`baby_card_id / card_id / text` 가 프론트의 `GET /cards/{baby_id}` 카드와 정확히 매칭되어
추천 단어가 화면에 그대로 렌더링된다. (FE 매칭 순서: baby_card_id → card_id → text)

`seed_data.json` 은 `sorisak-ai/dummy_data.py` 에서 추출한 커밋 산출물이라, 시드 시
AI 코드에 의존하지 않는다.

---

## 빠른 실행 (권장)

```bash
cd SoriSsack-Back
./run_dev.sh          # AI(8001) + Backend(8000) 동시 기동 (+ 시드 자동)
```

새 터미널에서 프론트:

```bash
cd SoriSsak-FE
pnpm install
pnpm start            # i: iOS, a: Android, w: Web
```

> 실기기로 테스트할 땐 `localhost` 대신 PC 의 LAN IP 를 써야 한다:
> `SoriSsak-FE/.env` 의 `EXPO_PUBLIC_API_BASE_URL=http://<PC-IP>:8000/api/v1`

---

## 수동 실행 (3개 터미널)

### 1) AI 서버 — :8001

```bash
cd sorisak-ai
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # 서빙엔 fastapi/uvicorn/pydantic/python-dotenv 면 충분
echo "DATA_SOURCE=dummy" > .env
uvicorn main:app --host 127.0.0.1 --port 8001
```

선택: `.env` 에 `OPENAI_API_KEY`(GPT 재정렬·문법보정), `STABILITY_API_KEY`(이미지),
`CLOVA_CLIENT_ID/SECRET`(TTS) 를 넣으면 실제 멀티모달이 켜진다. 없으면 stub 으로 동작.

### 2) Backend — :8000

```bash
cd SoriSsack-Back
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cat > .env <<EOF
DATABASE_URL=sqlite:///./sorissack.db
AI_SERVER_URL=http://127.0.0.1:8001
USE_MOCK_AI=false
EOF
python -m scripts.seed_sample_data
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 3) Frontend

```bash
cd SoriSsak-FE
pnpm install
pnpm start
```

---

## 동작 확인 (curl)

```bash
B=http://127.0.0.1:8000/api/v1
curl -s $B/health
curl -s $B/children/3
curl -s $B/cards/3
curl -s -X POST $B/recommendations -H 'Content-Type: application/json' \
     -d '{"baby_id":3,"selected_baby_card_id":301}'        # → AI 추천 프록시
curl -s -X POST $B/logs -H 'Content-Type: application/json' \
     -d '{"baby_id":3,"baby_card_id":301,"card_id":35,"text_snapshot":"장난감","used_at":"2026-06-04T13:20:00"}'
curl -s -X POST $B/expressions -H 'Content-Type: application/json' \
     -d '{"baby_id":3,"sentence_text":"장난감 사주세요","played_tts":true}'
# 멀티모달(보너스): 단어 배열 → AI 문장보정+이미지+음성
curl -s -X POST $B/expressions/generate -H 'Content-Type: application/json' \
     -d '{"baby_id":3,"words":[{"text":"물","pos":"noun"},{"text":"마시다","pos":"verb"}],"emotion":"happy"}'
```

## 엔드포인트 요약

| Method | URL | 설명 | AI 연동 |
|--------|-----|------|---------|
| GET  | `/api/v1/health` | 헬스 체크 | - |
| GET  | `/api/v1/children/{baby_id}` | 아동 정보 | - |
| GET  | `/api/v1/cards/{baby_id}` | 카드 목록(개인+기본, 카테고리 포함) | - |
| POST | `/api/v1/recommendations` | 단어 추천 | → AI `/recommend` |
| POST | `/api/v1/expressions` | 완성 문장 저장 | - |
| POST | `/api/v1/expressions/generate` | 멀티모달 문장 생성('말하기') | → AI `/sentence` |
| POST | `/api/v1/logs` | 단어 사용 로그 + usage_count 갱신 | - |

## 환경 변수

| 변수 | 위치 | 기본값 | 설명 |
|------|------|--------|------|
| `DATABASE_URL` | Backend | `sqlite:///./sorissack.db` | DB. Postgres 면 `postgresql+psycopg://...` |
| `AI_SERVER_URL` | Backend | `http://127.0.0.1:8001` | AI 서버 주소 |
| `USE_MOCK_AI` | Backend | `true` | `false` 면 실제 AI 호출(이 가이드 기준) |
| `DATA_SOURCE` | AI | `dummy` | `dummy` \| `db` |
| `EXPO_PUBLIC_API_BASE_URL` | FE | `http://localhost:8000/api/v1` | 백엔드 주소 |
| `EXPO_PUBLIC_TEST_BABY_ID` | FE | `3` | 데모 아동 ID |
| `OPENAI_API_KEY` | AI | (없음) | 있으면 GPT 문장 보정/추천 재정렬 |
| `STABILITY_API_KEY` | AI | (없음) | 있으면 Stable Diffusion 이미지 생성 |
| `CLOVA_CLIENT_ID` / `CLOVA_CLIENT_SECRET` | AI | (없음) | 있으면 Clova Voice TTS |
| `AI_PUBLIC_BASE_URL` | AI | `http://127.0.0.1:8001` | 생성 이미지/음성 URL prefix. 실기기 데모 시 LAN IP |

## 멀티모달 '말하기' 흐름 (FE ↔ AI)

FE "말하기" 버튼 → `POST /expressions/generate` → 백엔드 → AI `/sentence`:

1. **문장 보정(GPT)**: 선택 단어 → 자연스러운 문장. (`OPENAI_API_KEY` 없으면 단어 이어붙이기)
2. **이미지(SD)**: 문장 → 그림 URL. (`STABILITY_API_KEY` 없으면 `image_url=null`)
3. **음성(Clova)**: 아동별 voice_profile 반영. (`CLOVA_*` 없으면 `audio_url=null`)
4. 결과는 백엔드가 `sentence_master` 에 저장(`saved=true`).

FE 동작:
- 보정된 **문장**으로 화면 표시 + **기기 TTS(expo-speech)** 로 읽음 → GPT 키를 넣으면
  읽는 문장이 자동으로 자연스러워진다.
- `image_url` 이 오면 **생성 그림을 화면에 표시**(`expo-image`). SD 키를 넣으면 자동 표시.
- 키가 하나도 없어도 현재처럼 정상 동작(문장=단어 나열, 그림 없음).

> 참고: AI 가 만든 Clova `audio_url`(mp3)을 **기기 스피커로 직접 재생**하려면 FE 에
> 오디오 플레이어(`expo-audio`)를 추가해야 한다. 현재는 보정 문장을 기기 TTS 로 읽는다.
> AI 가 반환하는 이미지/음성 URL 은 AI 서버의 `/generated/...` 정적 경로다(이미 서빙 중).
