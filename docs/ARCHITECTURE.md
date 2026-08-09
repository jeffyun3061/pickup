# GamePickup 아키텍처

취업·포트폴리오 설명용 요약. “왜 이렇게 나눴는지”가 핵심이다.

## 한 줄 구조

```text
app/ (화면·라우팅)
  → hooks/ (화면용 조립)
    → state/ (설치 로컬 설정)
    → data/ (CatalogRepository 구현체)
      → domain/ (순수 타입·규칙)
  → components/ + theme/ (시안 토큰 UI)
  → assets/ (fonts.ts · images.ts 인덱스 매핑)
```

## 계층 역할

| 계층 | 책임 | 하지 않는 것 |
|---|---|---|
| `app/` | 라우트, 화면 조합, 네비게이션 | API URL 하드코딩, 스타일 복제 |
| `components/` | 재사용 UI (헤더/탭/카드/Empty) | 비즈니스 규칙, fetch |
| `hooks/` | Repository + AppState 조합 | JSX 스타일 난립 |
| `state/` | 온보딩·선택 게임·알림 3종 | 서버 소식 캐시(추후 쿼리층), secret 저장 |
| `data/` | CatalogRepository / preferencesStore / credentialStore | UI 컴포넌트 |
| `domain/` | 타입, kind 라벨, 날짜 포맷 | React / Expo API |
| `theme/` | Stitch 토큰·레이아웃 스케일 | 화면별 예외 색 |

## 확장 지점 (실서비스)

1. **콘텐츠 공급**: `EmptyCatalogRepository` → `ApiCatalogRepository`로 교체만 하면 UI는 동일.
2. **인증**: 사용자 로그인 없음.
   - 비민감 설정: `preferencesStore` (AsyncStorage)
   - 설치 secret: `credentialStore` (SecureStore) — API 연동 시 헤더에만 사용
3. **운영**: 관리자 웹/외부 수집기는 같은 도메인 모델(`ContentItem`, `draft→reviewed→published`)을 쓴다.
4. **알림**: 설정 3종만 저장. 발송은 서버 outbox/Cron 책임.

## 반응형 원칙 (Android)

- 기준 폭: 360 / 393 / 412 dp
- `useLayout()`이 margin·thumb·탭 라벨·타이포 스케일을 내려준다
- 카드 텍스트는 `flexShrink` + `numberOfLines`로 줄바꿈/말줄임
- 하단 탭은 `minWidth: 0` + compact 시 짧은 라벨

## 검증

```powershell
npm run verify   # tsc + vitest
npm run android  # 에뮬레이터 Fast Refresh
```

근거 결정: `docs/DECISIONS.md`  
UI 시안: `design-ref/DESIGN.md`
