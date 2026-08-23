# GamePickup (PIKY) 포트폴리오 정리

## 프로젝트 개요

관심 게임의 업데이트와 이벤트를 한곳에서 확인하고, 내가 고른 게임만 모아볼 수 있는 Android 우선 앱입니다.

콘텐츠는 자동 수집 단계에서 바로 공개하지 않습니다. 수집된 글은 초안으로 저장하고 운영자가 검수한 뒤 발행하도록 구성했습니다.

## 해결한 문제

- 게임별 공식 소식이 여러 채널에 나뉘어 있어 필요한 정보만 골라 보기 어려웠습니다.
- 자동 수집 데이터를 바로 노출하면 잘못된 링크나 중복 글이 섞일 수 있었습니다.
- 로그인 없이도 사용하되, 기기별 관심 게임과 알림 설정은 유지해야 했습니다.

## 구조

```text
모바일 앱 ─┐
관리자 웹 ─┼→ FastAPI → Service → Domain → Repository → SQLite/PostgreSQL
자동 수집 ─┘                 └→ Push Outbox → 발송 워커
```

- 모바일 앱: Expo, React Native, TypeScript, Expo Router
- API: FastAPI, SQLAlchemy, Pydantic
- 관리자: Vite, React, TypeScript
- 인증: 관리자 JWT, Ingest Key, 설치 단위 secret
- 상태 전이: `draft → reviewed → published`

## 주요 흐름

1. RSS나 외부 수집기가 `X-Ingest-Key`로 소식을 등록합니다.
2. API는 수집 글을 반드시 `draft`로 저장합니다.
3. 관리자가 내용을 확인하고 `reviewed`로 변경합니다.
4. 발행된 글만 모바일 공개 API에서 조회됩니다.
5. 발행 알림은 같은 트랜잭션에서 outbox에 기록하고 별도 발송 작업에서 처리합니다.

## 데이터 모델

핵심 테이블은 `games`, `contents`, `installations`, `device_tokens`, `push_outbox`, `announcements`, `inquiries`입니다.

설치 단위 인증을 사용하므로 회원 테이블을 두지 않았습니다. 설치 secret은 원문을 저장하지 않고 해시로 보관합니다.

## API

| 영역 | Method | Endpoint | 설명 |
| --- | --- | --- | --- |
| Public | GET | `/api/v1/games` | 게임 목록 |
| Public | GET | `/api/v1/contents` | 발행 소식 |
| Public | GET | `/api/v1/rankings` | 관심 게임 순위 |
| Public | POST | `/api/v1/installations` | 설치 credential 발급 |
| Public | POST | `/api/v1/inquiries` | 문의 등록 |
| Admin | POST | `/api/v1/admin/login` | 관리자 로그인 |
| Admin | POST | `/api/v1/admin/contents` | 소식 등록 |
| Admin | POST | `/api/v1/admin/push/dispatch` | 알림 outbox 처리 |
| Ingest | POST | `/api/v1/ingest/contents` | 검수 전 초안 등록 |

## 실행

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pytest -q
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

모바일 앱과 관리자 웹 실행 방법은 루트 README를 따릅니다.

## 문서 파일

- [앱 아키텍처](./ARCHITECTURE.md)
- [백엔드 아키텍처](./BACKEND_ARCHITECTURE.md)
- [draw.io 시스템 아키텍처](./diagrams/pickup-architecture.drawio)
- [draw.io 발행 흐름](./diagrams/pickup-flow.drawio)
- [draw.io ERD](./diagrams/pickup-erd.drawio)
