# 진행 현황 · 출시 체크리스트

작업 루트: `C:\Users\user\Projects\pickup`  
기준일: 2026-08-27

범례: `[x]` 완료 · `[~]` 부분 · `[ ]` 미착수

---

## 1. 모바일 앱 (Expo)

| 항목 | 상태 | 비고 |
|------|------|------|
| Neon-Tactical UI + PIKY 헤더/탭 | [x] | 5탭 |
| Preview / Empty / Api 카탈로그 | [x] | |
| 공개 게임 후보 카탈로그 | [x] | 붕괴: 스타레일·원신 포함 12종, 권리 검토 보류 2종은 공개 목록에서 제외 |
| 마이픽 · 온보딩 · 문의하기 | [x] | |
| 마이픽 4칸 폼 유지·상단 `+` 추가 | [x] | 0개는 4개 추가 슬롯, 1~3개는 남은 슬롯 유지, 최대 8개·4개씩 페이지·삭제 후 페이지 위치 보정 |
| SecureStore credential + 서버 등록 | [x] | `ensureInstallation` |
| Preference 서버 동기 | [x] | 알림 3종 + gameIds; 업데이트·인게임 이벤트 게시 알림과 종료 리마인더 토글 분리 |
| 알림 설정 UX·문구 통일 | [x] | 내부 설계 설명·게임별 토글·모바일 관리자 링크 제거; 내 게임 새 소식·이벤트 마감 알림·피키 공지만 노출. 개발용 미리보기 공지는 운영 화면에 표시하지 않음 |
| 관심 게임 정규화 저장·실제 등록 수 랭킹 | [x] | `installation_games` + 활성 설치 distinct count, 비활성 게임 선택 자동 제거 |
| Device token 등록 | [~] | Expo push token (`getExpoPushTokenAsync`, 네이티브 빌드 필요) |
| 알림 탭 딥링크 + cold start | [x] | `setupNotificationNavigation` → content/[id] |
| 카탈로그 오프라인 캐시 + 오프라인 배너 | [x] | AsyncStorage 스냅샷, 실패 시 폴백 |
| 앱 데이터 초기화 범위 | [x] | 설치 해지·관심 게임·알림·읽음·북마크·오프라인 캐시 삭제 |
| API 모드 운영 URL·카탈로그 모드 방어 | [x] | 릴리스에서 localhost fallback 차단, 잘못된 모드는 fail-fast |
| 비활성 게임 공개 피드 차단 | [x] | 관리자 기록은 보존하고 Public 소식·마이픽 조회에서 비활성 게임을 제외 |
| EAS 운영 빌드 환경 검사 | [x] | `eas-build-pre-install`에서 API 모드·HTTPS·placeholder 호스트 검증, `npm run test:release` 계약 테스트 |
| 공개 소식 응답 상한 | [x] | 기본 100건·최대 200건으로 장기 운영 시 응답 폭증 방지 |
| 당겨서 새로고침 (홈·뉴스·랭킹) | [x] | 오프라인 캐시 배너와 재시도 포함 |
| 뉴스 검색·종류 칩·보관함(북마크)·읽음 표시 | [x] | 로컬 저장 (`idSetStore`) |
| 이벤트 기간 D-day + 상세 일정/장소/예약 + 공유 | [x] | 새 소식 상세에는 D-day를 노출하지 않음 |
| 마이픽 0개 시 인기 게임 원탭 추가 | [x] | |
| 최소 버전 게이트 (`/meta`) | [x] | `MIN_APP_VERSION` 비우면 비활성 |
| 실기기 API 모드 검증 | [~] | |
| Android 디버그 APK·에뮬레이터 화면 검증 | [x] | x86_64 APK 설치 후 홈·오늘 소식·하단 탭 렌더링 확인, IPv4 우선 LAN Metro 실행과 Fast Refresh 확인 |
| 폭별 2×2 마이픽 레이아웃 | [x] | `resolvePickGrid`가 360/393/412dp 폭에 맞춰 카드 높이를 계산하고 짧은 화면은 세로 스크롤로 보완; Android API 37 에뮬레이터에서 최신 UI 확인 |
| 폰트 로딩 장애 보호 | [x] | 사용자 정의 폰트가 8초 안에 준비되지 않아도 시스템 폴백으로 진입; 폰트 하나 때문에 스플래시가 무한히 남지 않음 |
| 선택창 이미지 로딩 폴백·운영 키 검증 | [x] | 디코딩 중 게임 이니셜을 먼저 표시하고, API의 알 수 없는 번들 키는 안전한 기본 이미지로 대체 |
| Android 릴리스 빌드 / Play 등록 | [~] | 현재 소스 기준 debug APK를 새로 빌드해 에뮬레이터에서 온보딩 8개 선택·마이픽 `8/8 GAMES`·홈/탭 렌더링을 확인했다. Windows에서도 `scripts/android-release.ps1`의 Android Studio JBR/SDK 자동 탐지·기존 `P:` 재사용 후 임시 release 키로 `assembleRelease`와 `bundleRelease`를 성공시켰고, APK/AAB 서명을 별도 인증서로 확인했다. Play용 최종 서명은 EAS 원격 credentials 연결과 스토어 작업이 남았다. |

