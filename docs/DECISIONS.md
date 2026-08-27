# 설계 결정 (ADR)

## ADR-001: UI는 Stitch Neon-Tactical만 따른다
- 근거: 제공된 `design-ref/DESIGN.md`와 화면 HTML이 공식 시안이다.
- 결정: 배경 `#131314`, 액센트 `#FFD700` / `#D05BFF` / `#FFB300`, 폰트 Space Grotesk·Manrope·JetBrains Mono.
- 금지: 라이트 민트 테마, 임의 카드 UI, 시안에 없는 장식.

## ADR-002: 게임·소식 데이터는 Repository 경계로만 공급한다
- 근거: 콘텐츠는 운영자가 검수·발행한 뒤 API로 들어온다. UI는 구현체를 모른다.
- 결정:
  - 계약: `CatalogRepository` (`src/data/types.ts`)
  - 진입점: `src/data/catalog.ts` (`EXPO_PUBLIC_CATALOG_MODE`)
  - `preview`(기본): Stitch 시안 퀄리티 검증용 `PreviewCatalogRepository` — 픽션 타이틀 + 시안 AI 이미지
  - `empty`: 실운영 EmptyState 검증용 `EmptyCatalogRepository`
  - 이후: `ApiCatalogRepository`로 교체
- 금지: 실 IP(원신·롤 등) 게임명·공식 로고 하드코딩, 화면에서 Repository를 우회한 시드.

## ADR-003: 5탭 정보 구조는 시안 라벨을 따른다
- 뉴스 피드 · 마이 픽 · 홈 · 랭킹 · 설정
- 헤더 브랜드: `PIKY` (시안 TopAppBar)
- 알림 설정 3종: 선택 게임 새 소식 / 종료 임박 / 서비스 공지 (제품 계약)
- `종료 임박`은 게시 즉시 알림을 대신하지 않는다. 게시 알림은 새 소식 토글,
  마감 리마인더는 종료 임박 토글만 각각 따른다.
- 설정 화면에는 게임별 토글을 만들지 않는다. 사용자는 선택한 모든 게임의
  새 소식 수신 여부, 이벤트 마감 알림, 피키 공지 수신 여부만 조절한다.
- `내 게임 새 소식`은 업데이트·인게임 이벤트를 게임별로 묶어 발송하고,
  팝업·굿즈는 별도 탐색 피드에만 둔다. 팝업·굿즈 게시로 푸시를 보내지 않는다.
- 푸시 제목은 채널별 브랜드 문구로 고정한다: `피키의 새로운 소식 ~♬`,
  `피키의 이벤트 알림`, `피키 공지`. 새 소식 본문은 한 건이면
  `게임명 · 제목`, 여러 건이면 `게임명에 새 소식 N건이 올라왔어요`로
  묶어 짧게 표시한다.

## ADR-004: 공통 컴포넌트로만 화면을 조립한다
- 근거: 재사용·일관성·Android 폭(360/393/412) 대응.
- 결정: `AppHeader`, `CustomTabBar`, `Screen`, `FeedCard`, `EmptyState`, `SegmentedControl`, `ToggleRow`, `PickSquadCard`, `GameRegisterSlot`, `GameTile`만 사용.
- 마이픽: 시안처럼 한 페이지 2×2(4칸) + 가로 스와이프. 빈 칸은 `게임 등록` 슬롯.
- 화면별 일회성 스타일 복제를 금지한다.

## ADR-005: 로컬 상태는 설치 환경설정만 담당
- AppProvider: onboarding 완료 여부, 선택 gameIds, 알림 3종.
- 서버 소식/게임은 이후 API Repository로 교체 (지금은 EmptyCatalog).

## ADR-006: 레이아웃은 폭 스케일로만 반응한다
- 근거: Android 360/393/412에서 탭 라벨·카드 썸네일·마진이 깨지기 쉽다.
- 결정: `useLayout()` / `resolveLayout(width)`가 margin·thumb·tabLabel·타이포를 일괄 제공.
- 화면마다 `width` 분기를 직접 쓰지 않는다.

