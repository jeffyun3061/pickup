# GamePickup Backend Architecture

면접·실서비스 설명용. “왜 이 구조인가”가 핵심이다.

## 1. 한 줄 요약

**모듈형 모놀리스(FastAPI)** 위에서  
**공개 읽기 / 관리자 쓰기 / 자동화 초안(ingest) / 설치 쓰기** 경계를 인증·유스케이스로 분리한다.

앱 유저 로그인 없음 ≠ 보안 없음.  
권한은 **역할(Role) 단위**로 나눈다.

| 역할 | 주체 | 인증 | 할 수 있는 일 |
|------|------|------|----------------|
| Public | 모바일 앱 | 없음 | 발행 콘텐츠 조회, 문의 등록 |
| Admin | 운영자(나) | Username + password hash → JWT | CRUD, 검수·발행, 문의 처리 |
| Ingest | RSS/AI 자동화 | `X-Ingest-Key` | **draft 생성만** (발행 불가) |
| Installation | 모바일 앱 설치 | 설치 ID + secret | 기기 토큰·알림 환경설정 |

---

## 2. 왜 모듈형 모놀리스인가

| 선택지 | 채택 여부 | 이유 |
|--------|-----------|------|
| 마이크로서비스 | ❌ 초기 비채택 | 팀 1인·트래픽 작음. 네트워크/배포 복잡도만 증가 |
| 빅볼 오브 머드 | ❌ | Controller에 SQL·권한·상태전이 섞이면 면접·유지보수 불가 |
| **모듈형 모놀리스** | ✅ | 한 배포 단위 + 내부는 계층·모듈로 경계. 나중에 서비스 분리 가능 |

면접 한 줄:  
“지금은 모놀리스로 빠르게 일관된 트랜잭션을 보장하고, **모듈 경계**를 미리 그어 확장 비용을 낮춘다.”

---

## 3. 계층 (의존성 방향은 안쪽으로만)

```text
api/            Controller  — HTTP, DTO 검증, 상태코드
  ↓
services/       Application — 유스케이스, 트랜잭션 경계, 권한 규칙 호출
  ↓
domain/         Domain      — 엔티티 규칙, 상태 머신, 순수 함수 (프레임워크 독립)
  ↓
repositories/   Infrastructure — SQLAlchemy 영속화
```

### 각 계층이 하지 않는 것

| 계층 | 책임 | 금지 |
|------|------|------|
| Controller | 라우팅, Request/Response, auth dependency 주입 | 비즈니스 if문, SQL |
| Service | 유스케이스 오케스트레이션 | FastAPI Request 객체 직접 의존 |
| Domain | 상태 전이·불변식 | DB 세션, HTTP |
| Repository | CRUD / 쿼리 | 상태 머신 판단 (“발행해도 되나?”) |

**재사용성**: 같은 `ContentService.publish()`를 Admin API·향후 배치가 공유.  
**테스트**: Domain은 단위 테스트, Service는 가짜 Repository로 유스케이스 테스트.

---

## 4. 도메인 모델 · 자료구조

### 4.1 핵심 Aggregate

```text
Game (게임 카탈로그)
  └─ Content[]  (소식)  — game_id FK, status, kind, published_at

Announcement (서비스 공지) — Content와 분리 (게임 비종속 운영 메시지)
Inquiry (문의) — 앱→운영 단방향, 로그인 없이 생성
IngestSource ── IngestRun[] — RSS/API 설정과 실행 이력
```

### 4.2 Content 상태 머신 (알고리즘·규칙의 핵심)

허용 전이만 Domain에 둔다. 임의 `status = published` 대입 금지.

```text
draft ──review──▶ reviewed ──publish──▶ published
  ▲                  │
  └────reject────────┘   (수정 필요 시 draft로 복귀 가능)

published ──unpublish──▶ reviewed   (실수 발행 회수)
```

| 전이 | 부수 효과 | 이유 |
|------|-----------|------|
| publish | `published_at = now()` (최초 1회) | 앱 정렬·“최신” 기준 일관성 |
| ingest 생성 | 무조건 `draft` | 자동화는 검수 전제 |
| 자동 발행 (ADR-012) | 서버 백그라운드가 draft→reviewed→published 전이 대행 | ingest 키에 발행 권한을 주지 않고도 신뢰 소스 속도 확보 |

면접: “상태 머신을 코드로 강제해 **잘못된 발행**을 컴파일/런타임에 막는다.”

### 4.5 수집→발행 파이프라인 (ADR-012)

