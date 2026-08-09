# GamePickup API (`server/`)

모듈형 모놀리스. 설계 근거: `../docs/BACKEND_ARCHITECTURE.md`, ADR-009·010.

## 역할

| 역할 | 인증 | 할 일 |
|------|------|--------|
| Public | 없음 | 발행 조회, 문의 |
| Installation | `X-Installation-Id` + `X-Installation-Secret` | device token·preference |
| Admin | JWT | CRUD·검수·발행·outbox dispatch |
| Ingest | `X-Ingest-Key` | draft만 |

## 푸시 계약 (인프라 제외)

1. 앱: `POST /api/v1/installations` → SecureStore 저장  
2. 앱: token·preferences 등록  
3. Admin이 Content를 `published`로 전이 → **같은 트랜잭션에서 outbox enqueue**  
4. `POST /api/v1/admin/push/dispatch` → 스텁 발송(`sent`). 실서비스는 FCM 워커로 교체

## 로컬 실행

```powershell
cd C:\Users\user\Projects\pickup\server
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python scripts\make_password_hash.py YOUR_PASSWORD
# .env.example 을 .env 로 복사 후 ADMIN_PASSWORD_HASH / JWT_SECRET / INGEST_API_KEY 채우기
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

- OpenAPI: http://127.0.0.1:8000/docs

## 테스트

```powershell
cd C:\Users\user\Projects\pickup\server
.\.venv\Scripts\pytest -q
```

## 자동화 ingest 예시

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/ingest/contents `
  -H "X-Ingest-Key: YOUR_INGEST_KEY" `
  -H "Content-Type: application/json" `
  -d '{"game_id":"g_xxx","title":"초안","summary_points":["a"],"idempotency_key":"rss-1"}'
```