## ADR-007: 로컬 저장소를 민감/비민감으로 분리한다
- 근거: 회원가입이 없어도 **설치 비밀 자격증명**(추후 API)은 민감하고, 온보딩·알림 토글은 비민감이다. 모든 값을 SecureStore에 넣으면 책임 경계가 흐려지고, 전부 AsyncStorage에 넣으면 secret이 평문 영역에 남는다.
- 결정:
  - 비민감 환경설정 → `preferencesStore` (`@react-native-async-storage/async-storage`)
  - 민감 설치 secret → `credentialStore` (`expo-secure-store`) — 키체인/Keystore
- 금지: “일단 돌아가게” SecureStore에 환경설정을 넣는 임시 우회.
- 참고: SecureStore는 회원 로그인용이 아니라 **기기 설치 단위 secret**용이다.

## ADR-008: 폰트·이미지는 에셋 인덱스 매핑으로만 로드한다
- 근거: 화면마다 `require`/`@expo-google-fonts` 배럴 import를 흩뿌리면 경로 중복·미사용 weight 해석·교체 비용이 커진다.
- 결정:
  - `src/assets/fonts.ts` — 사용 weight만 명시 require, `useFonts(fontAssets)`
  - `src/assets/images.ts` — 이미지 키 매핑 (권리 확인된 에셋만)
  - `theme.tokens.font` 키와 `fontAssets` 키를 동일하게 유지
- 금지: 화면 파일에서 폰트/이미지 경로를 직접 require.

## ADR-009: 백엔드·관리자·자동화 ingest 분리
- 근거: 앱 사용자는 로그인 없이 발행 콘텐츠만 보고, 운영(나)만 쓰기 권한이 있어야 한다. RSS/AI 등은 초안만 넣을 수 있어야 한다.
- 결정:
  - `server/` FastAPI 모듈형 모놀리스 — Controller→Service→Repository
  - `admin/` 관리자 웹 — 로그인 후 게임/소식 CRUD·검수·발행·문의 확인
  - 앱 유저 인증 없음. 관리자만 `ADMIN_USERNAME` + `ADMIN_PASSWORD_HASH` → JWT
  - 자동화는 `INGEST_API_KEY` 헤더로 **draft 생성만** (`POST /api/v1/ingest/contents`)
  - 공개 API는 `published`만 조회 + `POST /api/v1/inquiries` (문의)
  - 시크릿은 환경변수만 (하드코딩 금지)
- 콘텐츠 상태: `draft` → `reviewed` → `published`
- 금지: 앱에 관리자 비밀번호 심기, ingest 키로 즉시 발행.

## ADR-010: 설치 credential + device token + push outbox
- 근거: 앱 유저 로그인 없이도 푸시 타겟이 필요하다. Admin JWT로 기기를 등록하면 최소 권한이 붕괴한다. 발행 트랜잭션 안에서 Expo Push API를 직접 호출하면 외부 장애가 발행을 깨뜨린다.
- 결정:
  - `POST /api/v1/installations` — `installation_id` + `secret` 1회 발급, secret은 bcrypt 해시만 저장
  - 쓰기: `X-Installation-Id` + `X-Installation-Secret` (네 번째 역할 Installation)
  - `PUT .../device-token` — Expo Push Token 배달 주소 upsert
  - `PUT .../preferences` — ADR-003 알림 3종 + `game_ids` 서버 동기
  - Content/Announcement 발행 시 **outbox enqueue만** (같은 DB 트랜잭션)
  - 같은 설치·게임의 대기 중 새 소식은 `게임명 새 소식 N건`으로 합쳐 한 번만 발송
  - `POST /api/v1/admin/push/dispatch` — outbox 디스패처(개발은 로그 스텁, 운영은 Expo Push API)
  - 요청 단위 트랜잭션: Repository는 flush만, `get_db`가 commit/rollback
- 금지: Admin/Ingest 키로 device token 등록, publish 중 동기 Expo 호출, secret 평문 DB 저장.