```text
collector (X-Ingest-Key)                 server
──────────────────────                   ──────────────────────────────
jobs/claim ◀── 소스 + http_cache
목록 조건부 GET (ETag/해시)
  변화 없음 → complete(not_modified)
파싱 → contents/check (새 글만)
새 글 상세 fetch (robots 허용 시)
contents 제출 (raw_text 포함)  ──▶      draft 저장 (201)
                                         └ BackgroundTasks:
                                             LLM 3줄 요약 + 종류 분류
                                             auto_publish 소스면 상태 전이 + push outbox
complete(건수, http_cache)     ──▶      health 갱신 (연속 실패/0건 감지)
```

요약 실패 건은 `summary_status=failed`인 draft로 남아 관리자 검수로 폴백한다.

### 4.3 조회·인덱스 (시간·공간)

| 쿼리 | 자료구조/인덱스 | 복잡도 목표 |
|------|-----------------|-------------|
| 발행 피드 최신순 | `(status, published_at DESC)` | O(log n + k) |
| 마이픽 필터 | `game_id IN (...)` + 위 인덱스 | 선택적 인덱스 `game_id` |
| 랭킹 | `installation_games` + 활성 설치 distinct count DESC | O(games + picks) / 이후 집계 뷰 |
| Ingest 멱등 | `idempotency_key UNIQUE` | 중복 insert 방지 O(1) 조회 |

**랭킹 알고리즘 (현재)**: `installation_games`에서 `revoked_at IS NULL`인 설치를
게임별 `COUNT(DISTINCT installation_id)`로 집계하고, 같은 수는 게임명·ID로
결정적으로 정렬한다. `games.interest_count`는 기존 시드/관리자 API 호환용이며
공개 랭킹과 관리자 카탈로그의 등록 수에는 사용하지 않는다. 데이터가 커지면 주기 집계 테이블로 교체해도
**Public API 계약은 동일**하다.

### 4.4 Ingest 멱등성

자동화는 재시도한다. 같은 페이로드를 두 번내면 안 된다.

- 클라이언트: `Idempotency-Key` 또는 body `external_id`
- 서버: UNIQUE 제약 + 동일 키면 기존 draft 반환 (201 vs 200 정책 문서화)

---

## 5. API 경계 (계약 우선)

```text
GET  /api/v1/games|contents|rankings|announcements   ← Public, published only (contents 기본 100건·최대 200건)
POST /api/v1/inquiries                               ← Public, rate limit 대상

POST /api/v1/installations                           ← 설치 발급 (secret 1회)
PUT  /api/v1/installations/me/device-token           ← Installation secret
PUT  /api/v1/installations/me/preferences            ← Installation secret

POST /api/v1/admin/login                             ← Admin 자격 → JWT
*    /api/v1/admin/**                                ← Bearer JWT
POST /api/v1/admin/push/dispatch                     ← outbox 디스패치(개발 스텁/운영 Expo)

POST /api/v1/ingest/contents                         ← X-Ingest-Key, draft only
POST /api/v1/ingest/contents/check                   ← 수집된 멱등 키 사전 조회
POST /api/v1/ingest/jobs/claim                       ← collector 작업 claim (+http_cache)
POST /api/v1/ingest/jobs/{id}/complete               ← 성공·실패·건수·캐시 기록

CRUD /api/v1/admin/ingest-sources                     ← Admin 소스 설정 (rss/api/html)
POST /api/v1/admin/ingest-sources/dry-run             ← 저장 전 테스트 수집
GET  /api/v1/admin/ingest-runs                        ← Admin 실행 이력
POST /api/v1/admin/contents/from-url                  ← URL 빠른 등록 (+AI 요약)
POST /api/v1/admin/contents/{id}/summarize            ← AI 요약 재실행
```

### 왜 Admin JWT와 Ingest Key를 나누나

| | Admin JWT | Ingest Key |
|--|-----------|------------|
| 유출 시 | 전 권한 위험 → 짧은 TTL·로테이션 | draft만 → 피해 제한 |
| 주체 | 사람(웹) | 기계(Cron/스크립트) |
| 면접 포인트 | 최소 권한 원칙(Principle of Least Privilege) | |

앱에 Admin 비밀번호를 넣지 않는다 (ADR-009).

---

## 5-1. 앱과 운영 도구의 장애 경계

모바일 앱은 관리자 웹이나 collector를 호출하지 않는다. 앱이 사용하는 유일한 쓰기 경로는
설치 단위 설정·푸시 토큰이고, 소식·게임·랭킹은 Public API의 `published` 데이터만 읽는다.
따라서 다음 상태에서도 이미 발행된 소식은 계속 표시된다.

| 상태 | 앱 동작 | 운영 대응 |
|------|---------|-----------|
| collector 중단 | 기존 발행분 표시, 새 소식만 늦어짐 | 관리자 웹에서 URL 수동 등록 → 검수 → 발행 |
| 관리자 웹 장애 | 앱은 정상, 자동 수집 초안도 API에 남음 | Admin API를 이용해 수동 등록하거나 웹 복구 |
| API 일시 장애 | 마지막 카탈로그 스냅샷을 오프라인 표시 | `/health/ready` 복구 후 앱 새로고침 |
| PostgreSQL 장애 | 새 읽기·쓰기는 중단 | Railway 백업 복구 및 readiness 확인 |

