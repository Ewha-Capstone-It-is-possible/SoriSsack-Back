# SoriSsack Backend Swagger Test / Front API Checklist

## 1. Swagger 테스트 추천 순서

발표나 시연 기준으로는 아래 순서대로 테스트하면 흐름이 가장 자연스럽다.

### 1) 서버 정상 동작 확인
- `GET /api/v1/health`
- 확인 포인트
  - 서버가 정상 실행 중인지
  - 공통 응답 형식 `{ success, data, message }` 가 맞는지

### 2) 보호자 회원가입
- `POST /api/v1/auth/register`
- Body 예시

```json
{
  "baby_id": 3,
  "parent_name": "김보호자",
  "email": "parent@example.com",
  "password": "sorissack123"
}
```

- 확인 포인트
  - `access_token` 이 내려오는지
  - 보호자 정보가 함께 반환되는지

### 3) 보호자 로그인
- `POST /api/v1/auth/login`
- Body 예시

```json
{
  "email": "parent@example.com",
  "password": "sorissack123"
}
```

- 확인 포인트
  - 로그인 성공 응답이 오는지
  - `access_token` 이 재발급되는지

### 4) 아동 정보 확인
- `GET /api/v1/children/{baby_id}`
- 예시
  - `baby_id = 3`
- 확인 포인트
  - 테스트에 사용할 아동이 실제로 존재하는지

### 5) 카드 목록 조회
- `GET /api/v1/cards/{baby_id}`
- 예시
  - `baby_id = 3`
- 확인 포인트
  - 공용 카드 + 아동 맞춤 카드가 같이 내려오는지
  - `baby_card_id`, `card_id`, `text`, `is_favorite`, `category` 필드 확인

### 6) 카테고리 목록 조회
- `GET /api/v1/categories/{baby_id}`
- 확인 포인트
  - 아동별 활성 카테고리가 내려오는지

### 7) 카테고리별 카드 조회
- `GET /api/v1/categories/{baby_id}/{baby_category_id}/cards`
- 확인 포인트
  - 특정 카테고리 안의 카드만 조회되는지

### 8) 추천 API 테스트
- `POST /api/v1/recommendations`
- Body 예시

```json
{
  "baby_id": 3,
  "selected_baby_card_id": 1
}
```

- 또는 공용 카드 기준이면

```json
{
  "baby_id": 3,
  "selected_card_id": 1
}
```

- 확인 포인트
  - 추천 단어 배열이 내려오는지
  - `recommended_words` 안에 `text`, `pos`, `system_score` 가 포함되는지

### 9) 로그 저장 테스트
- `POST /api/v1/logs`
- Body 예시

```json
{
  "baby_id": 3,
  "baby_card_id": 1,
  "card_id": 1,
  "text_snapshot": "사과",
  "context_json": {
    "source": "swagger-test",
    "emotion": "neutral"
  },
  "used_at": "2026-06-18T12:00:00"
}
```

- 확인 포인트
  - 로그가 저장되는지
  - `usage_count` 증가와 리포트 반영 데이터가 쌓이는지

### 10) 문장 저장 테스트
- `POST /api/v1/expressions`
- Body 예시

```json
{
  "baby_id": 3,
  "sentence_text": "사과 주세요.",
  "played_tts": true,
  "avatar_image_url": null,
  "avatar_audio_url": null
}
```

### 11) 멀티모달 문장 생성 테스트
- `POST /api/v1/expressions/generate`
- Body 예시

```json
{
  "baby_id": 3,
  "words": [
    { "text": "사과", "pos": "noun", "baby_card_id": 1 },
    { "text": "주세요", "pos": "verb", "card_id": 4 }
  ],
  "emotion": "happy",
  "save": true
}
```

- 확인 포인트
  - 문장, 이미지, 오디오 응답이 내려오는지
  - `sentence_id` 저장 여부 확인

### 12) 설정 저장 테스트
- `PUT /api/v1/settings/{baby_id}`
- Body 예시

```json
{
  "parent_pin": "1234",
  "tts_voice": "nara",
  "tts_speed": 1.0,
  "reward_enabled": true,
  "communication_level": "beginner",
  "favorite_topics": ["음식", "놀이"],
  "sensory_notes": "밝은 화면 자극에 민감",
  "avatar_name": "소리곰"
}
```

### 13) 설정 조회 테스트
- `GET /api/v1/settings/{baby_id}`

### 14) 부모 PIN 확인 테스트
- `POST /api/v1/auth/verify-pin`
- Body 예시

```json
{
  "baby_id": 3,
  "pin": "1234"
}
```

- 확인 포인트
  - `verified: true` 가 내려오는지

### 15) 마이페이지 요약 조회
- `GET /api/v1/mypage/{baby_id}`
- 확인 포인트
  - 총 카드 수, 즐겨찾기 수, 로그 수, 문장 수가 요약되어 보이는지

