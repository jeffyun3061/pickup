import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { readFile } from 'node:fs/promises';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const script = resolve(root, 'scripts/release-preflight.mjs');

function run(overrides) {
  return spawnSync(process.execPath, [script], {
    cwd: root,
    encoding: 'utf8',
    env: {
      ...process.env,
      EXPO_PUBLIC_CATALOG_MODE: 'api',
      EXPO_PUBLIC_API_URL: 'https://api.gamepickup.app',
      ...overrides,
    },
  });
}

assert.equal(run({}).status, 0, 'valid production API origin should pass');

for (const apiUrl of [
  'https://api.gamepickup.example',
  'https://api.gamepickup.example.com',
  'http://api.gamepickup.app',
  'https://api.gamepickup.app/v1',
  'https://localhost:8000',
]) {
  assert.notEqual(
    run({ EXPO_PUBLIC_API_URL: apiUrl }).status,
    0,
    `placeholder or non-origin URL should fail: ${apiUrl}`,
  );
}

assert.notEqual(
  run({ EXPO_PUBLIC_CATALOG_MODE: 'preview' }).status,
  0,
  'preview catalog must not pass the production preflight',
);

// EAS 프로필의 APK/AAB·API 모드 계약도 운영 빌드 전에 고정한다.
// 실제 eas.json을 덮어쓰지 않고 preflight가 받는 임시 JSON 입력만 바꾼다.
const originalEas = JSON.parse(await readFile(resolve(root, 'eas.json'), 'utf8'));
const brokenPreview = structuredClone(originalEas);
brokenPreview.build.preview.android.buildType = 'app-bundle';
assert.notEqual(
  run({ RELEASE_PREFLIGHT_EAS_JSON: JSON.stringify(brokenPreview) }).status,
  0,
  'preview must remain an APK profile',
);

const brokenProduction = structuredClone(originalEas);
brokenProduction.build.production.android.buildType = 'apk';
assert.notEqual(
  run({ RELEASE_PREFLIGHT_EAS_JSON: JSON.stringify(brokenProduction) }).status,
  0,
  'production must remain an app-bundle profile',
);

console.log('릴리스 사전검사 계약 테스트 통과');