## 2. 백엔드 API (`server/`)

| 항목 | 상태 | 비고 |
|------|------|------|
| 계층 + 상태머신 + Admin/Ingest/Public | [x] | |
| 요청 단위 트랜잭션 (flush/commit) | [x] | |
| Installation 발급·인증 | [x] | ADR-010 |
| Device token / preferences | [x] | |
| Publish → push outbox enqueue | [x] | 업데이트·인게임 이벤트만 같은 게임별로 묶어 `피키의 새로운 소식 ~♬` 공통 제목으로 발송; 팝업·굿즈는 푸시 제외; PostgreSQL `FOR UPDATE SKIP LOCKED`로 중복 처리 방지 |
| Outbox dispatch | [x] | `POST /admin/push/dispatch` (개발은 스텁, 운영은 Expo Push API) |
| pytest (권한 부정 + 푸시 플로우) | [x] | |
| 수집 소스·실행 이력·작업 API | [x] | RSS/API/HTML, draft-only |
| 별도 collector 실행기 | [x] | RSS + JSON API + HTML 크롤 (ADR-012) |
| 출처별 공통 수집 계약·멱등 키 | [x] | `CollectedItem` 정규화, 서버 저장 시 `source_id` 스코프 적용, 빈/불완전 응답 테스트 21개 |
| 변화 감지 (조건부 GET·해시·멱등 키) | [x] | `http_cache` + `/ingest/contents/check` |
| robots.txt·UA·상세 fetch 상한 | [x] | collector `robots.py` |
| LLM 요약 (실패 폴백·일일 상한) | [x] | `summarize_service`, 키 없으면 규칙 요약 |
| 신뢰 소스 자동 발행 + 푸시 | [x] | `auto_publish`, 서버가 전이 대행 |
| 소스 dry-run·URL 빠른 등록 | [x] | `/dry-run`, `/contents/from-url` |
| 크롤 깨짐 감지 (0건 연속 경고) | [x] | source health: ok/failing/quiet |
| Expo Push 실발송기 | [x] | `EXPO_PUSH_ENABLED=true` 시 실발송, 아니면 스텁 |
| Expo 폐기 토큰 정리 | [x] | `DeviceNotRegistered`·`InvalidDeviceToken` 자동 삭제, 일시 ticket 오류는 재시도 |
| 조용시간 (23~08시 → 아침 발송) | [x] | enqueue 시 `available_at` 조정 |
| AI 요약 품질 게이트 + 보류 사유 | [x] | 통과 실패 시 `needs_review_reason` + 검수 큐 |
| kind 키워드 폴백 분류 | [x] | LLM 없을 때 제목 기반 |
| 소스 신뢰도 카운터 + 자동 강등/승격 제안 | [x] | 무수정/수정/회수 집계, 회수 시 auto_publish 강등 |
| 주기 러너 (기간 콘텐츠 마감 리마인더·예약 발행·데드링크) | [x] | `SCHEDULER_ENABLED`, 기본 1분 주기; event·popup·goods 종료 24시간 전 |
| 감사 로그 (`audit_logs`) | [x] | 발행·회수·삭제 등 기록 |
| 관리자 로그인·수집 소스 감사 로그 | [x] | 성공 로그인·소스 등록/수정/삭제까지 통합 테스트 |
| pytest 82개 통과 (PostgreSQL) | [x] | `scripts/run_tests_pg.py` — 2026-08-27 재실행 82 passed, 임베디드 PG라 Docker 불필요 |
| PostgreSQL 단일 DB 엔진 | [x] | 로컬·CI·운영 모두 PostgreSQL, 인스턴스만 분리 |
| 문의 rate limit | [x] | IP당 10분 5건, 초과 시 429 |
| 이미지 업로드 (`/admin/uploads` → `/media` 서빙) | [x] | PNG/JPEG/WebP/GIF, 5MB 제한, 볼륨 저장 |
| 공개 응답 미검증 이미지 차단 | [x] | 공개는 권리 승인 이미지 키만 반환, 관리자는 검수용 URL 유지 |
| 모바일 API 장애 처리 | [x] | 15초 타임아웃, 네트워크 예외를 상태 0으로 표준화, 401/429/500 계약 테스트 |
| `/privacy`·`/terms` 정책 페이지 | [x] | 스토어 등록용, 운영 문의처 환경변수 주입 |
| 설정 화면 정책 링크 | [x] | 운영 API 모드에서 개인정보처리방침·이용약관 열기 |
| `/health/live`·`/health/ready` | [x] | 프로세스 생존·DB readiness |
| collector 고아 작업 회수·지수 백오프 | [x] | 기본 45분(`INGEST_STALE_AFTER_MINUTES`) |
| collector API 주소 fail-fast 검증 | [x] | `INGEST_SERVER_URL` 누락·비정상 URL 즉시 종료 |
| HTTP 보안 응답 헤더 | [x] | nosniff·frame·referrer·permissions·운영 HSTS |
| 운영 Content-Security-Policy | [x] | 관리자 same-origin 화면의 스크립트·프레임·리소스 제한 |
| 데드링크 점검 SSRF 방어 | [x] | 원문 URL 공개 IP 재검증·리다이렉트 미추적, 내부 주소는 요청하지 않음 |
| production 설정 placeholder 차단 | [x] | 개발용 CORS·문의처 도메인·잘못된 origin 형식 거부 |
| production 관리자 bcrypt 해시 검증 | [x] | 잘못된 예시 문자열로 배포되는 설정 차단 |
| PostgreSQL 연결 재사용 방어·CORS 허용 목록 제한 | [x] | `pool_pre_ping`·30분 recycle·명시적 메서드/헤더 |
| 관리자 웹 same-origin 서빙 (`/admin`) | [x] | vite base `/admin/`, CORS 불필요 |
| Dockerfile (api·collector) | [x] | 워커 1개 고정, 헬스체크, Railway용 |
| CI 릴리스·Docker·PostgreSQL 검증 | [x] | PR/push마다 API 주소·Android 운영 권한·Android 디버그 빌드 사전검사, PostgreSQL 테스트, npm·Python 보안 감사, PostgreSQL 연결 API 이미지 생존 스모크·collector 이미지 빌드 확인 |
| Python 의존성 보안 감사 | [x] | `pip-audit` CI 고정, 런타임 0건 |
| JavaScript 의존성 보안 감사 | [x] | `npm audit --omit=dev --audit-level=high` 0건, Metro/uuid override 고정 |
| 배포 후 API 스모크 명령 | [x] | health·관리자 SPA·게임·랭킹·정책 URL 7개 검사 |
| Railway 배포 | [ ] | `docs/DEPLOY.md` 절차 준비됨. Railway 계정·프로젝트·운영 환경변수 입력 후 외부 게이트 수행 필요 |

