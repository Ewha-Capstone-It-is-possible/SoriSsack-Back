# 소리싹 Frontend 연동용 API 명세서

> 현재 백엔드 코드 기준으로 **바로 호출 가능한 API만** 정리한 문서입니다.
> Base URL: `http://localhost:8000/api/v1`

---

## 공통 응답 형식

모든 성공 응답은 아래 래퍼 구조를 사용합니다.

```json
{
  "success": true,
  "data": {},
  "message": "설명 메시지"
}
```

에러 응답은 FastAPI 기본 에러 형식을 따릅니다.

```json
{
  "detail": "에러 메시지"
}
```

---

## 1. 서버 상태 확인

### `GET /health`

서버가 정상 동작 중인지 확인합니다.

### Response

```json
{
  "success": true,
  "data": {
    "status": "ok"
  },
  "message": "서버가 정상 동작 중입니다."
}
```

---

## 2. 아동 정보 조회

### `GET /children/{baby_id}`

아동 1명의 기본 정보를 조회합니다.

### Path Parameter

| 필드 | 타입 | 설명 |
|------|------|------|
| `baby_id` | `number` | 아동 ID |

### Response

```json
{
  "success": true,
  "data": {
    "baby_id": 3,
    "baby_name": "민준",
    "sex": "M",
    "birth": "2022-06-15T00:00:00",
    "created_at": "2026-05-10T09:00:00",
    "updated_at": "2026-05-10T09:00:00"
  },
  "message": "아동 정보를 조회했습니다."
}
```

### Front 사용 포인트

- 메인 진입 시 아동 이름, 기본 프로필 표시용
- 현재 구현 기준으로 `age`, `development_stage`는 내려오지 않음

---

## 3. 카드 목록 조회

### `GET /cards/{baby_id}`

아동에게 할당된 개인 카드와 아직 할당되지 않은 기본 카드를 함께 조회합니다.

### Path Parameter

| 필드 | 타입 | 설명 |
|------|------|------|
| `baby_id` | `number` | 아동 ID |

### Response

```json
{
  "success": true,
  "data": [
    {
      "baby_card_id": 101,
      "card_id": 36,
      "text": "블록",
      "part_of_speech": "noun",
      "image_url": "https://example.com/images/block.png",
      "is_favorite": false,
      "source": "system_default",
      "status": "default",
      "usage_count": 0,
      "category": {
        "baby_category_id": 12,
        "category_id": 7,
        "name": "놀이",
        "icon_url": "https://example.com/icons/play.png"
      }
    },
    {
      "baby_card_id": null,
      "card_id": 42,
      "text": "물",
      "part_of_speech": "noun",
      "image_url": "https://example.com/images/water.png",
      "is_favorite": false,
      "source": "system_default",
      "status": "default",
      "usage_count": 0,
      "category": {
        "baby_category_id": 21,
        "category_id": 3,
        "name": "음식/음료",
        "icon_url": "https://example.com/icons/food.png"
      }
    }
  ],
  "message": "카드 목록을 조회했습니다."
}
```

### 카드 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `baby_card_id` | `number \| null` | 아동 개인 카드 ID |
| `card_id` | `number \| null` | 공용 카드 ID |
| `text` | `string` | 화면에 표시할 단어 |
| `part_of_speech` | `string \| null` | 품사 (`noun`, `verb`, `adjective`) |
| `image_url` | `string \| null` | 카드 이미지 URL |
| `is_favorite` | `boolean` | 즐겨찾기 여부 |
| `source` | `string` | 카드 생성 출처 |
| `status` | `string` | 카드 상태 |
| `usage_count` | `number` | 사용 횟수 |
| `category` | `object \| null` | 카드가 속한 카테고리 |

### category 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `baby_category_id` | `number \| null` | 아동별 카테고리 ID |
| `category_id` | `number \| null` | 공용 카테고리 ID |
| `name` | `string` | 카테고리명 |
| `icon_url` | `string \| null` | 카테고리 아이콘 |

### Front 사용 포인트

- `category.name` 기준으로 카드 그룹핑 가능
- `baby_card_id`는 추천 요청/로그 저장 시 사용
- `baby_card_id === null` 인 카드는 아직 개인 카드가 아닌 기본 카드로 해석

---

## 4. 추천 단어 조회

### `POST /recommendations`

선택한 카드 기준으로 다음 추천 단어를 조회합니다.

