# GamePickup 실서비스 출시 체크리스트

기준: 1인 운영·저비용 MVP를 먼저 출시하고, 사용자가 늘 때만 확장한다.
첫 출시 권장 구조는 Railway의 관리형 PostgreSQL + API 1개 + API 볼륨 1개다.
자동 수집을 켤 때만 collector 1개를 선택적으로 추가한다. 처음부터 ECS/RDS, Redis, CDN을 넣지 않는다.

출시 범위: 모바일 앱과 소식 수집·검수·게시·알림에 집중한다. 고급 운영 대시보드의
통계·시각화·자동화 UX는 앱 출시 후 별도 작업으로 진행한다. 출시 전에는 소식 등록,
검수, 발행, 푸시 확인에 필요한 최소 관리자 기능만 보장한다.

상태 표기: `[x]` 완료 · `[~]` 부분 확인 필요 · `[ ]` 출시 전 필수

## 1. 제품·정책

- [x] 홈(오늘 소식), 이벤트 기간, 내 게임, 통합 소식, 팝업·행사 UX 확정
- [x] 관심 게임 최대 8개 및 읽음/놓친 소식 정책 확정
- [ ] 서비스명·아이콘·마스코트의 상표/사용권 확인
- [ ] 게임별 이름·이미지·배너의 사용 권한과 출처 URL 기록
- [ ] 공식 RSS/API 이용약관, 재배포·캐시·요약 허용 범위 확인
- [ ] 크롤링 소스는 robots.txt와 서비스 약관을 확인하고 허용된 소스만 등록
- [~] 개인정보처리방침(`/privacy`), 이용약관(`/terms`), 문의·삭제 요청 채널 공개 — `PRIVACY_CONTACT_EMAIL` 운영값 입력 필요
- [x] AI 요약은 참고용임을 표시하고 게임명·공식 원문 링크를 항상 제공 (`소식 상세` 하단 안내 + 공식 원문 보기)
- [x] 콘텐츠 삭제/정정 요청 절차와 처리 기한 정의 — `docs/CONTENT_OPERATIONS.md` (실제 문의 이메일은 운영값 입력 필요)

## 2. 콘텐츠 수집·검수

- [x] RSS/JSON API/HTML collector와 조건부 GET·해시 중복 방지
- [x] 수집 실행 이력, source health, 0건 연속 실패 경고
- [x] draft → reviewed → published 상태머신
- [x] 공식 소스 자동 발행과 push outbox
- [x] LLM 요약 실패 시 규칙 기반 폴백과 품질 게이트
- [~] 게임별 실제 공식 소스 1개 이상 등록하고 dry-run 결과 확인 — 자동 수집을 켤 때의 게이트이며, 첫 출시는 관리자 수동 등록으로 진행 가능
- [x] 소스별 허용 필드(제목·요약·이미지·날짜·원문 URL) 문서화 — `docs/INGESTION_DATA_CONTRACT.md`
- [x] 오탐/중복/잘못된 날짜를 검수 큐에서 처리하는 담당자와 주기 지정 — `docs/CONTENT_OPERATIONS.md`의 1인 운영자·매일 09:00 KST 기준
- [x] 소스가 변경될 때 selector/API 버전과 롤백 방법 기록 — `docs/CONTENT_OPERATIONS.md`의 YYYYMMDD-N 버전·직전 설정 보관
- [x] 첫 출시 후 1주일은 자동 발행을 보수적으로 두고 수동 승인 비율 측정 — 무수정 승인 20건·수정/회수 0건 전까지 수동 검수

## 3. 백엔드·보안

