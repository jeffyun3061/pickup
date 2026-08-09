# 진행 현황 · 출시 체크리스트

작업 루트: `C:\Users\user\Projects\pickup`  
기준일: 2026-08-09

범례: `[x]` 완료 · `[~]` 부분 · `[ ]` 미착수

---

## 1. 모바일 앱 (Expo)

| 항목 | 상태 | 비고 |
|------|------|------|
| Neon-Tactical UI + PIKY 헤더/탭 | [x] | 5탭 |
| Preview / Empty / Api 카탈로그 | [x] | |
| 마이픽 · 온보딩 · 문의하기 | [x] | |
| SecureStore credential + 서버 등록 | [x] | `ensureInstallation` |
| Preference 서버 동기 | [x] | 알림 3종 + gameIds |
| Device token 등록 | [~] | expo-notifications (권한·네이티브 빌드 필요) |
| 실기기 API 모드 검증 | [~] | |
| Android 릴리스 빌드 / Play 등록 | [ ] | 인프라·스토어 |

## 2. 백엔드 API (`server/`)

| 항목 | 상태 | 비고 |
|------|------|------|
| 계층 + 상태머신 + Admin/Ingest/Public | [x] | |
| 요청 단위 트랜잭션 (flush/commit) | [x] | |
| Installation 발급·인증 | [x] | ADR-010 |
| Device token / preferences | [x] | |
| Publish → push outbox enqueue | [x] | |
| Outbox stub dispatch | [x] | `POST /admin/push/dispatch` |
| pytest (권한 부정 + 푸시 플로우) | [x] | |
| PostgreSQL / HTTPS 배포 | [ ] | 인프라 제외 |
| 실 FCM 발송 워커 | [ ] | 스텁→교체 |
| 문의 rate limit | [ ] | |

## 3. 관리자 웹

| 항목 | 상태 |
|------|------|
| 로그인·CRUD·발행·문의 | [x] |
| 프로덕션 호스팅 | [ ] |

## 4. 출시 직전

| 항목 | 상태 |
|------|------|
| 스토어 메타·개인정보처리방침 | [ ] |
| EAS AAB · 내부 테스트 | [ ] |

---

## 깃 워크플로

작업 끝나면 에이전트가 **한글 커밋 메시지 3안 + 명령어**만 제안. 커밋·push는 사용자 직접.
