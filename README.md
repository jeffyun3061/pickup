# GamePickup (PIKY)

관심 게임 소식을 한곳에서 보는 Android 우선 모바일 앱입니다.  
운영자가 검수·발행한 콘텐츠만 앱에 노출되고, RSS·자동화 수집은 초안(draft)까지만 들어옵니다.

| 구분 | 역할 |
|------|------|
| 모바일 앱 | 5탭 UI, 마이 픽·알림 설정, 문의 |
| API (`server/`) | 공개 조회 / 관리자 CRUD / Ingest 초안 수집 |
| 관리자 웹 (`admin/`) | 게임·소식 등록, 검수, 발행, 문의 확인 |

---

## 화면 구성 (5탭)

UI는 Stitch **Neon-Tactical** 시안을 기준으로 구현했습니다.  
아래 캡처는 `design-ref/` HTML 시안을 모바일 뷰포트(393×852)로 렌더링한 것입니다.

| 새 소식 | 마이 픽 | 홈 |
|:---:|:---:|:---:|
| ![새 소식](docs/screenshots/01-news-feed.png) | ![마이 픽](docs/screenshots/02-my-pick.png) | ![홈](docs/screenshots/03-home.png) |
| 통합 소식·팝업&행사 세그먼트 | 선택한 게임 그리드·최대 8개 | 오늘 소식 + 이벤트 기간 |

| 랭킹 | 설정 |
|:---:|:---:|
| ![랭킹](docs/screenshots/04-ranking.png) | ![설정](docs/screenshots/05-settings.png) |
| 포디움 + 관심 순위 | 알림 3종·공지·문의 |

**탭 순서:** 새 소식 · 마이 픽 · 홈 · 랭킹 · 설정

---

## 왜 이렇게 만들었는지

게임 소식은 공식 채널·커뮤니티·이벤트 페이지에 흩어져 있습니다.  
사용자 입장에서는 "내가 하는 게임 새 소식만 빠르게 보고 싶다"는 니즈가 있고, 운영 입장에서는 **검수 없이 올라가면 안 되는** 콘텐츠가 섞입니다.

그래서 흐름을 이렇게 잡았습니다.

```text
수집(Ingest) → draft → 운영 검수(reviewed) → 발행(published) → 앱 노출
```

collector와 관리자 웹은 운영 도구이며 모바일 앱의 런타임 의존성이 아닙니다. 자동 수집이
멈춰도 기존 발행 소식은 앱에서 읽을 수 있고, 운영자는 관리자 웹(또는 Admin API)에서
같은 상태 머신으로 수동 등록할 수 있습니다. API가 잠시 끊기면 앱은 마지막 카탈로그
스냅샷을 보여줍니다.

앱 사용자는 로그인하지 않습니다. 대신 **설치 단위 credential**으로 기기·알림 설정만 서버와 맞춥니다.  
쓰기 권한은 관리자 JWT와 Ingest Key로 나눠서, 키가 유출돼도 피해 범위를 줄였습니다.

---

## 기술 스택

| 영역 | 스택 |
|------|------|
| 모바일 | Expo 57, React Native, TypeScript, Expo Router |
| API | Python, FastAPI, SQLAlchemy, Pydantic, pytest |
| 관리자 | Vite, React, TypeScript |
| 저장 | PostgreSQL(로컬·CI·운영, 환경별 인스턴스 분리) |
| 인증 | Admin JWT(bcrypt), Ingest API Key, Installation secret |

`main`/`develop`에 push하거나 PR을 만들면 `.github/workflows/ci.yml`가 모바일 타입·단위 테스트,
관리자 웹 빌드, API·collector 테스트를 자동으로 확인합니다.

---

## 아키텍처 요약

### 모바일

화면은 공통 컴포넌트(`AppHeader`, `FeedCard`, `CustomTabBar` 등)로만 조립합니다.  
데이터는 `CatalogRepository` 뒤에 숨겨서 `preview` / `empty` / `api` 모드를 바꿔도 UI 코드는 그대로 둡니다.

```text
app/ → hooks/ → data/CatalogRepository → domain/
         ↘ state/ (온보딩·마이픽·알림 3종)
```

- 비민감 설정: AsyncStorage  
- 설치 secret: SecureStore  
- 반응형: `resolveLayout()` — 360 / 393 / 412dp 기준

### 백엔드

모듈형 모놀리스. 의존성은 안쪽으로만 갑니다.

```text
api/ → services/ → domain/ → repositories/
```

콘텐츠 상태는 Domain에서 강제합니다.

```text
draft → reviewed → published
```

발행 시 푸시는 outbox에만 적재하고, Expo Push API 발송은 별도 dispatch로 분리했습니다. (발행 트랜잭션과 외부 API 장애 분리)

자세한 설명: [docs/BACKEND_ARCHITECTURE.md](docs/BACKEND_ARCHITECTURE.md)