- [x] Public/Admin/Ingest 계층 분리
- [x] 관리자 JWT, ingest API key, installation 인증
- [x] 요청 단위 트랜잭션과 PostgreSQL 호환 검증
- [x] DB 연결 타임아웃·API 시작 스키마 초기화 재시도
- [x] 설치 발급·문의 rate limit, 이미지 확장자·크기 제한, 감사 로그
- [x] 공개 API에서 권리 미검증 이미지 URL·원본 출처 URL 차단
- [x] 관리자·수집 이미지 URL 스킴 및 URL 인증정보 검증
- [x] Expo 영구 토큰 오류(`DeviceNotRegistered`·`InvalidDeviceToken`) 자동 정리
- [x] collector 고아 작업 회수 및 지수 백오프 재시도
- [x] X-Content-Type-Options·Frame·Referrer·Permissions 보안 헤더
- [x] 운영 API 문서(Swagger/OpenAPI) 비공개 — 개발 환경에서만 `/docs`·`/openapi.json` 제공
- [x] production 개발용 CORS·문의처 placeholder 차단
- [ ] 운영 환경의 `ENV=production`과 모든 기본 비밀번호 제거
- [ ] `JWT_SECRET`, `INGEST_API_KEY`, 관리자 비밀번호를 비밀 저장소에만 보관
- [ ] CORS를 실제 앱/API 도메인으로 제한하고 관리자 경로에 HTTPS 적용
- [ ] 관리자 계정 2FA 또는 최소한 강한 비밀번호·정기 교체 적용
- [ ] DB 계정은 앱용/마이그레이션용 권한을 분리하고 외부 공개 금지
- [ ] API 응답에 내부 예외·토큰·원문 수집 헤더가 노출되지 않는지 확인
- [x] 삭제·회수·발행·관리자 로그인·수집 소스 변경을 감사 로그에 남김 (통합 테스트 확인)

## 4. 인프라·운영

- [x] API/collector Dockerfile 및 헬스체크
- [x] API 볼륨 `/data` 설계와 `/media` 서빙
- [~] Railway 배포 절차 문서화
- [ ] Railway Postgres 생성 후 자동 백업과 보존 기간 확인
- [ ] DB 백업을 실제로 복원하는 리허설 1회 실행
- [ ] API 서비스 배포 후 `/health/live`와 `/health/ready`가 각각 200인지 확인
- [x] 프로세스 생존 `/health/live`와 DB 연결 포함 `/health/ready` 제공
- [x] 배포 후 공개 API 스모크 명령 (`npm run smoke:api -- <도메인>`)
- [~] collector가 private network로 API에 연결되고 실패 시 재시도하는지 확인 — collector 선택 배포 시 필수, 수동 출시에는 해당 없음
- [ ] 스케줄러가 중복 실행되지 않도록 API/collector 인스턴스를 각각 1개로 고정
- [ ] 로그 보존 기간, 오류 알림, 수집 실패 알림, 비용 알림 설정
- [ ] 이미지 볼륨 용량과 오래된 이미지 정리 정책 설정
- [x] 장애 시 이전 배포로 되돌리는 절차를 README에 기록 — health/smoke 확인·볼륨 보존·스키마 호환성·자동 발행 중지 포함

## 5. 모바일 앱

- [x] Preview/Empty/API CatalogRepository 분리
- [x] 운영 빌드 API 주소 사전검사 (`npm run release:check`)
- [x] 오프라인 캐시·오프라인 배너·당겨서 새로고침
- [x] 알림 탭 딥링크와 cold start
- [x] 최대 8개 게임 선택, 읽음 상태, 이벤트 종료 표시
- [x] 설치별 관심 게임 정규화 저장 및 실제 등록 수 기반 랭킹
- [~] Expo push token은 네이티브 빌드에서 실기기 검증 필요
- [ ] `EXPO_PUBLIC_CATALOG_MODE=api`와 운영 API URL로 빌드 (release 기본값도 api)
- [x] standalone Android release APK/AAB 로컬 패키징·에뮬레이터 기동 확인 (테스트 서명; 스토어 서명은 EAS에서 수행)
- [~] `eas.json` 내부 APK·운영 AAB 프로필과 EAS 환경 고정 — EAS 프로젝트 연결·keystore 생성 필요. Windows 로컬 Gradle은 경로 제한 시 `scripts/android-release.ps1` 사용
- [ ] 내부 테스트 트랙에서 저가형·작은 화면·Android 13/14/15 확인
- [~] 네트워크 끊김, 빈 응답, API 401/429/500, 오래된 앱 버전 화면 확인 — API 오류 계약·오프라인 폴백은 자동 테스트 완료; 실기기 화면과 최소 버전 게이트는 내부 테스트에서 확인 필요
- [ ] 알림 권한 거부·토큰 만료·중복 알림·조용 시간 확인
- [ ] 앱 아이콘, 스플래시, 개인정보 링크, 문의 이메일 확인
- [ ] Play Console Data safety, 콘텐츠 등급, 스토어 설명·스크린샷 작성