### 16) 리포트 조회
- `GET /api/v1/reports/{baby_id}?days=30`
- 확인 포인트
  - `top_words`, `emotion_counts`, `recent_sentences`, `insight` 확인

### 17) 리포트 PDF 다운로드
- `GET /api/v1/reports/{baby_id}/pdf?days=30`
- 확인 포인트
  - PDF 다운로드가 되는지

### 18) 보상 조회
- `GET /api/v1/rewards/{baby_id}`
- 확인 포인트
  - 포인트, 레벨, 배지가 계산되어 내려오는지

### 19) 사용자 카드 생성
- `POST /api/v1/cards`
- Body 예시

```json
{
  "baby_id": 3,
  "text": "포도",
  "part_of_speech": "noun",
  "image_url": null,
  "is_favorite": true,
  "category_name": "음식"
}
```

### 20) 카드 수정
- `PATCH /api/v1/cards/{baby_card_id}`
- Body 예시

```json
{
  "text": "포도 주세요",
  "is_favorite": false,
  "category_name": "간식"
}
```

### 21) 즐겨찾기만 변경
- `PATCH /api/v1/cards/{baby_card_id}/favorite`
- Body 예시

```json
{
  "is_favorite": true
}
```


## 2. 프론트에 넘기면 되는 API 목록

프론트와 연결할 때는 화면 기준으로 아래처럼 넘기면 된다.

### 로그인 / 부모 모드
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/verify-pin`

### 홈 / 시작 화면
- `GET /api/v1/health`
- `GET /api/v1/children/{baby_id}`
- `GET /api/v1/mypage/{baby_id}`

### 카드 메인 화면
- `GET /api/v1/cards/{baby_id}`
- `GET /api/v1/categories/{baby_id}`
- `GET /api/v1/categories/{baby_id}/{baby_category_id}/cards`

### 카드 선택 후 추천 흐름
- `POST /api/v1/recommendations`
- `POST /api/v1/logs`
- `POST /api/v1/expressions/generate`
- `POST /api/v1/expressions`

### 부모 카드 관리 화면
- `POST /api/v1/cards`
- `PATCH /api/v1/cards/{baby_card_id}`
- `PATCH /api/v1/cards/{baby_card_id}/favorite`
- `POST /api/v1/cards/suggest`

### 설정 / 온보딩 / 부모 모드
- `GET /api/v1/settings/{baby_id}`
- `PUT /api/v1/settings/{baby_id}`

### 리포트 / 통계 / PDF
- `GET /api/v1/reports/{baby_id}?days=30`
- `GET /api/v1/reports/{baby_id}/pdf?days=30`

### 보상 / 배지
- `GET /api/v1/rewards/{baby_id}`


## 3. 프론트 연결 우선순위

시간이 부족하면 아래 순서대로 붙이는 게 맞다.

### 1순위
- `POST /auth/login`
- `GET /cards/{baby_id}`
- `POST /recommendations`
- `POST /logs`
- `POST /expressions/generate`

이 5개가 붙으면
`로그인 -> 카드 선택 -> 추천 -> 문장 생성 -> 로그 저장`
핵심 데모가 완성된다.

### 2순위
- `GET /categories/{baby_id}`
- `GET /categories/{baby_id}/{baby_category_id}/cards`
- `GET /mypage/{baby_id}`
- `GET /settings/{baby_id}`
- `PUT /settings/{baby_id}`
- `POST /auth/verify-pin`

이 단계가 붙으면
카테고리 탐색, 마이페이지, 설정 화면, 부모 모드 진입까지 연결된다.

### 3순위
- `GET /reports/{baby_id}`
- `GET /reports/{baby_id}/pdf`
- `GET /rewards/{baby_id}`
- `POST /cards`
- `PATCH /cards/{baby_card_id}`
- `PATCH /cards/{baby_card_id}/favorite`
- `POST /cards/suggest`
- `GET /rewards/{baby_id}`
- `POST /cards`
- `PATCH /cards/{baby_card_id}`

이 단계는 발표에서 “확장 기능”으로 보여주기 좋다.


## 4. 프론트 팀에 같이 전달하면 좋은 말

아래처럼 전달하면 된다.

> 프론트에서는 우선 `cards -> recommendations -> logs -> expressions/generate` 흐름부터 붙이면 핵심 데모가 완성됩니다.  
> 이후 `settings`, `mypage`, `reports`, `rewards`는 추가 화면 단위로 확장 연결하면 됩니다.  
> 모든 응답은 기본적으로 `{ success, data, message }` 구조로 내려갑니다.


## 5. 바로 확인할 것

- Swagger에서 새로 추가된 라우터가 보이는지
  - `settings`
  - `mypage`
  - `reports`
  - `rewards`
- DB에 `baby_app_settings` 테이블이 실제 생성되는지
- 프론트가 기대하는 필드명과 실제 응답 필드명이 맞는지
