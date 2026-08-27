# 배포 가이드 (Railway 단일 프로젝트)

원칙: 관리 쉬운 정석 구성, 오버엔지니어링 금지. 1인 운영 기준 월 $10~15 예상.
트래픽·인원이 늘면 그때 확장한다 (CDN, 오브젝트 스토리지, 워커 증설 등).

## 구성 (필수 2개 + 선택 1개 + 볼륨 1개)

| 서비스 | 소스 | 역할 |
|---|---|---|
| Postgres | Railway 관리형 | 운영 DB (자동 백업) |
| api | `Dockerfile` | FastAPI + 관리자 웹(`/admin`) + 업로드 이미지(`/media`) |
| collector (선택) | `Dockerfile.collector` | RSS/API/HTML 수집 폴링. 첫 출시에는 수동 등록으로 대체 가능 |

- **api 볼륨**: `/data` 마운트 → 업로드 이미지가 재배포에도 유지된다.
  관리자 보드에서 올린 게임/소식 사진은 볼륨에 저장되고 `https://<도메인>/media/...` 로 서빙.
- **워커 1개 고정** (Dockerfile CMD): 인메모리 rate limit·스케줄러 중복 실행 방지.
- API는 시작 시 PostgreSQL 초기화를 연결 타임아웃과 함께 최대 약 20초 재시도하므로, Railway의 짧은 DB 부팅 순서 차이를 흡수한다. 계속 실패하면 컨테이너가 종료되어 readiness에 진입하지 않는다.

## api 환경변수

```
DATABASE_URL           = Postgres 서비스 참조 (postgresql+psycopg://... 권장; Railway 기본 postgresql://도 자동 정규화)
ENV                    = production
ADMIN_USERNAME         = admin
ADMIN_PASSWORD_HASH    = (make_password_hash.py 로 생성)
JWT_SECRET             = UTF-8 32바이트 이상 긴 무작위 문자열
INGEST_API_KEY         = UTF-8 32바이트 이상 긴 무작위 문자열 (collector와 동일 값)
CORS_ORIGINS           = https://<도메인> (운영에서는 빈 값 금지; 앱 공개 API 도메인만 허용)
EXPO_PUSH_ENABLED      = true
SCHEDULER_ENABLED      = true
INGEST_STALE_AFTER_MINUTES = 45
OPENAI_API_KEY         = (요약 사용 시)
MIN_APP_VERSION        = (강제 업데이트 필요 시)
# MEDIA_DIR / ADMIN_DIST_DIR 는 Dockerfile 기본값 사용 (/data/media, /app/admin-dist)
PRIVACY_CONTACT_EMAIL = 운영 문의 이메일 (production 필수)
```

## collector 환경변수

```
INGEST_API_KEY    = api와 동일 값
INGEST_SERVER_URL = api 서비스 내부 주소 (Railway private networking)
```

## 배포 순서

1. Railway 프로젝트 생성 → Postgres 추가.
2. GitHub 저장소 연결 → api 서비스 (Dockerfile Path `Dockerfile`), `/data` 볼륨 마운트.
3. 환경변수 입력 → 배포 → `https://<도메인>/health/live`와
   `https://<도메인>/health/ready`가 각각 200인지 확인.
   로컬에서 전체 공개 경로를 반복 확인하려면 `npm run smoke:api -- https://<도메인>`을 실행한다.
4. (선택) 자동 수집을 사용할 때만 collector 서비스 추가 (Dockerfile Path
   `Dockerfile.collector`) → 환경변수 입력 → 모든 소스를 dry-run한다. 수동 출시라면
   이 단계는 건너뛰고 관리자 웹의 URL 등록/직접 입력을 사용한다.
5. `/admin` 로그인 → **권리 확인이 끝난 게임만** 생성(이미지 출처·허가 상태 기록) →
   소식 검수·발행 → 앱(api 모드)에서 확인.
6. 앱: `EXPO_PUBLIC_CATALOG_MODE=api`, `EXPO_PUBLIC_API_URL=https://<도메인>` 으로 EAS 빌드.

collector는 앱의 런타임 의존성이 아니다. API와 PostgreSQL만 운영 중이어도 관리자에서
수동으로 발행한 소식은 즉시 앱에 표시된다. 자동 수집은 첫 주 수동 운영으로 원문 권리와
파싱 품질을 확인한 뒤 별도 서비스로 켜는 것을 권장한다.

### 운영 카탈로그 초기화 원칙

`server/scripts/seed_demo_games.py`는 화면·API 계약 확인용 개발 시드다. 운영 DB에
그대로 실행하지 않는다(데모 관심 수와 이미지 출처가 실서비스 근거가 아니기 때문).
운영에서는 관리자에서 권리 검토가 끝난 게임을 등록하고, `interest_count`는 입력하지
않거나 0으로 둔다. 공개 랭킹은 `installation_games`의 실제 활성 설치 수만 집계한다.

### Android 내부 테스트·운영 AAB

`eas.json`에 API 모드가 고정된 두 프로필을 둔다. 최초 1회만 EAS 로그인과
프로젝트 연결을 한다.

운영 앱 서명은 EAS의 원격 Android credentials를 사용한다. 로컬에서
`npx expo prebuild`로 `android/`를 생성해 Gradle 빌드를 할 때도 디버그 키를
재사용하지 말고
`MYAPP_UPLOAD_STORE_FILE`, `MYAPP_UPLOAD_STORE_PASSWORD`,
`MYAPP_UPLOAD_KEY_ALIAS`, `MYAPP_UPLOAD_KEY_PASSWORD`를 비밀 환경변수로
주입해야 한다. keystore·`credentials.json`은 저장소에 커밋하지 않는다.

