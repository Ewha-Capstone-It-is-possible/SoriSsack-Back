# 소리싹 Backend API 명세서

> **Base URL**: `http://localhost:8000/api/v1`
> **Version**: 1.0.0
> **Last Updated**: 2026-04-17

---

## 목차

1. [공통 응답 형식](#공통-응답-형식)
2. [헬스 체크](#1-헬스-체크)
3. [아동 정보 조회](#2-아동-정보-조회)
4. [카드 목록 조회](#3-카드-목록-조회)
5. [단어 추천](#4-단어-추천)
6. [문장 표현 저장](#5-문장-표현-저장)
7. [단어 사용 로그 저장](#6-단어-사용-로그-저장)
8. [에러 응답](#에러-응답)

---

## 공통 응답 형식

모든 API는 동일한 래퍼 구조로 응답합니다.

### 성공 시

```json
{
  "success": true,
  "data": { ... },
  "message": "설명 메시지"
}
```

### 실패 시

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 설명"
  }
}
```

---

## 1. 헬스 체크

서버 상태 확인

| 항목 | 값 |
|------|------|
| **Method** | `GET` |
| **URL** | `/api/v1/health` |

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

아동의 기본 정보를 조회합니다.

| 항목 | 값 |
|------|------|
| **Method** | `GET` |
| **URL** | `/api/v1/children/{baby_id}` |

### Path Parameters

| 필드 | 타입 | 설명 |
|------|------|------|
| `baby_id` | `int` | 아동 ID |

### Response

```json
{
  "success": true,
  "data": {
    "baby_id": 3,
    "baby_name": "민준",
    "sex": "M",
    "birth": "2022-06-15T00:00:00",
    "created_at": "2026-01-10T09:00:00+09:00",
    "updated_at": "2026-04-01T14:30:00+09:00"
  },
  "message": "아동 정보를 조회했습니다."
}
```

### Response 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `baby_id` | `int` | 아동 ID |
| `baby_name` | `string` | 아동 이름 |
| `sex` | `string` | 성별 (`"M"` / `"F"`) |
| `birth` | `datetime` | 생년월일 |
| `created_at` | `datetime` | 생성일시 |
| `updated_at` | `datetime` | 수정일시 |

---

## 3. 카드 목록 조회

아동의 전체 카드 목록을 조회합니다. (개인 카드 + 기본 카드)

| 항목 | 값 |
|------|------|
| **Method** | `GET` |
| **URL** | `/api/v1/cards/{baby_id}` |

### Path Parameters

| 필드 | 타입 | 설명 |
|------|------|------|
| `baby_id` | `int` | 아동 ID |

### Response

```json
{
  "success": true,
  "data": [
    {
      "baby_card_id": 501,
      "card_id": 10,
      "text": "물",
      "part_of_speech": "noun",
      "image_url": "https://example.com/images/water.png",
      "is_favorite": true,
      "source": "system_default",
      "status": "active",
      "usage_count": 15
    },
    {
      "baby_card_id": 502,
      "card_id": null,
      "text": "엄마가 만든 카드",
      "part_of_speech": "noun",
      "image_url": "https://example.com/images/custom.png",
      "is_favorite": false,
      "source": "parent_custom",
      "status": "active",
      "usage_count": 3
    },
    {
      "baby_card_id": null,
      "card_id": 36,
      "text": "블록",
      "part_of_speech": "noun",
      "image_url": "https://example.com/images/block.png",
      "is_favorite": false,
      "source": "system_default",
      "status": "default",
      "usage_count": 0
    }
  ],
  "message": "카드 목록을 조회했습니다."
}
```

### Response 필드 (`data[]` 각 항목)

| 필드 | 타입 | 설명 |
|------|------|------|
| `baby_card_id` | `int \| null` | 아동 개인 카드 ID. `null`이면 아직 할당 안 된 기본 카드 |
| `card_id` | `int \| null` | 기본 카드 ID. `null`이면 부모가 만든 커스텀 카드 |
| `text` | `string` | 카드에 표시할 단어 |
| `part_of_speech` | `string \| null` | 품사 (`"noun"`, `"verb"`, `"adjective"`) |
| `image_url` | `string \| null` | 카드 이미지 URL |
| `is_favorite` | `boolean` | 즐겨찾기 여부 |
| `source` | `string` | 카드 출처 (`"system_default"`, `"parent_custom"`) |
| `status` | `string` | 상태 (`"active"`, `"default"`, `"off"`) |
| `usage_count` | `int` | 사용 횟수 |

### 카드 타입 판별

| `baby_card_id` | `card_id` | 의미 |
|---|---|------|
| 값 있음 | 값 있음 | 아동에게 할당된 기본 카드 |
| 값 있음 | `null` | 부모가 직접 추가한 커스텀 카드 |
| `null` | 값 있음 | 아직 할당 안 된 기본 카드 |

---

## 4. 단어 추천

AI 기반으로 다음에 추천할 단어 목록을 반환합니다.

| 항목 | 값 |
|------|------|
| **Method** | `POST` |
| **URL** | `/api/v1/recommendations` |
| **Content-Type** | `application/json` |

### Request Body

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `baby_id` | `int` | O | 아동 ID |
| `selected_baby_card_id` | `int \| null` | X | 방금 선택한 카드 ID. 첫 진입이면 `null` 또는 생략 |

### Request 예시

```json
{
  "baby_id": 3,
  "selected_baby_card_id": 501
}
```

첫 진입 시:
```json
{
  "baby_id": 3
}
```

### Response

```json
{
  "success": true,
  "data": {
    "baby_id": 3,
    "selected_word": "장난감",
    "recommended_words": [
      {
        "baby_card_id": 302,
        "card_id": 40,
        "text": "사주세요",
        "pos": "verb",
        "system_score": 1.63
      },
      {
        "baby_card_id": 303,
        "card_id": 41,
        "text": "갖고싶어요",
        "pos": "adjective",
        "system_score": 1.57
      },
      {
        "baby_card_id": null,
        "card_id": 36,
        "text": "블록",
        "pos": "noun",
        "system_score": 0.50
      }
    ]
  },
  "message": "추천 단어를 조회했습니다."
}
```

### Response 필드 (`data`)

| 필드 | 타입 | 설명 |
|------|------|------|
| `baby_id` | `int` | 아동 ID |
| `selected_word` | `string \| null` | 선택한 카드의 텍스트. 첫 진입이면 `null` |
| `recommended_words` | `array` | 추천 단어 목록 (점수 내림차순, 최대 5개) |

### `recommended_words[]` 각 항목

| 필드 | 타입 | 설명 |
|------|------|------|
| `baby_card_id` | `int \| null` | 아동 카드 ID. `null`이면 기본 카드에서 추천 |
| `card_id` | `int \| null` | 기본 카드 ID. `null`이면 커스텀 카드 |
| `text` | `string` | 추천 단어 텍스트 |
| `pos` | `string \| null` | 품사 (`"noun"`, `"verb"`, `"adjective"`) |
| `system_score` | `float` | AI 추천 점수 (높을수록 추천도 높음) |

---

## 5. 문장 표현 저장

아동이 만든 문장 표현을 저장합니다.

| 항목 | 값 |
|------|------|
| **Method** | `POST` |
| **URL** | `/api/v1/expressions` |
| **Content-Type** | `application/json` |

### Request Body

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `baby_id` | `int` | O | 아동 ID |
| `sentence_text` | `string` | O | 생성된 문장 텍스트 (1자 이상) |
| `played_tts` | `boolean` | X | TTS 재생 여부 (기본: `false`) |
| `avatar_image_url` | `string \| null` | X | 아바타 이미지 URL |
| `avatar_audio_url` | `string \| null` | X | 아바타 오디오 URL |

### Request 예시

```json
{
  "baby_id": 3,
  "sentence_text": "물 주세요",
  "played_tts": true,
  "avatar_image_url": "https://example.com/avatar/img_001.png",
  "avatar_audio_url": "https://example.com/avatar/audio_001.mp3"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "sentence_id": 42,
    "baby_id": 3,
    "sentence_text": "물 주세요",
    "played_tts": true,
    "avatar_image_url": "https://example.com/avatar/img_001.png",
    "avatar_audio_url": "https://example.com/avatar/audio_001.mp3",
    "created_at": "2026-04-17T14:30:00+09:00"
  },
  "message": "문장 생성 결과를 저장했습니다."
}
```

---

## 6. 단어 사용 로그 저장

아동이 카드를 사용(선택)한 기록을 저장합니다. 해당 카드의 `usage_count`와 `last_used_at`도 자동 업데이트됩니다.

| 항목 | 값 |
|------|------|
| **Method** | `POST` |
| **URL** | `/api/v1/logs` |
| **Content-Type** | `application/json` |

### Request Body

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `baby_id` | `int` | O | 아동 ID |
| `baby_card_id` | `int \| null` | X | 사용한 아동 카드 ID |
| `card_id` | `int \| null` | X | 기본 카드 ID |
| `text_snapshot` | `string` | O | 사용 시점의 카드 텍스트 (1자 이상) |
| `context_json` | `object \| null` | X | 사용 컨텍스트 (자유 형식 JSON) |
| `used_at` | `datetime` | O | 사용 시각 (ISO 8601) |

### Request 예시

```json
{
  "baby_id": 3,
  "baby_card_id": 501,
  "card_id": 10,
  "text_snapshot": "물",
  "context_json": {
    "session_id": "abc-123",
    "screen": "word_board"
  },
  "used_at": "2026-04-17T14:25:00+09:00"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "log_id": 1234,
    "baby_id": 3,
    "baby_card_id": 501,
    "card_id": 10,
    "text_snapshot": "물",
    "context_json": {
      "session_id": "abc-123",
      "screen": "word_board"
    },
    "used_at": "2026-04-17T14:25:00+09:00",
    "created_at": "2026-04-17T14:25:01+09:00"
  },
  "message": "단어 사용 로그를 저장했습니다."
}
```

---

## 에러 응답

### 404 Not Found

존재하지 않는 리소스 요청 시

```json
{
  "detail": "아동 정보를 찾을 수 없습니다."
}
```

```json
{
  "detail": "선택한 아동 카드를 찾을 수 없습니다."
}
```

### 422 Unprocessable Entity

요청 데이터 타입/형식 오류 시

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "baby_id"],
      "msg": "Field required"
    }
  ]
}
```

---

## 전체 API 요약

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/api/v1/health` | 서버 상태 확인 |
| `GET` | `/api/v1/children/{baby_id}` | 아동 정보 조회 |
| `GET` | `/api/v1/cards/{baby_id}` | 카드 목록 조회 |
| `POST` | `/api/v1/recommendations` | AI 단어 추천 |
| `POST` | `/api/v1/expressions` | 문장 표현 저장 |
| `POST` | `/api/v1/logs` | 단어 사용 로그 저장 |

---

## 시스템 구조 참고

```
[Frontend] → [Backend API] → [AI Server]
                 ↕
              [PostgreSQL]
```

- 프론트엔드는 이 Backend API만 호출하면 됩니다.
- 단어 추천(`/recommendations`) 호출 시, Backend가 내부적으로 AI 서버를 호출합니다.
- 프론트에서 AI 서버를 직접 호출할 필요 없습니다.
