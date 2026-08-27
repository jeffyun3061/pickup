# GamePickup 보안 감사 기록

기준일: 2026-08-27

## 서버 런타임

- `pip-audit -r server/requirements.txt --strict` 결과: **No known vulnerabilities found**
- FastAPI `0.141.1` + Starlette `1.3.1`
- `python-multipart 0.0.32`
- `PyJWT 2.13.0` 사용. `python-jose`와 `ecdsa` 의존성은 제거했다.
- CI가 모든 PR/push에서 같은 감사를 실행한다.

## 모바일·관리자 JavaScript

`npm audit --omit=dev --audit-level=high` 결과: **No known vulnerabilities found**.
Expo/RN이 요구하는 Metro 패치 버전(0.84.5)과 `uuid` 11.1.1을 `package.json`
`overrides`와 lockfile에 고정해 CI와 로컬 설치 결과를 일치시켰다. 다음 Expo/RN SDK
업그레이드 때는 override가 여전히 호환되는지 `npm audit`, 전체 테스트, Expo Doctor로
재검증한다.

## 적용된 런타임 방어

- 운영 설정에서 PostgreSQL·비밀값·HTTPS CORS·문의처·푸시·스케줄러를 필수화
- production CORS의 localhost·개발 placeholder와 개인정보처리방침 example 도메인 차단
- production 관리자 비밀번호가 실제 bcrypt 해시 형식인지 시작 시 검증
- 운영 JWT·수집 키는 placeholder를 거부하고 UTF-8 기준 32바이트 이상으로 강제
- API 시작 시 PostgreSQL 일시 연결 실패를 연결 타임아웃과 함께 제한된 횟수로 재시도하고, 실패 시 연결 문자열 없이 오류를 남김
- HTTP 보안 헤더 및 운영 HSTS
- 관리자 same-origin 정적 화면용 Content-Security-Policy
- 운영 환경에서는 관리자·수집 API 구조가 노출되는 Swagger/OpenAPI 문서를 비공개하고,
  개발 환경에서만 `/docs`·`/redoc`·`/openapi.json`을 제공한다
- 공개 API에서 권리 미검증 이미지 URL·원본 출처 URL 제거
- 관리자·수집 입력의 이미지 주소는 HTTP(S) 또는 `/media/`만 허용하고 URL 인증정보를 거부
- 이미지 MIME/매직바이트/5MB 제한
- collector SSRF·robots·redirect·상세 fetch 상한
- 스케줄러 원문 링크 점검도 공개 IP 재검증·redirect 미추적으로 내부망 요청 차단
- 관리자 로그인·설치 발급·문의 rate limit
- 관리자 로그인 성공·콘텐츠/소스 변경·발행·회수·삭제 감사 로그
- Expo 폐기 토큰 자동 삭제 및 일시 오류 재시도
- 푸시 outbox 발송 시 PostgreSQL 행 잠금(`SKIP LOCKED`)으로 동시 실행 중복 발송 방지
- Android 운영 매니페스트는 인터넷·진동·알림에 필요한 권한만 유지하고,
  저장소 읽기/쓰기와 `SYSTEM_ALERT_WINDOW`는 운영 변형에서 제거한다
  (개발 변형의 오버레이 권한은 Metro 개발 도구에만 한정)

## 운영 규칙

보안 패치가 필요한 경우 먼저 `server/requirements.txt`·`package.json`의 호환 범위를
확인하고, 전체 pytest/모바일 검증/Expo Doctor/관리자 빌드를 통과한 뒤 변경한다.
운영 시크릿은 저장소·이슈·채팅에 올리지 않고 Railway/EAS 환경변수에만 둔다.
