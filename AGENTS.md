# GamePickup 작업 규칙

## 작업 루트
`C:\Users\user\Projects\pickup` 한 폴더만 사용한다.

## UI 근거
- 시안: `design-ref/DESIGN.md` + Stitch HTML
- 결정 로그: `docs/DECISIONS.md`
- 카탈로그: `src/data/catalog.ts` (`preview` 기본 / `empty` 전환)
- 금지: 실 IP 게임명·공식 로고 하드코딩, 시안 밖 테마

## 검증
```powershell
cd C:\Users\user\Projects\pickup
npm run verify
npm run android
```

## 포트폴리오 설명 포인트
- UI/데이터 분리: CatalogRepository (`preview` / `empty` / `api`)
- 백엔드: Public / Admin JWT / Ingest Key / Installation 최소 권한 (ADR-009·010)
- Content 상태머신 draft→reviewed→published, publish→push outbox
- 시안 근거: design-ref + DECISIONS ADR
- 반응형: resolveLayout(360/393/412)

## 백엔드
```powershell
cd C:\Users\user\Projects\pickup\server
.\.venv\Scripts\pip install -r requirements-dev.txt
.\.venv\Scripts\python scripts\run_tests_pg.py
.\.venv\Scripts\python scripts\run_local_pg_api.py
cd ..\admin
npm run dev
```
앱 실연동: `EXPO_PUBLIC_CATALOG_MODE=api`, `EXPO_PUBLIC_API_URL=http://<host>:8000`

로컬 개발은 Docker를 요구하지 않는다. `run_local_pg_api.py`가 PostgreSQL을
`server/tmp/gamepickup-postgres`에 실행한다. 컨테이너 실행 형태가 필요하면 루트에서
`docker compose up --build`로 API와 PostgreSQL을 함께 검증하고, Dockerfile/Compose는
CI와 운영 컨테이너 배포에도 재사용한다. 운영 DB는 관리형 PostgreSQL을 사용한다.

## 원칙
- Expo Router + TypeScript
- CatalogRepository 경계로 데이터 교체
- 앱 유저 로그인 없음 / 관리자·ingest만 쓰기
- 저장소 분리: 환경설정=AsyncStorage, 설치 secret=SecureStore (ADR-007)
- Controller→Service→Domain→Repository
- 임시 우회로 “일단 동작”을 만들지 않는다
- 커밋은 사용자가 직접 한다