자동 수집은 편의 기능이고 앱의 런타임 의존성이 아니다. 수동 등록도 동일한
`draft → reviewed → published` 상태 머신과 공식 원문 URL 검증을 거치므로, collector를
나중에 교체하거나 완전히 끄더라도 모바일 계약은 변경하지 않는다.

---

## 6. 패키지 목표 구조 (리팩터 타깃)

```text
server/
  app/
    main.py                 # composition root (라우터 조립만)
    config.py               # pydantic-settings, 시크릿은 env만
    api/                    # Controllers
      public.py
      admin/
      ingest.py
      deps.py               # auth dependencies
    domain/
      content_status.py     # 상태 머신 (순수)
      ids.py                # id 생성 규칙
    services/               # use cases
      catalog_service.py
      content_command_service.py
      game_command_service.py
      auth_service.py
      inquiry_service.py
    repositories/           # SQL 어댑터
    models/                 # ORM entities (인프라 모델)
    schemas/                # Pydantic DTO (입출력 검증)
  tests/
    domain/
    services/
  docs 연계: DECISIONS ADR-009, 본 문서
collector/
  connectors/               # RSS / JSON API 외부 어댑터
  runner.py                 # 별도 polling 프로세스
admin/
  src/pages/IngestSourcesPage.tsx
```

ORM 모델 ≠ Domain 규칙:  
규칙은 `domain/`에, 테이블 매핑은 `models/`에.  
지금은 모놀리스라 파일을 나눈 것이고, 나중에 Domain Entity를 순수 dataclass로 승격해도 경계는 유지된다.

---

## 7. 트랜잭션 · 일관성

- **쓰기 유스케이스 1개 = DB 트랜잭션 1개** (Service 종료 시 commit)
- publish 시 Content 행만 갱신 (앱은 다음 조회로 일관 — read your writes 불필요)
- 문의 생성은 별 aggregate, Content와 트랜잭션 공유 안 함

---

## 8. 보안 체크리스트 (실서비스)

1. 시크릿 하드코딩 금지 (`ADMIN_PASSWORD_HASH`, `JWT_SECRET`, `INGEST_API_KEY`)
2. 비밀번호는 bcrypt 해시만 저장 (평문 비교 금지)
3. Public 문의: IP/키 기반 rate limit (남용 방지)
4. CORS allowlist (관리자 origin만 credentials)
5. Ingest는 draft만 — 발행은 Admin 검수 후
6. SQLAlchemy 파라미터 바인딩 (SQL injection 기본 방어)
7. DB 엔진은 모든 환경에서 PostgreSQL로 통일한다. 로컬 Docker·CI 임베디드·운영 Railway는
   서로 다른 인스턴스이며 `DATABASE_URL`만 환경별로 주입한다.
8. 수집 URL은 공개 HTTP(S)만 허용하고 private/reserved IP 차단
9. 외부 API secret은 collector 환경변수에만 저장

---

## 9. 확장 로드맵 (과설계 없이)

| 단계 | 내용 | 계층 영향 |
|------|------|-----------|
| Now | CRUD + 상태머신 + Admin/Ingest/Public/Installation + outbox + RSS/API collector | 현재 구조 |
| Now/운영 전환 | Expo Push API 실발송 활성화 · collector 배포 | PushService/운영 환경변수 |
| Later | 읽기 전용 replica / 랭킹 집계 잡 | Repository 교체 |
| Optional | Admin을 별도 서비스로 분리 | api/admin만 이사 |

**2회 이상 반복될 때만 공통화** (사용자 규칙).  
미래를 위한 추상 인터페이스 남발 금지. Protocol은 **테스트 교체·구현 2개 이상**일 때.

---

## 10. 면접에서 말할 스토리 (60초)

1. 앱은 로그인 없이 **발행분 조회**만 한다.  
2. 운영 쓰기는 **Admin JWT**, 자동화는 **Ingest Key(draft only)** 로 최소 권한을 나눈다.  
3. 콘텐츠는 **상태 머신**으로 검수 없이 발행되지 못하게 한다.  
4. 구조는 Controller→Service→Domain→Repository 라서 UI/자동화/웹이 **같은 유스케이스**를 재사용한다.  
5. 모놀리스로 시작하되 모듈 경계를 지켜 **유지보수·확장** 비용을 통제한다.

---

## 11. 관련 ADR

- ADR-002: 앱은 Repository 경계로 API 교체
- ADR-007: 앱 로컬 민감/비민감 저장 분리
- ADR-009: 백엔드 Admin / Ingest / Public 분리