운영자가 삭제·정정 요청과 수집 소스 장애를 처리하는 기준은
[docs/CONTENT_OPERATIONS.md](docs/CONTENT_OPERATIONS.md)에 기록합니다.

---

## 프로젝트 구조

```text
.
├── app/                 # Expo Router (5탭 + 온보딩·문의)
├── src/                 # 컴포넌트, hooks, data, theme
├── server/              # FastAPI
├── admin/               # 관리자 웹
├── design-ref/          # Stitch 시안 HTML·DESIGN.md
├── docs/                # 아키텍처·결정 로그·스크린샷
└── tools/               # 스크린샷 캡처 스크립트
```

---

## 실행 방법

### 1. 모바일 (기본: preview 모드)

```powershell
cd C:\Users\user\Projects\pickup
npm install
npm run verify
npm run android
```

### Android Studio Live UI (권장)

개발 클라이언트를 한 번 설치한 뒤에는 매번 APK를 다시 빌드하지 않아도 됩니다. Android Studio에서 에뮬레이터를 켜고, 프로젝트 루트에서 Metro를 실행합니다.

```powershell
cd C:\Users\user\Projects\pickup
$env:NODE_OPTIONS = "--dns-result-order=ipv4first"
npm run android
```

`npm run android`는 에뮬레이터가 접근할 수 있는 LAN Metro 주소로 개발 클라이언트를 엽니다. 이후 `app/` 또는 `src/`의 TypeScript·스타일을 저장하면 Fast Refresh로 에뮬레이터에 바로 반영됩니다. Metro 터미널에서 `r`을 누르면 수동 새로고침합니다.

Android Studio에서 `assembleDebug`만 실행해 APK를 직접 열면 debug 변형은 JavaScript를
Metro에서 받기 때문에 스플래시 또는 빈 화면으로 남을 수 있습니다. 화면을 보며 개발할
때는 프로젝트 루트에서 `npm run android`를 실행하고, standalone 동작은 EAS preview APK
또는 production AAB로 확인합니다.
처음 실행이 검은 화면에 머물면 Metro가 오래된 캐시를 다시 만드는 중일 수 있으므로 위 명령을 다시 실행하고 `--clear`를 유지합니다. 네이티브 디버그 클라이언트를 `assembleDebug`로만 실행한 경우에는 개발 메뉴의 `Change Bundle Location`에서 현재 Metro 주소(에뮬레이터는 보통 `10.0.2.2:8081` 또는 Metro가 출력한 LAN 주소)를 선택해야 합니다. 사용자 정의 폰트가 느린 기기에서 로드되지 않아도 앱은 8초 뒤 시스템 폴백으로 진입합니다.

다음 변경은 네이티브 APK를 다시 빌드해야 합니다.

- `android/`, `app.json`, 권한·아이콘·스플래시 변경
- 네이티브 모듈이 포함된 패키지 추가·삭제

Windows에서 로컬 `assembleRelease`를 실행할 때 React Native codegen 경로가 260자를
넘을 수 있습니다. 이 경우 프로젝트를 옮기지 않고 짧은 임시 드라이브(`P:`)로 매핑해
빌드하는 스크립트를 사용합니다. 스토어 서명 키와 운영 API 주소는 먼저 환경변수로
설정해야 합니다. 스크립트는 환경변수가 비어 있으면 Android Studio의 내장 JBR와
기본 SDK 경로를 자동 탐지하고, 이미 같은 `P:` 매핑이 있으면 재사용합니다. 실제 Play
배포용 AAB는 경로 제한이 없는 EAS Linux 빌드를 권장합니다.

```powershell
$env:EXPO_PUBLIC_CATALOG_MODE = "api"
$env:EXPO_PUBLIC_API_URL = "https://<운영-API-도메인>"
$env:MYAPP_UPLOAD_STORE_FILE = "C:\secure\gamepickup-upload.jks"
$env:MYAPP_UPLOAD_STORE_PASSWORD = "<secret>"
$env:MYAPP_UPLOAD_KEY_ALIAS = "gamepickup"
$env:MYAPP_UPLOAD_KEY_PASSWORD = "<secret>"
.\scripts\android-release.ps1 -Task assembleRelease
```

`P:` 드라이브가 이미 같은 프로젝트 상위 폴더를 가리키면 재사용하고, 다른 경로를
가리키면 덮어쓰지 않고 중단합니다. 스크립트가 직접 만든 매핑은 빌드가 끝나면
해제하며 원본 프로젝트 파일은 이동하지 않습니다.

API 연동 시:

```env
EXPO_PUBLIC_CATALOG_MODE=api
EXPO_PUBLIC_API_URL=http://<PC_IP>:8000
```

Android 운영 빌드 전에는 반드시 API 주소 검사를 실행합니다.

`scripts/android-release.ps1`도 같은 사전검사를 서명 단계 전에 자동 실행하므로,
HTTPS가 아닌 주소나 localhost·placeholder 주소로 release 산출물이 만들어지지 않습니다.

