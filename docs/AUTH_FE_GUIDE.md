# 프론트 연동 가이드 — 로그인 / 회원가입 / 인증

> Base URL: `http://<서버>/api/v1`  (로컬: `http://localhost:8000/api/v1`, EC2: `http://3.26.181.63:8000/api/v1`)
> 인터랙티브 명세: `http://<서버>/docs` (Swagger, 우측 상단 **Authorize** 로 토큰 테스트 가능)

## ⚠️ 핵심 변경 — 이제 모든 API가 로그인 필수

추천·카드·카테고리·말하기·로그·아동 등 **기존 모든 엔드포인트가 JWT 토큰을 요구**한다.
로그인 후 받은 `access_token` 을 **모든 요청 헤더에 실어야** 한다:

```
Authorization: Bearer <access_token>
```

토큰 없이 호출하면 **401**, 남의 아이 데이터에 접근하면 **403** 이 온다.

---

## 공통 응답 형태

성공: `{ "success": true, "data": <...>, "message": "..." }`
실패: `{ "detail": "에러 메시지" }`  (HTTP 4xx/5xx)

---

## 1. 회원가입  `POST /auth/signup`

회원가입 폼 6필드 그대로. **성공 시 바로 로그인 토큰까지 발급**(→ 온보딩으로 이동).

```jsonc
// 요청
{
  "parent_name": "홍길동",      // 부모이름
  "user_id": "gildong01",       // 아이디
  "password": "secret123",      // 비밀번호 (passwordConfirm 은 프론트에서만 검증)
  "email": "g@example.com",     // 이메일
  "phone_number": "010-1234-5678" // 핸드폰
}
// 응답 data
{ "access_token": "eyJ...", "token_type": "bearer",
  "parent": { "parent_id": 1, "user_id": "gildong01", "parent_name": "홍길동", ... } }
```
- 아이디 중복 시 **409**.

## 2. 아이디 중복확인  `GET /auth/check-id?user_id=gildong01`

"중복 확인" 버튼용. (현재 프론트는 "서버와 연결 안 됨"이라고 떠 있음 → 이걸로 교체)
```jsonc
// 응답 data
{ "user_id": "gildong01", "available": true }   // true = 사용 가능
```

## 3. 로그인  `POST /auth/login`

**지금은 버튼만 누르면 로그인되는데, 실제로 이걸 호출해야 한다.**
```jsonc
// 요청
{ "user_id": "gildong01", "password": "secret123" }
// 응답 data  (회원가입과 동일 구조)
{ "access_token": "eyJ...", "token_type": "bearer", "parent": { ... } }
```
- 아이디/비번 틀리면 **401**.

## 4. 내 정보  `GET /auth/me`  (토큰 필요)
```jsonc
{ "parent_id": 1, "user_id": "gildong01", "parent_name": "홍길동", "email": "...", "phone_number": "...", "provider": "local" }
```

## 5. 카카오 로그인  `POST /auth/kakao`  — ⏳ 준비중

현재 **501** 반환. (백엔드 자리는 만들어둠. 카카오 앱 키 발급 후 활성화 예정)
활성화되면: 프론트가 **카카오 SDK 로 받은 access token** 을 보내고, 백엔드가 토큰을 발급한다.
```jsonc
// (예정) 요청
{ "kakao_access_token": "<카카오 SDK 토큰>" }
```
> 그때 프론트는 카카오 SDK 연동(`@react-native-seoul/kakao-login` 등)이 필요하다.

---

## 6. 아이 등록 (온보딩)  `POST /children`  (토큰 필요)

회원가입 → 온보딩에서 아이를 만든다. (이 아이가 추천/말하기의 `baby_id`)
```jsonc
// 요청
{ "baby_name": "민준", "sex": "M", "birth": "2020-03-15T00:00:00" }
// 응답 data
{ "baby_id": 7, "baby_name": "민준", ... }
```

## 7. 내 아이 목록  `GET /children`  (토큰 필요)
```jsonc
[ { "baby_id": 7, "baby_name": "민준", ... } ]
```

---

## 프론트가 해야 할 일 요약

1. **로그인/회원가입** → `access_token` 받아서 **SecureStore/AsyncStorage 에 저장**
2. axios **인터셉터**로 모든 요청에 `Authorization: Bearer <token>` 자동 첨부
3. **401 응답 시 로그인 화면으로** 리다이렉트(토큰 만료/없음)
4. "중복 확인" 버튼 → `GET /auth/check-id`
5. 온보딩에서 `POST /children` 로 아이 등록 → 받은 `baby_id` 를 추천/말하기에 사용
6. 카카오 버튼은 당분간 비활성 또는 "준비중" (백엔드 501)

> axios 예시
> ```ts
> api.interceptors.request.use(async (config) => {
>   const token = await SecureStore.getItemAsync("access_token");
>   if (token) config.headers.Authorization = `Bearer ${token}`;
>   return config;
> });
> ```

## "Clova 소리 안 남" 관련

음성은 **`POST /expressions/generate`** 응답의 `data.audio.audio_url` 로 온다(백엔드가 AI 서버 경유해 Clova 호출). 프론트는 그 URL 을 `<audio>`/expo-av 로 재생만 하면 된다. **단, 이제 이 호출도 토큰이 필요**하다(위 2번 인터셉터 적용 시 자동 해결). 토큰 없으면 401 이라 음성 자체가 안 온다.
