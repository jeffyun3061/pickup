# GamePickup Collector

관리 콘솔에 등록한 RSS·JSON API·HTML 크롤 소스를 가져와 Ingest API에 **draft**로 넣는 별도 프로세스다. 관리자 JWT나 발행 권한을 갖지 않는다. (자동 발행 전이는 서버가 수행 — ADR-012)

## 실행

```powershell
cd C:\Users\user\Projects\pickup
.\server\.venv\Scripts\pip install -r collector\requirements.txt
$env:INGEST_SERVER_URL="http://127.0.0.1:8000"
$env:INGEST_API_KEY="<server와 같은 값>"
.\server\.venv\Scripts\python -m collector.runner
```

작업 하나만 처리하려면 `--once`를 붙인다. 처리할 작업이 없으면 즉시 종료한다.

## 동작 순서 (소스 1개 = 잡 1개)

1. `POST /ingest/jobs/claim` — 실행할 소스와 저장된 HTTP 캐시(etag 등)를 받는다.
2. 목록 페이지 조건부 GET — 304 또는 본문 해시 동일이면 파싱 없이 `not_modified`로 종료.
3. 커넥터 파싱 → `POST /ingest/contents/check`로 이미 수집된 글을 제외.
4. **새 글만** 상세 페이지에서 본문 추출(robots.txt 허용 시, 기본 최신 10건, 요청 간 1초 대기).
5. `POST /ingest/contents` 제출 → 서버가 백그라운드에서 AI 요약·자동 발행을 처리.
6. `POST /ingest/jobs/{run}/complete` — 결과와 갱신된 HTTP 캐시 보고.

## 소스 config 키

공통: `kind`(update|event|popup|goods), `max_items`, `fetch_detail`(false로 끄기),
`max_detail_fetches`, `fetch_delay_seconds`, `detail_selector`(상세 본문 위치)

- **JSON API**: `items_path`(`data.articles`), `id_field`, `title_field`, `url_field`,
  선택 `summary_field`, `image_field`, `published_field`, `auth_header`, `auth_prefix`.
  인증 토큰은 콘솔에 `secret_env_name`만 저장하고 실제 값은 collector 환경변수로 주입한다.
- **HTML 크롤**: `list_selector`(필수), 선택 `title_selector`, `url_selector`/`url_attr`,
  `id_selector`/`id_attr`, `summary_selector`, `image_selector`/`image_attr`,
  `date_selector`/`date_attr`. 관리 콘솔의 "테스트 수집"으로 저장 전에 검증한다.
  - JS 렌더 목록: `render_js=true`, `wait_selector`, 선택 `render_timeout_seconds`(기본 20초).
    Playwright Chromium으로 공개 DOM을 렌더링하며 이미지·미디어·폰트는 받지 않는다.
    API 서버 dry-run 대신 저장 후 관리 콘솔의 **지금 실행**으로 확인한다.

자동 실행 시간 제한(모든 타입 공통): `active_start_hour`, `active_end_hour`,
`utc_offset_hours`. 예: `8` / `22` / `9`이면 한국시간 08:00~22:00에만 자동 실행한다.
시작과 종료가 같거나 둘 중 하나가 없으면 24시간 실행하며 수동 실행은 제한을 우회한다.

## 크롤 예의

- robots.txt를 24시간 캐시로 확인하고, `Disallow` 또는 `401/403`으로 접근을 거부한
  URL은 건너뛴다 (HTML 목록·상세 공통). `404`(파일 없음)만 허용으로 처리한다.
- `COLLECTOR_USER_AGENT`로 식별하며, 상세 fetch는 실행당 상한과 간격이 있다.
- SSRF 방지: 사설/내부 IP로 해석되는 URL은 요청 자체를 거부한다.