```powershell
$env:EXPO_PUBLIC_CATALOG_MODE = "api"
$env:EXPO_PUBLIC_API_URL = "https://<운영-API-도메인>"
npm run release:check
```

EAS 빌드에도 같은 검사가 자동으로 실행되므로 API 주소가 빠진 빌드는 중단됩니다.

배포 후 공개 경로 스모크 검사:

```powershell
npm run smoke:api -- https://<실제-API-도메인>
```

### 장애 시 롤백

1. `/health/ready` 또는 `npm run smoke:api`가 실패하면 관리자에서 자동 수집과
   자동 발행을 먼저 중지한다. 첫 출시에는 collector를 배포하지 않았다면 이 단계는
   수동 등록만 유지한다.
2. Railway 프로젝트의 **api 서비스 → Deployments**에서 마지막 정상 배포를 선택해
   Rollback/Redeploy한다. `/data` 볼륨은 삭제하지 않는다(업로드 이미지 보존).
3. `/health/live` → `/health/ready` → `npm run smoke:api -- https://<도메인>` 순서로
   복구를 확인한다. 실패 원인·영향 범위·롤백 시각을 감사 기록에 남긴다.
4. 스키마 변경이 포함된 배포는 이전 이미지와 호환되는지 먼저 확인한다. 비호환이면
   이미지를 되돌리지 말고 Railway PostgreSQL 백업 복원 여부를 별도로 판단한다.
5. 복구 후 collector는 `auto_publish=false`로 시작하고, 정상 dry-run과 수동 검수를
   통과한 뒤에만 자동 발행을 다시 켠다.

### 2. API

```powershell
cd C:\Users\user\Projects\pickup\server
python -m venv .venv
.\.venv\Scripts\pip install -r requirements-dev.txt
copy .env.example .env
# .env에서 개발용 관리자 해시·JWT·ingest 키를 확인
.\.venv\Scripts\python scripts\run_local_pg_api.py
```

`run_local_pg_api.py`는 Docker 없이 개발 의존성의 PostgreSQL을
`server/tmp/gamepickup-postgres`에 시작하고 FastAPI를 함께 실행합니다. 데이터는
스크립트를 다시 실행해도 보존되며, 로컬·CI·운영 모두 PostgreSQL을 사용합니다.
Dockerfile과 `compose.yaml`은 CI 및 나중의 컨테이너 배포 검증용으로만 유지합니다.

전체 API 테스트는 별도 임베디드 PostgreSQL에서 실행합니다.

```powershell
.\.venv\Scripts\python scripts\run_tests_pg.py
```

운영 APK가 참조할 API는 반드시 공개 HTTPS 주소여야 합니다. `127.0.0.1`은
현재 PC/에뮬레이터에서만 접근할 수 있으므로 외부 테스트용 빌드에 넣지 않습니다.

### 3. 관리자 웹

```powershell
cd admin
npm install
npm run dev
```

### 스크린샷 다시 뽑기

```powershell
node tools/capture-screenshots.mjs
```

`design-ref/` HTML을 기준으로 `docs/screenshots/`에 5탭 이미지를 생성합니다.

---

## 주요 API

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/games`, `/contents`, `/rankings` | 발행 콘텐츠 조회 (Public) |
| POST | `/api/v1/inquiries` | 문의 등록 |
| POST | `/api/v1/installations` | 설치 credential 발급 |
| POST | `/api/v1/admin/login` | 관리자 JWT |
| POST | `/api/v1/ingest/contents` | 초안 수집 (Ingest Key) |

스토어 정책 링크는 운영 API의 `/privacy`와 `/terms`에서 제공하며, 앱 설정에서도
운영 API 모드일 때 바로 열 수 있습니다.

---

## 문서

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — 앱 계층·확장 지점
- [docs/BACKEND_ARCHITECTURE.md](docs/BACKEND_ARCHITECTURE.md) — API·상태머신·보안
- [docs/INGESTION_DATA_CONTRACT.md](docs/INGESTION_DATA_CONTRACT.md) — RSS·API·HTML 공통 수집 계약과 출처별 차이 처리
- [docs/DECISIONS.md](docs/DECISIONS.md) — ADR (설계 결정 기록)
- [docs/PROGRESS.md](docs/PROGRESS.md) — 진행 현황
- [docs/SECURITY.md](docs/SECURITY.md) — 의존성 감사·운영 보안 규칙

---

## 현재 상태

- [x] 5탭 UI + Preview/Empty/Api 카탈로그 모드
- [x] FastAPI 계층·상태머신·Admin/Ingest/Public 분리
- [x] 관리자 웹 CRUD·발행·문의
- [x] Installation 인증 + 푸시 outbox/Expo Push API 디스패처 (운영 토큰 오류 자동 정리)
- [ ] Railway PostgreSQL·HTTPS 배포 (절차는 `docs/DEPLOY.md`에 준비)
- [ ] Play 스토어 출시

---

## 라이선스

개인 포트폴리오·실서비스 PoC 목적 프로젝트입니다.