## 6. 출시 전 테스트 게이트

- [x] 프론트 `npm run verify` 통과
- [~] Expo Doctor 20/21 통과 및 SDK 57 패치 버전 정렬 — `android/` 네이티브 프로젝트를 Android Studio 소스로 유지하므로 app.json의 Prebuild 동기화 경고 1건은 예상됨. 네이티브 패키지·아이콘·스킴·알림 권한은 `android/`와 릴리스 매니페스트로 별도 검증한다.
- [x] 모바일·관리자 npm 고위험 감사 0건 및 lockfile override 고정
- [x] 백엔드 PostgreSQL pytest 통과 (82개; 임베디드 PostgreSQL)
- [ ] 운영 DB에 마이그레이션을 새 DB에서 0부터 실행
- [ ] 관리자에서 게임 생성 → 이미지 업로드 → 소식 검수 → 발행 → 앱 표시 스모크
- [~] RSS/API/HTML 각각 정상·빈 응답·불완전 행·중복 상황 테스트 — collector 계약 테스트 21개 통과; 실제 운영 소스의 selector/API 변경은 배포 전 dry-run 필요
- [x] 푸시 발송 성공·실패·재시도·조용 시간 테스트 (백엔드 계약; 실기기 푸시는 별도 확인)
- [ ] 원문 링크, 발행 시각, 한국어 줄바꿈, 긴 제목/이미지 비율 확인
- [ ] 삭제/회수된 콘텐츠가 홈·뉴스·캐시에 남지 않는지 확인
- [ ] Android 내부 테스트에서 설치·업데이트·딥링크·백그라운드 복귀 확인

## 7. 출시 당일 순서

1. Railway Postgres와 API를 배포하고 헬스체크를 확인한다.
2. 관리자 계정·비밀값·소스 URL을 운영값으로 입력한다.
3. 자동 수집을 사용할 경우에만 collector를 연결하고 모든 소스를 dry-run한다. 수동 출시라면
   관리자에서 직접 등록하는 경로를 확인한다.
4. 테스트 게임 1개와 테스트 소식 1개로 발행·푸시·앱 표시를 확인한다.
5. 실제 게임 소스는 수동 검수 모드로 시작한다.
6. EAS AAB를 내부 테스트 트랙에 올리고 승인된 테스터에게 배포한다.
7. 오류율·수집 성공률·푸시 성공률·비용을 24시간 관찰한다.
8. 이상이 없을 때만 자동 발행 범위를 단계적으로 넓힌다.

## 8. 출시 후 운영 주기

- 매일: 수집 실패·검수 큐·푸시 실패·비용 확인
- 매주: 소스 변경 여부, 중복률, AI 요약 수정률, 사용자 문의 확인
- 매월: DB 복원 리허설, 관리자 권한 점검, 이미지/로그 정리, 비용 검토
- 장애 시: 자동 발행 중지 → 원인/영향 범위 기록 → 수정/검수 → 재발행

## 현재 가장 먼저 할 일

1. 실제 공식 소스와 이미지 권한을 게임별로 확정한다.
2. Railway에 API/Postgres를 배포하고 운영 헬스체크를 통과시킨다. 자동 수집을 사용할 때만
   collector를 추가 배포한다.
3. 운영 DB에서 수집부터 앱 표시까지 한 번에 스모크 테스트한다.
4. EAS 내부 테스트 빌드를 만들어 실기기 알림과 딥링크를 검증한다.
5. 개인정보·약관·스토어 메타를 준비한 뒤 공개 출시한다.