## ADR-011: 수집 설정은 Admin, 실행은 별도 Collector
- 근거: FastAPI 요청 프로세스에서 외부 RSS/API를 직접 호출하면 지연·장애·SSRF가 운영 API로 전파된다. 반대로 별도 관리 웹을 만들면 인증·검수 UI가 중복된다.
- 결정:
  - 기존 `admin/`을 통합 운영 콘솔로 확장해 소스 CRUD·즉시 실행·이력을 관리한다.
  - `collector/`는 별도 프로세스로 실행하며 `X-Ingest-Key` 최소 권한만 가진다.
  - 소스와 실행 이력은 `IngestSource` / `IngestRun`으로 저장하고 작업 claim·완료를 API 계약으로 분리한다.
  - RSS/API 결과는 멱등 키와 함께 항상 draft로 저장한다. 발행은 Admin 상태머신만 수행한다.
  - 외부 URL은 공개 HTTP(S)만 허용하고 사설망·localhost를 거부한다.
  - API 비밀값은 DB가 아닌 collector 환경변수에 저장하며 DB에는 환경변수 이름만 둔다.
  - 실패 시 지수 백오프 후 재시도 일정을 잡는다.
- 이번 범위 제외: 사이트별 HTML 크롤링. 약관·robots.txt·저작권 검토 후 connector로 추가한다.
- 금지: 웹 요청 중 수집 실행, 자동 발행, DB에 외부 API 토큰 평문 저장.

## ADR-012: HTML 크롤 + LLM 요약 + 신뢰 소스 자동 발행
- 근거: 대상 게임 공식 사이트 대부분이 RSS/공개 API를 제공하지 않는다. 속도(공지 후 10~15분 내 앱 노출)와 놓침 방지가 앱의 핵심 가치인데, 매 건 수동 검수는 이를 깨뜨린다. 반면 ingest 키에 발행 권한을 주면 ADR-009의 권한 경계가 무너진다.
- 결정:
  - **커넥터 3종 유지**: `rss` / `api`(JSON 경로 매핑) / `html`(CSS 셀렉터). 사이트별 전용 크롤러를 만들지 않고 소스별 config로 흡수한다. 렌더링(JS) 필요 사이트는 내부 JSON API를 우선 찾고, 그것도 없으면 수동(URL 등록) 운용.
  - **변화 감지 3단**: ① 조건부 GET(ETag/Last-Modified) ② 목록 본문 SHA-256 비교 ③ 아이템 멱등 키 사전 조회(`/ingest/contents/check`). 변화 없으면 파싱·상세 fetch를 전부 건너뛴다. HTTP 캐시는 `IngestSource.http_cache_json`에 저장되어 claim 시 collector로 전달된다.
  - **크롤 예의**: robots.txt 확인(24h 캐시, HTML만 — RSS/JSON 피드는 구독용 인터페이스로 간주), 식별 UA, 상세 fetch는 새 글만·실행당 상한·간격 대기, SSRF 차단.
  - **LLM 요약은 서버 책임**: collector는 `raw_text`(상세 본문, 최대 8천자)만 제출하고, 서버가 응답 후 BackgroundTasks에서 저가 모델(`gpt-5-mini`, JSON 강제)로 3줄 요약+종류 분류. 실패 시 `summary_status=failed`로 draft에 남겨 검수 폴백. `SUMMARIZE_DAILY_LIMIT`로 비용 상한.
  - **자동 발행은 서버가 대행**: `IngestSource.auto_publish` 소스는 요약 성공 시 서버가 상태머신 전이(draft→reviewed→published)와 푸시 outbox를 수행한다. ingest 키가 발행하는 것이 아니므로 ADR-009 경계 유지. 요약 실패 건은 자동 발행하지 않는다. 사후 교정은 "발행 회수"로.
  - **조용한 실패 감지**: 성공인데 페이지 변화 후 0건 파싱이 연속되면(기본 5회) 소스 health를 `quiet`로 표시 — 셀렉터 깨짐 의심. 연속 실패 3회는 `failing`.
  - **빠른 수동 등록**: `POST /admin/contents/from-url` — URL만으로 제목·본문 추출+요약된 초안 생성. dry-run(`/admin/ingest-sources/dry-run`)으로 저장 전 셀렉터 검증.
  - **스키마 마이그레이션**: Alembic 없이 `db_migrate.ensure_schema`(ADD COLUMN만). 파괴적 변경이 필요해지면 Alembic으로 승격.
