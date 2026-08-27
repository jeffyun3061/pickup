# GamePickup API (`server/`)

모듈형 모놀리스. 설계 근거: `../docs/BACKEND_ARCHITECTURE.md`, ADR-009·010.

## 역할

| 역할 | 인증 | 할 일 |
|------|------|--------|
| Public | 없음 | 발행 조회, 문의 |
| Installation | `X-Installation-Id` + `X-Installation-Secret` | device token·preference |
| Admin | JWT | CRUD·검수·발행·outbox dispatch |
| Ingest | `X-Ingest-Key` | 수집 작업 claim·draft 생성·실행 결과 기록 |

## 푸시 계약 (인프라 제외)

1. 앱: `POST /api/v1/installations` → SecureStore 저장  
2. 앱: token·preferences 등록  
3. Admin이 Content를 `published`로 전이 → **같은 트랜잭션에서 outbox enqueue**  
4. `POST /api/v1/admin/push/dispatch` → 개발에서는 스텁, 운영에서는 Expo Push API 실발송

## 공개 상태·랭킹

- `GET /health/live` — 프로세스 생존 확인
- `GET /health/ready` — DB 연결을 포함한 트래픽 수신 가능 여부
- `GET /api/v1/rankings` — 활성 설치의 관심 게임 등록 수(`installation_games`) 기준
  랭킹. 관리자 수동 점수는 공개 집계에 사용하지 않는다.
- `GET /api/v1/contents?scope=mine&game_ids=...&limit=...` — 발행 소식. 기본 100건,
  최대 200건으로 제한한다.

## 로컬 실행

```powershell
cd C:\Users\user\Projects\pickup
cd server
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python scripts\make_password_hash.py YOUR_PASSWORD
# .env.example 을 .env 로 복사 후 ADMIN_PASSWORD_HASH / JWT_SECRET / INGEST_API_KEY 채우기
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

Docker를 사용하지 않는 1인 개발 환경에서는 개발 의존성의 PostgreSQL
실행 스크립트를 사용할 수 있다. `server/tmp/gamepickup-postgres`에 데이터가
보존되며, 운영 PostgreSQL이나 SQLite로 바꾸지 않는다.

```powershell
cd C:\Users\user\Projects\pickup\server
.\.venv\Scripts\pip install -r requirements-dev.txt
.\.venv\Scripts\python scripts\run_local_pg_api.py
```

Docker Compose는 CI 이미지 스모크와 나중의 컨테이너 배포 검증을 위해 남겨둔다.

로컬·CI·운영은 모두 PostgreSQL을 사용한다. SQLite는 지원하지 않는다.

- OpenAPI: 개발 환경에서만 http://127.0.0.1:8000/docs 제공 (운영에서는 `/docs`, `/redoc`, `/openapi.json` 비공개)

## 테스트

```powershell
cd C:\Users\user\Projects\pickup\server
.\.venv\Scripts\python scripts\run_tests_pg.py
```

## 자동화 ingest 예시

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/ingest/contents `
  -H "X-Ingest-Key: YOUR_INGEST_KEY" `
  -H "Content-Type: application/json" `
  -d '{"game_id":"g_xxx","title":"초안","summary_points":["a"],"idempotency_key":"rss-1"}'
```

## RSS·공식 API 자동 수집

1. Admin 웹의 `자동 수집`에서 소스를 등록한다.
2. collector를 API와 별도 프로세스로 실행한다.

```powershell
cd C:\Users\user\Projects\pickup
$env:INGEST_SERVER_URL="http://127.0.0.1:8000"
$env:INGEST_API_KEY="<server .env와 동일>"
.\server\.venv\Scripts\python -m collector.runner
```

수집 결과는 앱에 즉시 노출되지 않는다. Admin의 `소식 관리`에서 원문을 확인하고 `초안 → 검수 완료 → 발행`해야 한다.

collector가 비정상 종료되어 `running`으로 남은 작업은 기본 45분 후 실패 처리되고
지수 백오프로 다시 예약된다. 운영에서 변경하려면 `INGEST_STALE_AFTER_MINUTES`를 설정한다.
