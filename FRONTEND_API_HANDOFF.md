# SoriSsack Frontend API Handoff

프론트에서 바로 붙일 수 있도록, 현재 백엔드 API를 화면 기준으로 정리한 문서입니다.


## 1. 기본 정보

- Base URL

```txt
http://127.0.0.1:8000/api/v1
```

- Swagger

```txt
http://127.0.0.1:8000/docs
```

- 현재 인증 없음
  - 별도 토큰 없이 바로 호출 가능

- 공통 응답 형식

```json
{
  "success": true,
  "data": {},
  "message": "설명 메시지"
}
```


## 2. 프론트에서 우선 붙이면 되는 핵심 흐름

가장 먼저 붙이면 되는 흐름은 아래 4개입니다.

1. `GET /cards/{baby_id}`
2. `POST /recommendations`
3. `POST /logs`
4. `POST /expressions/generate`

이 4개가 붙으면

`카드 선택 -> 다음 단어 추천 -> 선택 로그 저장 -> 문장/음성 생성`

핵심 데모 흐름이 완성됩니다.


## 3. 화면별 API 정리

### 3-1. 홈 / 시작 화면

#### `GET /children/{baby_id}`

- 용도
  - 아동 기본 정보 조회

- 예시

```txt
GET /children/3
```

- 응답에서 쓰는 필드
  - `data.baby_id`
  - `data.baby_name`
  - `data.sex`
  - `data.birth`


#### `GET /mypage/{baby_id}`

- 용도
  - 홈/마이페이지 요약 데이터

- 예시

```txt
GET /mypage/3
```

- 응답에서 쓰는 필드
  - `data.baby`
  - `data.settings`
  - `data.total_cards`
  - `data.favorite_cards`
  - `data.total_logs`
  - `data.total_sentences`
  - `data.latest_sentence`


### 3-2. 카드 메인 화면

#### `GET /cards/{baby_id}`

- 용도
  - 아동이 사용하는 전체 카드 목록 조회
  - 공용 카드 + 아동 맞춤 카드 포함

- 예시

```txt
GET /cards/3
```

- 응답에서 쓰는 필드
  - `data[].baby_card_id`
  - `data[].card_id`
  - `data[].text`
  - `data[].part_of_speech`
  - `data[].image_url`
  - `data[].is_favorite`
  - `data[].source`
  - `data[].status`
  - `data[].usage_count`
  - `data[].category.name`

- 참고
  - 카드 선택 후 추천 요청에는 `baby_card_id`를 넘기면 됩니다.


#### `GET /categories/{baby_id}`

- 용도
  - 아동별 카테고리 목록 조회

- 예시

```txt
GET /categories/3
```

- 응답에서 쓰는 필드
  - `data[].baby_category_id`
  - `data[].name`
  - `data[].icon_url`
  - `data[].is_favorite`


#### `GET /categories/{baby_id}/{baby_category_id}/cards`

- 용도
  - 특정 카테고리에 속한 카드 조회

- 예시

```txt
GET /categories/3/16/cards
```

- 응답에서 쓰는 필드
  - `data.baby_category_id`
  - `data.category_name`
  - `data.cards[]`


### 3-3. 카드 선택 후 추천 흐름

#### `POST /recommendations`

- 용도
  - 선택한 카드 기준 다음 단어 추천

- 요청 body 예시

```json
{
  "baby_id": 3,
  "selected_baby_card_id": 301
}
```

- 응답에서 쓰는 필드
  - `data.baby_id`
  - `data.selected_word`
  - `data.recommended_words[].baby_card_id`
  - `data.recommended_words[].card_id`
  - `data.recommended_words[].text`
  - `data.recommended_words[].pos`
  - `data.recommended_words[].system_score`

- 참고
  - 현재 mock 추천일 수 있으므로 `selected_word` 값은 고정 문자열처럼 보일 수 있습니다.
  - 프론트에서는 우선 `recommended_words` 배열 중심으로 쓰면 됩니다.


#### `POST /logs`

- 용도
  - 카드 선택 기록 저장
  - 이후 리포트, 통계, 보상 계산에 사용

- 요청 body 예시

```json
{
  "baby_id": 3,
  "baby_card_id": 301,
  "card_id": 35,
  "text_snapshot": "장난감",
  "context_json": {
    "source": "frontend",
    "emotion": "neutral"
  },
  "used_at": "2026-06-18T12:00:00"
}
```

- 응답에서 쓰는 필드
  - `data.log_id`
  - `data.baby_id`
  - `data.baby_card_id`
  - `data.card_id`
  - `data.text_snapshot`

- 권장 호출 시점
  - 사용자가 카드를 실제로 선택했을 때 바로 저장


### 3-4. 말하기 / 문장 생성 화면

#### `POST /expressions/generate`

- 용도
  - 선택 단어 배열을 기반으로 문장 + 이미지 + 음성 생성

- 요청 body 예시

```json
{
  "baby_id": 3,
  "words": [
    { "text": "장난감", "pos": "noun", "baby_card_id": 301 },
    { "text": "주세요", "pos": "verb", "card_id": 28 }
  ],
  "emotion": "happy",
  "save": true
}
```

- 응답에서 쓰는 필드
  - `data.sentence`
  - `data.image.image_url`
  - `data.audio.audio_url`
  - `data.avatar.emotion`
  - `data.saved`
  - `data.sentence_id`

- 참고
  - `save: true` 이면 생성 결과가 DB에 저장됩니다.


#### `POST /expressions`

- 용도
  - 이미 만들어진 문장을 별도로 저장할 때 사용

- 요청 body 예시