### Request Body

```json
{
  "baby_id": 3,
  "selected_baby_card_id": 101
}
```

### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `baby_id` | `number` | O | 아동 ID |
| `selected_baby_card_id` | `number \| null` | X | 선택한 개인 카드 ID |

### Response

```json
{
  "success": true,
  "data": {
    "baby_id": 3,
    "selected_word": "블록",
    "recommended_words": [
      {
        "baby_card_id": 205,
        "card_id": 51,
        "text": "주세요",
        "pos": "verb",
        "system_score": 0.95
      },
      {
        "baby_card_id": null,
        "card_id": 63,
        "text": "좋아요",
        "pos": "adjective",
        "system_score": 0.88
      }
    ]
  },
  "message": "추천 단어를 조회했습니다."
}
```

### Front 사용 포인트

- 추천 요청은 **반드시 `baby_card_id` 기준**으로 보내는 것이 안전함
- `recommended_words` 응답에는 현재 `category`, `image_url`가 포함되지 않음
- 추천 단어를 카드처럼 렌더링하려면 필요 시 `/cards/{baby_id}` 응답과 매핑 필요

---

## 5. 문장 생성 결과 저장

### `POST /expressions`

완성된 문장을 저장합니다.

### Request Body

```json
{
  "baby_id": 3,
  "sentence_text": "블록 주세요",
  "played_tts": true,
  "avatar_image_url": "https://example.com/avatar/result.png",
  "avatar_audio_url": "https://example.com/audio/result.mp3"
}
```

### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `baby_id` | `number` | O | 아동 ID |
| `sentence_text` | `string` | O | 최종 문장 |
| `played_tts` | `boolean` | O | TTS 재생 여부 |
| `avatar_image_url` | `string \| null` | X | 생성 이미지 URL |
| `avatar_audio_url` | `string \| null` | X | 생성 음성 URL |

### Response

```json
{
  "success": true,
  "data": {
    "sentence_id": 77,
    "baby_id": 3,
    "sentence_text": "블록 주세요",
    "played_tts": true,
    "avatar_image_url": "https://example.com/avatar/result.png",
    "avatar_audio_url": "https://example.com/audio/result.mp3",
    "created_at": "2026-05-14T13:30:00"
  },
  "message": "문장 생성 결과를 저장했습니다."
}
```

---

## 6. 단어 사용 로그 저장

### `POST /logs`

아동이 카드를 선택한 이벤트를 저장합니다.

### Request Body

```json
{
  "baby_id": 3,
  "baby_card_id": 101,
  "card_id": 36,
  "text_snapshot": "블록",
  "context_json": {
    "screen": "child-home",
    "category": "놀이"
  },
  "used_at": "2026-05-14T13:20:00"
}
```

### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `baby_id` | `number` | O | 아동 ID |
| `baby_card_id` | `number \| null` | X | 선택한 개인 카드 ID |
| `card_id` | `number \| null` | X | 공용 카드 ID |
| `text_snapshot` | `string` | O | 선택 당시 단어 텍스트 |
| `context_json` | `object \| null` | X | 화면/카테고리 등 부가 정보 |
| `used_at` | `datetime` | O | 선택 시각 |

### Response

```json
{
  "success": true,
  "data": {
    "log_id": 501,
    "baby_id": 3,
    "baby_card_id": 101,
    "card_id": 36,
    "text_snapshot": "블록",
    "context_json": {
      "screen": "child-home",
      "category": "놀이"
    },
    "used_at": "2026-05-14T13:20:00",
    "created_at": "2026-05-14T13:20:01"
  },
  "message": "단어 사용 로그를 저장했습니다."
}
```

---

## 프론트 연동 순서 추천

### 초기 진입

1. `GET /health`
2. `GET /children/{baby_id}`
3. `GET /cards/{baby_id}`

### 카드 선택 시

1. `POST /logs`
2. `POST /recommendations`

### 문장 완성 시

1. `POST /expressions`

---

## 주의사항

- 현재 백엔드는 **성공 응답만 공통 래퍼 형식**을 사용합니다.
- 에러 응답은 FastAPI 기본 형식(`detail`)입니다.
- 추천 API는 AI 서버 연동 여부에 따라 응답이 달라질 수 있습니다.
- 추천 API 입력에는 `baby_card_id`가 필요하므로, 프론트는 카드 목록 조회 결과를 먼저 보관해야 합니다.
