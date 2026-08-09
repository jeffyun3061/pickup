# GamePickup (PIKY)

Android 우선 게임 소식 앱 + 운영 API + 관리자 웹.

UI는 Stitch **Neon-Tactical** 시안. 콘텐츠는 운영 검수·발행 후 API로 채워진다.

## 왜 이렇게 만들었나 (면접용 한 줄)

화면은 공통 컴포넌트 + 디자인 토큰으로만 조립하고, 데이터는 `CatalogRepository` 뒤로 숨긴다.  
백엔드는 **Public / Admin JWT / Ingest Key**로 권한을 나누고, 소식은 **상태 머신**(`draft→reviewed→published`)으로만 발행한다.

## 구조

```text
app/                 Expo Router 화면
src/                 컴포넌트·도메인·data·theme
server/              FastAPI (Controller→Service→Domain→Repository)
admin/               관리자 웹 (Vite + React)
docs/                DECISIONS · ARCHITECTURE · BACKEND_ARCHITECTURE
design-ref/          시안 DESIGN.md / HTML
```

근거: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/BACKEND_ARCHITECTURE.md](docs/BACKEND_ARCHITECTURE.md) · [docs/DECISIONS.md](docs/DECISIONS.md)

## 실행

### 모바일
```powershell
cd C:\Users\user\Projects\pickup
npm install
npm run verify
npm run android
```

실연동: `EXPO_PUBLIC_CATALOG_MODE=api`, `EXPO_PUBLIC_API_URL=http://<PC_IP>:8000`

### API
```powershell
cd server
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
# .env.example → .env 후 ADMIN_PASSWORD_HASH / JWT_SECRET / INGEST_API_KEY
.\.venv\Scripts\pytest -q
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

### 관리자 웹
```powershell
cd admin
npm install
npm run dev
```

## 데이터 정책

- 앱 유저 로그인 없음
- 관리자만 쓰기 / 자동화(Ingest)는 draft만
- `preview` 모드는 시안 퀄리티 검증용