> Expo Doctor는 현재 20/21이다. Android Studio에서 바로 열 수 있도록 `android/` 네이티브 프로젝트를
> 저장소 소스로 유지하고 있어 app.json의 Prebuild 전용 속성 동기화 경고가 1건 발생한다. 네이티브
> 패키지·아이콘·딥링크·알림 권한은 Gradle 릴리스 매니페스트 검사로 별도 확인했으며, EAS 연결 후
> 실제 AAB 내부 테스트에서 최종 확인한다.

## 3. 관리자 웹

| 항목 | 상태 |
|------|------|
| 로그인·CRUD·발행·문의 | [x] |
| 자동 수집 소스·실행 이력·검수 연계 | [x] |
| HTML 셀렉터 설정 + 테스트 수집(dry-run) | [x] |
| 자동 발행 토글 + 수집 health 경고 | [x] |
| URL 빠른 등록 + AI 요약 재실행 + 단계 타임라인 | [x] |
| 대시보드 운영 센터 (검수 큐 승인·발행·수정 딥링크, 최근 발행+회수, 수집 주기 인라인 조절·즉시 실행·일시중지) | [x] |
| UTC 시각 표시 버그 수정 (parseUtc 공통화) | [x] |
| 푸시 발송 현황 위젯 + 수동 발송 | [x] |
| 유저 통계 위젯 (설치·토큰·인기 마이픽) | [x] |
| 게임 등록 수를 실제 활성 설치 집계로 표시 | [x] | 수동 interest_count 입력 제거 |
| 최근 작업 이력 (감사 로그) | [x] |
| 예약 발행 UI + 예약 뱃지 | [x] |
| 경고 통합 (데드링크·승격 제안·수집 실패) | [x] |
| 게임/소식 이미지 파일 업로드 UI (URL 직접 입력도 지원) | [x] |
| 프로덕션 호스팅 | [ ] |

