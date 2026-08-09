# GamePickup API (`server/`)

모듈형 모놀리스. 설계 근거: `../docs/BACKEND_ARCHITECTURE.md`, ADR-009.

## 역할

| 역할 | 인증 | 할 일 |
|------|------|--------|
| Public | 없음 | 발행 조회, 문의 |
| Admin | JWT | CRUD·검수·발행 |
| Ingest | `X-Ingest-Key` | draft만 |

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
