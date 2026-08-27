/**
 * 배포 후 공개 API 최소 스모크 검사.
 * 사용법: npm run smoke:api -- https://api.gamepickup.example
 */

const raw = String(process.argv[2] || process.env.API_URL || '').trim();
if (!raw) {
  console.error('API URL을 인자로 지정하세요. 예: npm run smoke:api -- https://api.example.com');
  process.exit(1);
}

let base;
try {
  base = new URL(raw);
  if (!['http:', 'https:'].includes(base.protocol)) throw new Error('scheme');
  if (base.pathname !== '/' || base.search || base.hash || base.username || base.password) {
    throw new Error('origin');
  }
} catch {
  console.error('API URL은 credentials·경로·쿼리 없는 http(s) origin이어야 합니다.');
  process.exit(1);
}

// API뿐 아니라 Docker 이미지에 함께 포함되는 관리자 SPA도 실제 배포에서
// 정적 파일이 빠지지 않았는지 확인한다. 관리자 내부 이동은 hash 라우팅이라
// `/admin/` 한 경로만 검사하면 새로고침 진입 계약까지 검증할 수 있다.
const paths = [
  '/health/live',
  '/health/ready',
  '/admin/',
  '/api/v1/games',
  '/api/v1/rankings',
  '/privacy',
  '/terms',
];
const controller = new AbortController();
const timer = setTimeout(() => controller.abort(), 10_000);

try {
  for (const path of paths) {
    const response = await fetch(new URL(path, base), {
      headers: { Accept: 'application/json,text/html' },
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`${path} returned HTTP ${response.status}`);
    }
    console.log(`OK ${response.status} ${path}`);
  }
  console.log(`API 스모크 통과: ${base.origin}`);
} catch (error) {
  console.error(`API 스모크 실패: ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
} finally {
  clearTimeout(timer);
}