```powershell
npx eas-cli login
npx eas-cli init
npx eas-cli build --profile preview --platform android       # 내부 배포용 APK
npx eas-cli build --profile production --platform android    # Play 업로드용 AAB
npx eas-cli submit --profile production --platform android   # Play 내부 테스트 트랙
```

운영 API 주소는 EAS 프로젝트 환경변수로 등록한다(소스에 URL·시크릿을 커밋하지 않는다).

```powershell
npx eas-cli env:set --scope project --name EXPO_PUBLIC_API_URL --value https://<도메인> --environment production --visibility plaintext
npx eas-cli env:set --scope project --name EXPO_PUBLIC_API_URL --value https://<도메인> --environment preview --visibility plaintext
npx eas-cli env:list --scope project --environment production
```

`EXPO_PUBLIC_API_URL`은 앱 번들에 포함되는 공개 API 주소이므로 `plaintext`로 저장한다.
JWT·ingest 키 같은 서버 비밀값은 앱/EAS에 넣지 않고 Railway 환경변수에만 저장한다.
`eas.json`은 preview를 `preview`, production을 `production` EAS 환경에 각각 고정한다.

그 다음 `eas-cli build`를 실행한다. API가 배포되고 `/health/ready`가 확인되기 전에는
production 프로필을 만들지 않는다. `npx eas-cli init`은 최초 1회 실행해 `projectId`를
연결해야 네이티브 푸시 토큰 등록이 완성된다.

운영 빌드 전에 로컬호스트·preview 모드가 섞이지 않았는지 확인한다.

```powershell
$env:EXPO_PUBLIC_CATALOG_MODE = "api"
$env:EXPO_PUBLIC_API_URL = "https://<도메인>"
npm run release:check
# 주소 차단 규칙(placeholder·localhost·경로)을 자동 검증
npm run test:release
```

### Windows 로컬 Gradle 경로 제한

React Native의 새 아키텍처 codegen은 Windows에서 `Filename longer than 260 characters`
오류가 날 수 있다. 소스 경로를 영구적으로 옮기거나 네이티브 코드를 수정하지 말고,
프로젝트를 임시 `P:` 드라이브로 매핑하는 저장소 스크립트를 사용한다.

```powershell
$env:EXPO_PUBLIC_CATALOG_MODE = "api"
$env:EXPO_PUBLIC_API_URL = "https://<도메인>"
# MYAPP_UPLOAD_* 네 값은 실제 release keystore의 비밀값으로 설정
.\scripts\android-release.ps1 -Task bundleRelease
```

이 스크립트는 로컬 검증용이다. 회사 PC 정책 등으로 `subst`가 차단되면 스크립트가
프로젝트 원래 경로로 자동 전환한다(경로가 긴 환경에서는 EAS 빌드를 권장).
실행 시 `scripts/release-preflight.mjs`를 먼저 호출해 운영 API의 HTTPS·origin·placeholder
조건을 확인한 뒤 서명 환경변수와 Gradle 작업을 진행한다.
`JAVA_HOME`·`ANDROID_HOME`이 비어 있으면 Android Studio의 내장 JBR와 기본 SDK를
자동 탐지하며, 이미 같은 `P:` 매핑이 있으면 재사용한다.
Play 업로드 AAB는 동일한 환경변수 검사를 수행하는 EAS Linux 빌드
(`npx eas-cli build --profile production --platform android`)를 표준 경로로 사용한다.
`debug.keystore`를 운영 서명에 재사용하지 않는다.

## 스토어 등록에 쓰는 URL

- 개인정보처리방침: `https://<도메인>/privacy`
- 이용약관·자동 정리 고지: `https://<도메인>/terms`
- 관리자: `https://<도메인>/admin` (검색엔진 노출 없음, JWT 로그인)

## 로컬 PostgreSQL과 검증

SQLite는 지원하지 않는다. 1인 개발 환경에서는 Docker를 설치하거나 실행하지 않고
개발 의존성의 PostgreSQL 실행 스크립트를 사용한다. 데이터는 저장소의 무시된 경로에
보존되며, 운영 Railway PostgreSQL과 엔진은 동일하게 PostgreSQL이다.

```powershell
cd C:\Users\user\Projects\pickup\server
.\.venv\Scripts\pip install -r requirements-dev.txt
copy .env.example .env
.\.venv\Scripts\python scripts\run_local_pg_api.py
```

`run_local_pg_api.py`는 `server/tmp/gamepickup-postgres`에 데이터베이스를 만들고
FastAPI를 `http://127.0.0.1:8000`에서 실행한다. 프로세스를 종료해도 데이터는
보존된다. 컨테이너 이미지와 Compose 파일은 CI·운영 컨테이너 배포가 필요할 때만
사용한다.

```powershell
cd server
.\.venv\Scripts\python scripts\run_tests_pg.py  # 임베디드 PostgreSQL (Docker 불필요)
```

## 나중에 (지금 하지 않음)

- 이미지가 수 GB로 늘면: Cloudflare R2 + CDN으로 이관
- 트래픽 증가 시: api 수평 확장 (rate limit을 Redis로, 스케줄러 분리 후)
- 스키마 변경이 잦아지면: Alembic 도입 (ADR-012)