```json
{
  "baby_id": 3,
  "sentence_text": "장난감 주세요.",
  "played_tts": true,
  "avatar_image_url": null,
  "avatar_audio_url": null
}
```


### 3-5. 부모 카드 관리 화면

#### `POST /cards`

- 용도
  - 사용자 정의 카드 추가

- 요청 body 예시

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

- 응답에서 쓰는 필드
  - `data.baby_card_id`
  - `data.text`
  - `data.category`


#### `PATCH /cards/{baby_card_id}`

- 용도
  - 카드 수정

- 예시

```txt
PATCH /cards/301
```

- 요청 body 예시

```json
{
  "text": "장난감 주세요",
  "is_favorite": true,
  "category_name": "놀이"
}
```


#### `PATCH /cards/{baby_card_id}/favorite`

- 용도
  - 즐겨찾기 토글

- 예시

```txt
PATCH /cards/301/favorite
```

- 요청 body 예시

```json
{
  "is_favorite": false
}
```


#### `POST /cards/suggest`

- 용도
  - 부모가 새 카드를 추가할 때 관련 단어 추천

- 요청 body 예시

```json
{
  "text": "과일",
  "baby_id": 3,
  "count": 6
}
```

- 응답에서 쓰는 필드
  - `data.text`
  - `data.suggestions[].text`
  - `data.suggestions[].pos`


### 3-6. 설정 화면

#### `GET /settings/{baby_id}`

- 용도
  - 설정 화면 초기값 조회

- 예시

```txt
GET /settings/3
```

- 응답에서 쓰는 필드
  - `data.parent_pin_enabled`
  - `data.tts_voice`
  - `data.tts_speed`
  - `data.reward_enabled`
  - `data.communication_level`
  - `data.favorite_topics`
  - `data.sensory_notes`
  - `data.avatar_name`


#### `PUT /settings/{baby_id}`

- 용도
  - 설정 저장

- 요청 body 예시

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


### 3-7. 리포트 / 통계 화면

#### `GET /reports/{baby_id}?days=30`

- 용도
  - 로그 기반 리포트 조회

- 예시

```txt
GET /reports/3?days=30
```

- 응답에서 쓰는 필드
  - `data.total_selections`
  - `data.unique_words`
  - `data.total_sentences`
  - `data.average_sentence_length`
  - `data.top_words`
  - `data.emotion_counts`
  - `data.recent_sentences`
  - `data.insight`


#### `GET /reports/{baby_id}/pdf?days=30`

- 용도
  - 리포트 PDF 다운로드

- 예시

```txt
GET /reports/3/pdf?days=30
```

- 참고
  - 브라우저 다운로드 또는 파일 저장 용도로 사용


### 3-8. 보상 / 배지 화면

#### `GET /rewards/{baby_id}`

- 용도
  - 포인트, 레벨, 배지 조회

- 예시

```txt
GET /rewards/3
```

- 응답에서 쓰는 필드
  - `data.reward_enabled`
  - `data.points`
  - `data.level`
  - `data.badges[].key`
  - `data.badges[].title`
  - `data.badges[].earned`
  - `data.badges[].description`


## 4. 프론트 연결 추천 순서

### 1순위

- `GET /cards/{baby_id}`
- `POST /recommendations`
- `POST /logs`
- `POST /expressions/generate`

이 단계가 붙으면 메인 사용자 흐름이 완성됩니다.


### 2순위

- `GET /categories/{baby_id}`
- `GET /categories/{baby_id}/{baby_category_id}/cards`
- `GET /mypage/{baby_id}`
- `GET /settings/{baby_id}`
- `PUT /settings/{baby_id}`

이 단계가 붙으면 화면 구성이 훨씬 안정됩니다.


### 3순위

- `GET /reports/{baby_id}`
- `GET /reports/{baby_id}/pdf`
- `GET /rewards/{baby_id}`
- `POST /cards`
- `PATCH /cards/{baby_card_id}`
- `PATCH /cards/{baby_card_id}/favorite`
- `POST /cards/suggest`

이 단계는 부모 기능/확장 기능입니다.


## 5. 프론트에서 주의할 점

- 모든 응답은 `data` 안쪽을 실제 payload로 보면 됩니다.
- 현재 인증이 없으므로 바로 호출 가능합니다.
- 추천 API는 mock 결과일 수 있으니, 우선 `recommended_words` 배열 기준으로 UI를 붙이면 됩니다.
- `cards` 조회 결과의 `baby_card_id`는 이후 추천, 로그 저장, 카드 수정에 계속 사용됩니다.
- `reports`, `rewards`는 `logs` 데이터가 있어야 값이 자연스럽게 보입니다.


## 6. 빠른 테스트용 실제 값

현재 로컬 테스트 기준 예시:

- `baby_id = 3`
- 카드 예시
  - `baby_card_id = 301`
  - `card_id = 35`
  - `text = "장난감"`

추천 테스트 예시:

```json
{
  "baby_id": 3,
  "selected_baby_card_id": 301
}
```

로그 저장 테스트 예시:

```json
{
  "baby_id": 3,
  "baby_card_id": 301,
  "card_id": 35,
  "text_snapshot": "장난감",
  "context_json": {
    "source": "frontend",
    "emotion": "neutral"
  },
  "used_at": "2026-06-18T12:00:00"
}
```


## 7. 프론트 팀에게 바로 전달할 한 줄 요약

우선 `cards -> recommendations -> logs -> expressions/generate` 순으로 붙이면 핵심 데모가 완성되고, 그다음 `mypage`, `settings`, `reports`, `rewards`를 화면 단위로 확장하면 됩니다.
