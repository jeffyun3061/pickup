/**
 * Android 운영 빌드 전에 API 연결 설정을 확인한다.
 *
 * 사용법:
 *   EXPO_PUBLIC_CATALOG_MODE=api EXPO_PUBLIC_API_URL=https://<actual-api-domain> npm run release:check
 *
 * CI 계약 테스트만 RELEASE_PREFLIGHT_ALLOW_TEST_HOST=1을 함께 지정한다.
 */

import { readFileSync } from 'node:fs';

const mode = String(process.env.EXPO_PUBLIC_CATALOG_MODE || '').trim().toLowerCase();
const apiUrl = String(process.env.EXPO_PUBLIC_API_URL || '').trim();
const allowTestHost = process.env.RELEASE_PREFLIGHT_ALLOW_TEST_HOST === '1';
const errors = [];

// EAS 환경이 profile 이름과 어긋나면 preview 빌드가 production API를 보거나
// 운영 빌드가 개발 환경을 참조할 수 있으므로, 빌드 직전에 정적 설정도 확인한다.
try {
  // 계약 테스트는 임시 JSON을 환경변수로 주입해 실제 eas.json을 변경하지 않는다.
  const easSource = process.env.RELEASE_PREFLIGHT_EAS_JSON
    || readFileSync(new URL('../eas.json', import.meta.url), 'utf8');
  const eas = JSON.parse(easSource);
  const profiles = eas?.build ?? {};
  if (profiles.preview?.environment !== 'preview') {
    errors.push('eas.json의 preview 프로필은 preview 환경이어야 합니다.');
  }
  if (profiles.production?.environment !== 'production') {
    errors.push('eas.json의 production 프로필은 production 환경이어야 합니다.');
  }
  if (profiles.preview?.android?.buildType !== 'apk') {
    errors.push('eas.json의 preview Android 빌드는 APK여야 합니다.');
  }
  if (profiles.production?.android?.buildType !== 'app-bundle') {
    errors.push('eas.json의 production Android 빌드는 Play용 app-bundle이어야 합니다.');
  }
  if (profiles.preview?.env?.EXPO_PUBLIC_CATALOG_MODE !== 'api') {
    errors.push('eas.json의 preview 프로필은 공개 API 카탈로그 모드여야 합니다.');
  }
  if (profiles.production?.env?.EXPO_PUBLIC_CATALOG_MODE !== 'api') {
    errors.push('eas.json의 production 프로필은 공개 API 카탈로그 모드여야 합니다.');
  }
} catch {
  errors.push('eas.json을 읽을 수 없거나 JSON 형식이 올바르지 않습니다.');
}

if (mode !== 'api') {
  errors.push('EXPO_PUBLIC_CATALOG_MODE는 운영 빌드에서 api여야 합니다.');
}

if (!apiUrl) {
  errors.push('EXPO_PUBLIC_API_URL이 비어 있습니다. 운영 HTTPS API 주소를 지정하세요.');
} else {
  try {
    const parsed = new URL(apiUrl);
    if (parsed.protocol !== 'https:') {
      errors.push('EXPO_PUBLIC_API_URL은 https:// 주소여야 합니다.');
    }
    if (['localhost', '127.0.0.1', '0.0.0.0'].includes(parsed.hostname)) {
      errors.push('운영 빌드에 로컬호스트 API 주소를 사용할 수 없습니다.');
    }
    const hostname = parsed.hostname.toLowerCase();
    const placeholderHosts = new Set([
      'example.com',
      'example.org',
      'example.net',
      'invalid',
      'test',
    ]);
    if (
      (
        placeholderHosts.has(hostname) ||
        hostname === 'example' ||
        hostname.endsWith('.example.com') ||
        hostname.endsWith('.example.org') ||
        hostname.endsWith('.example.net') ||
        hostname.endsWith('.example') ||
        hostname.endsWith('.invalid') ||
        hostname.endsWith('.test') ||
        hostname.endsWith('.local') ||
        hostname.endsWith('.localhost')
      ) ||
      (!allowTestHost &&
        (hostname === 'gamepickup.dev' || hostname.endsWith('.gamepickup.dev')))
    ) {
      errors.push('운영 빌드에 문서용·개발용 API 호스트를 사용할 수 없습니다.');
    }
    if (parsed.pathname !== '/' || parsed.search || parsed.hash) {
      errors.push('EXPO_PUBLIC_API_URL에는 origin만 넣고 경로·쿼리·해시는 제거하세요.');
    }
  } catch {
    errors.push('EXPO_PUBLIC_API_URL이 올바른 URL이 아닙니다.');
  }
}

if (errors.length) {
  console.error('릴리스 사전검사 실패');
  for (const error of errors) console.error(`- ${error}`);
  process.exitCode = 1;
} else {
  console.log(`릴리스 사전검사 통과: ${apiUrl}`);
}
