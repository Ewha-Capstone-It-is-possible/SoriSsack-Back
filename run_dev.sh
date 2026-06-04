#!/usr/bin/env bash
#
# run_dev.sh — 3-tier 로컬 개발 스택을 한 번에 띄운다.
#
#   AI 추론 서버 (sorisak-ai)   : 127.0.0.1:8001   (DATA_SOURCE=dummy, 외부 키 불필요)
#   Backend API (this repo)     : 127.0.0.1:8000   (USE_MOCK_AI=false → 위 AI 호출)
#   Frontend (SoriSsak-FE)      : Expo, 별도 터미널에서 `pnpm start`
#
# 사용:
#   ./run_dev.sh           # 두 파이썬 서버(AI + Backend) 기동
#   Ctrl-C 로 둘 다 종료
#
# 전제: 형제 디렉터리 구조
#   <parent>/sorisak-ai
#   <parent>/SoriSsack-Back   ← 현재 위치
#   <parent>/SoriSsak-FE
set -euo pipefail

BACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_DIR="$(cd "$BACK_DIR/../sorisak-ai" && pwd)"

# Python 3.11+ 인터프리터 선택 (macOS 기본 python3 가 너무 최신/구버전일 수 있음)
pick_python() {
  for c in python3.11 python3.12 python3; do
    if command -v "$c" >/dev/null 2>&1; then echo "$c"; return; fi
  done
  echo "python3"
}
PY="$(pick_python)"

ensure_venv() {
  local dir="$1"
  if [ ! -d "$dir/.venv" ]; then
    echo "[setup] $dir : .venv 생성 + 의존성 설치"
    "$PY" -m venv "$dir/.venv"
    "$dir/.venv/bin/pip" install -q --upgrade pip
    "$dir/.venv/bin/pip" install -q -r "$dir/requirements.txt"
  fi
}

# --- .env 기본값 보장 ---------------------------------------------------------
[ -f "$AI_DIR/.env" ]   || printf 'DATA_SOURCE=dummy\n' > "$AI_DIR/.env"
[ -f "$BACK_DIR/.env" ] || printf 'DATABASE_URL=sqlite:///./sorissack.db\nAI_SERVER_URL=http://127.0.0.1:8001\nUSE_MOCK_AI=false\n' > "$BACK_DIR/.env"

ensure_venv "$AI_DIR"
ensure_venv "$BACK_DIR"

# --- AI 서버 (8001) ----------------------------------------------------------
echo "[ai] starting on :8001 (dummy mode)"
( cd "$AI_DIR" && .venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001 ) &
AI_PID=$!

# --- Backend (8000) : 시드 후 기동 -------------------------------------------
echo "[backend] seeding demo data (AI dummy 와 동일 ID 미러링)"
( cd "$BACK_DIR" && .venv/bin/python -m scripts.seed_sample_data )
echo "[backend] starting on :8000 (USE_MOCK_AI=false → AI 8001)"
( cd "$BACK_DIR" && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 ) &
BACK_PID=$!

cleanup() { echo; echo "stopping..."; kill "$AI_PID" "$BACK_PID" 2>/dev/null || true; }
trap cleanup INT TERM

cat <<EOF

────────────────────────────────────────────────────────────
  AI       : http://127.0.0.1:8001        (docs: /docs)
  Backend  : http://127.0.0.1:8000        (docs: /docs, api: /api/v1)
  Frontend : 새 터미널에서  cd ../SoriSsak-FE && pnpm start
             (.env 의 EXPO_PUBLIC_API_BASE_URL → http://localhost:8000/api/v1)
  종료     : Ctrl-C
────────────────────────────────────────────────────────────
EOF

wait