## 4. 출시 직전

| 항목 | 상태 |
|------|------|
| 스토어 메타·개인정보처리방침 | [ ] |
| EAS AAB · 내부 테스트 | [ ] |

## 5. 2026-08-27 로컬 재검증 기록

- `npm run verify`: 타입검사 통과, Vitest 6개 파일·31개 테스트 통과, 릴리스 사전검사 계약 통과
- `admin/npm run build`: Vite 운영 빌드 통과
- `server/scripts/run_tests_pg.py`: PostgreSQL 통합 테스트 82개 통과 (DB 시작 재시도·outbox 행 잠금·알림 문구·이미지 URL 검증·운영 API 문서 비공개 포함)
- 비활성 게임 공개 피드 회귀 시나리오 포함: 관리자 기록은 유지하고 Public 소식에서는 제외
- `PYTHONPATH=. server/.venv/Scripts/python.exe -m pytest -q collector/tests`: collector 계약 테스트 21개 통과
- PostgreSQL 연결 타임아웃(3초)·API 시작 스키마 초기화 재시도(최대 4회) 동작을 단위 테스트로 확인
- PostgreSQL 미기동 가짜 로컬 포트에서 초기화가 19.1초 후 `OperationalError`로 종료됨을 확인(무한 대기 없음)
- 정상 카탈로그 응답 시 retired/삭제 게임 ID를 마이픽에서 정리하고, 오프라인 캐시에서는 선택을 보존하는 회귀 테스트 추가
- `scripts/android-release.ps1 -Task assembleRelease` 및 `-Task bundleRelease`: 임시 keystore(시스템 Temp에만 생성) 주입으로 최신 소스 APK/AAB 생성 성공. `apksigner` APK v2 검증 및 AAB `keytool -printcert`로 `GamePickup Release Check` 인증서 확인. 운영 keystore는 생성·저장하지 않았으며 Play 업로드는 EAS 원격 서명을 사용한다.
- 현재 소스 debug APK: Gradle `:app:assembleDebug` 성공. Android API 37 에뮬레이터 `emulator-5554`에 설치 후 Metro dev-client 연결, `MY PICK` 8/8 및 2×2 카드, 홈·오늘 소식·하단 탭·소식 상세를 화면·UIAutomator로 확인
- `emulator-5554`: `com.gamepickup.app/.MainActivity` 프로세스·최상위 액티비티 확인
- 보안 감사 재실행: 모바일·관리자 `npm audit --omit=dev --audit-level=high` 0건, 서버·collector `pip-audit` 0건
- `npx expo-doctor`: 20/21 통과. 네이티브 프로젝트 유지로 인한 Prebuild 동기화 경고 1건은 의도된 구성
- 릴리스 번들 설정 확인: AAB의 운영 API 호스트 포함, `localhost:8000`·`127.0.0.1:8000` 미포함
- 로컬 실행 API 스모크: `http://127.0.0.1:8000`에서 health 2개·관리자 SPA·공개 게임·랭킹·정책 URL 7개 모두 200
- Docker Desktop은 설치되어 있으나 Linux 엔진이 `hasNoVirtualization: true`/`stopped` 상태라 로컬 이미지 스모크는 보류 (BIOS 가상화·WSL2 활성화 필요, CI의 Docker 이미지·PostgreSQL 스모크가 별도 수행)
- `eas-cli`: 현재 셸에 설치되어 있지 않아 `npx eas-cli`로 실행해야 하며 계정 로그인·프로젝트 연결은 외부 게이트로 남음. Railway CLI도 현재 셸에 설치되어 있지 않아 GitHub 연동 Railway UI 배포 경로를 사용하거나 CLI 설치가 필요하다.

---

## 깃 워크플로

작업 끝나면 에이전트가 **한글 커밋 메시지 3안 + 명령어**만 제안. 커밋·push는 사용자 직접.
