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
