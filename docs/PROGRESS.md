# 진행 현황 · 출시 체크리스트

작업 루트: `C:\Users\user\Projects\pickup`  
기준일: 2026-08-09

범례: `[x]` 완료 · `[~]` 부분 · `[ ]` 미착수

---

## 1. 모바일 앱 (Expo)

| 항목 | 상태 | 비고 |
|------|------|------|
| Neon-Tactical UI + PIKY 헤더/탭 | [x] | 5탭: 뉴스·마이픽·홈·랭킹·설정 |
| Preview / Empty 카탈로그 | [x] | `EXPO_PUBLIC_CATALOG_MODE` |
| ApiCatalogRepository 연동 코드 | [x] | `api` 모드 + `EXPO_PUBLIC_API_URL` |
| 마이픽 2×2 + 게임 등록 슬롯 | [x] | |
| 온보딩 · 알림 토글 로컬 저장 | [x] | AsyncStorage (ADR-007) |
| SecureStore credential 계층 | [x] | 키 저장 골격만, 서버 등록 미연동 |
| 문의하기 → API | [x] | `POST /api/v1/inquiries` |
| 소식/공지 상세 화면 | [x] | |
| 실기기에서 API 모드 검증 | [~] | LAN IP·배포 URL로 재확인 필요 |
| 푸시 알림 수신 | [ ] | FCM + 토큰 등록 |
| 스플래시/아이콘 최종 브랜드 | [~] | 기본 Expo 에셋 수준 |
| Android 릴리스 빌드 (EAS/AAB) | [ ] | |
| Play Store 등록 정보 | [ ] | |

## 2. 백엔드 API (`server/`)

| 항목 | 상태 | 비고 |
|------|------|------|
| FastAPI 계층 구조 | [x] | Controller→Service→Domain→Repository |
| Public 조회 + 문의 | [x] | published만 |
| Admin JWT 로그인/CRUD/발행 | [x] | |
| Ingest draft 전용 | [x] | `X-Ingest-Key` + idempotency |
| Content 상태머신 | [x] | draft→reviewed→published |
| pytest | [x] | 9 passed |
| SQLite 로컬 개발 | [x] | |
| PostgreSQL 프로덕션 | [ ] | `DATABASE_URL` |
| 시크릿 로테이션 · 프로덕션 `.env` | [ ] | admin 비밀번호/JWT/ingest 키 |
| HTTPS 배포 (API 호스팅) | [ ] | |
| 문의 rate limit | [ ] | 남용 방지 |
| 이미지 업로드/CDN | [ ] | 지금은 URL 문자열 |
| 관측성 (로그·헬스·에러) | [~] | 기본 FastAPI만 |
| DB 마이그레이션 도구 | [ ] | Alembic 등 |

## 3. 관리자 웹 (`admin/`)

| 항목 | 상태 | 비고 |
|------|------|------|
| 로그인 | [x] | |
| 게임 CRUD | [x] | |
| 소식 상태 전이 (검수·발행) | [x] | |
| 문의 닫기 | [x] | |
| UX/권한·모바일 대응 다듬기 | [~] | 최소 동작 |
| 프로덕션 빌드·호스팅 | [ ] | |
| HTTPS + API 프록시 | [ ] | |

## 4. 콘텐츠·운영

| 항목 | 상태 | 비고 |
|------|------|------|
| 수동 발행 플로우 | [x] | admin으로 가능 |
| RSS/AI ingest 파이프라인 | [ ] | API만 준비됨 |
| 실 게임 카탈로그·썸네일 권리 | [ ] | 픽션 preview만 |
| 출시용 시드 콘텐츠 N건 | [ ] | |
| 문의 대응 루틴 | [~] | admin에서 확인 가능 |

## 5. 출시 직전 (Play Store)

| 항목 | 상태 |
|------|------|
| 개인정보처리방침 / 문의 채널 URL | [ ] |
| 스토어 스크린샷·설명·연령등급 | [ ] |
| 프로덕션 API URL을 앱에 고정 | [ ] |
| 내부 테스트 트랙 (closed testing) | [ ] |
| 크래시/ANR 모니터링 | [ ] |
| 출시 체크리스트 최종 통과 | [ ] |

---

## 권장 순서 (다음에 할 일)

1. **API 프로덕션 배포** — Postgres + 시크릿 교체 + HTTPS  
2. **앱 `api` 모드로 실연동 검증** — 피드/마이픽/문의  
3. **EAS Android 빌드** — internal → closed testing  
4. **푸시(선택)** — 설치 credential + FCM outbox  
5. **스토어 메타·정책 문서** — 공개 출시

---

## 완료 요약 (지금까지)

- 모바일: Neon-Tactical UI, CatalogRepository(`preview`/`empty`/`api`), 마이픽, 문의하기
- 서버: Public / Admin JWT / Ingest Key, 상태머신, pytest
- 관리자: 로그인·게임·소식·문의
- 문서: ARCHITECTURE / BACKEND_ARCHITECTURE / DECISIONS (ADR-001~009)

## 깃

- 스테이징 155파일 준비됨 (`.env` / `.venv` / `node_modules` 제외)
- **커밋 대기**: 이 PC에 `user.name` / `user.email` 미설정 → 본인 정보 알려주면 커밋 완료
- 원격(remote) 미연결 → push는 저장소 URL 필요