- 금지: 전문(全文) 재게시(요약+원문 링크만), robots 차단 경로 크롤, 요약 실패 건 자동 발행, Playwright 등 렌더링 크롤 선제 도입.

## ADR-013: 외부 이미지는 권한 검수 후 노출한다
- 근거: 공식 뉴스·RSS·API가 이미지 URL을 제공하더라도 앱 재게시나 직접 링크까지 자동 허용되는 것은 아니다. 블러 처리도 저작권 허가를 대신하지 못한다.
- 결정:
  - 게임·소식 이미지는 `unverified` / `official` / `licensed` / `original` 상태와 출처·허가 근거 URL을 관리자에서 함께 기록한다.
  - 자동 수집 이미지는 항상 `unverified`로 들어오며, 관리자가 근거를 확인하기 전 앱에서 원본을 노출하지 않는다.
  - 권한 미확인·URL 없음·로드 실패 시 `src/assets/images.ts`의 자체 제작 테마 이미지를 게임별로 사용한다.
  - RSS `enclosure`·Media RSS, JSON 이미지 필드, HTML 이미지 셀렉터는 후보 수집만 담당하며 사용 허가 판정을 자동화하지 않는다.
- 금지: 권한 미확인 이미지 노출, 블러로 권리 검수를 우회, 약관상 허용되지 않은 이미지 핫링크.

## ADR-014: 관리자 세션 만료 복귀 + 로그인 잠금
- 근거: 관리자 화면을 켜둔 채 JWT가 만료되면 폴링이 401을 무한 반복하며 조용히 깨진다(운영 로그로 확인). 또한 공개망에 배포되는 `/admin/login`은 무차별 대입 방어가 없다.
- 결정:
  - 관리자 웹: 로그인 외 요청이 401을 받으면 토큰을 지우고 로그인 화면으로 복귀하며 "세션 만료" 안내를 1회 표시한다 (`admin/src/api.ts`).
  - 서버: 클라이언트 IP당 실패 5회(10분 창) 시 10분 잠금 — 429 + `Retry-After` (`app/domain/login_guard.py`). 성공 로그인은 카운터를 초기화한다.
  - 잠금 상태는 프로세스 메모리에만 둔다(단일 인스턴스 전제). 수평 확장 시 공유 저장소로 승격.
- 금지: 401 응답을 무시한 채 폴링 지속, 로그인 엔드포인트 잠금 없이 공개망 배포.

## ADR-015: 랭킹은 설치별 관심 게임 관계를 집계한다
- 근거: 관리자 입력값이나 미리보기 점수는 실제 사용자 선택을 반영하지 않아
  랭킹 신뢰를 훼손한다. 회원가입 없는 앱에서도 설치 단위의 선택은 서버가
  중복 없이 집계할 수 있다.
- 결정:
  - `installation_games(installation_id, game_id)` 복합키로 관심 등록을 저장한다.
  - 공개 랭킹은 `revoked_at IS NULL` 설치의 `COUNT(DISTINCT installation_id)`를
    내림차순 집계하고, 동률은 게임명·ID로 결정적으로 정렬한다.
  - 기존 `game_ids_json`은 구버전 응답 호환 및 마이그레이션 원본으로만 유지한다.
  - 설치 환경설정은 최대 8개로 제한하며, 비활성·삭제된 게임 ID는 집계에서 제외한다.
- 금지: 공개 랭킹에서 `games.interest_count` 수동값을 사용자 수처럼 표시하거나,
  기기 토큰 수를 사용자 수로 오인하는 것.

## ADR-016: 권리 검토 전 게임은 공개 후보에서 보류한다
- 근거: 게임명만 제공하는 것과 공식 이미지·콘텐츠를 재배포하는 것은 별개의 권리 문제다.
  초기 출시에서 확인되지 않은 소스를 늘리면 운영자가 삭제 요청과 출처를 추적하기 어렵다.
- 결정: 현재 미리보기·개발 시드에서는 젠레스 존 제로와 명조를 비활성화하고,
  기존 DB 기록은 삭제하지 않는다. 공식 API/RSS·이미지 사용 범위와 약관을 확인한 뒤
  관리자에서 다시 활성화한다.
- 금지: 권리 확인 전 외부 이미지 핫링크·본문 재게시·자동 발행.
