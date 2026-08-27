import Constants from 'expo-constants';

import { apiFetch } from '@/src/data/apiClient';
import { catalogMode } from '@/src/data/catalog';

/** semver 비교: a < b → 음수, 같으면 0, a > b → 양수 */
export function compareSemver(a: string, b: string): number {
  const pa = a.split('.').map((x) => parseInt(x, 10) || 0);
  const pb = b.split('.').map((x) => parseInt(x, 10) || 0);
  for (let i = 0; i < 3; i += 1) {
    const diff = (pa[i] ?? 0) - (pb[i] ?? 0);
    if (diff !== 0) return diff;
  }
  return 0;
}

/**
 * 서버 최소 지원 버전 확인. api 모드가 아니거나 확인 실패 시 앱 사용을 막지 않는다.
 */
export async function checkUpdateRequired(): Promise<boolean> {
  if (catalogMode !== 'api') return false;
  try {
    const meta = await apiFetch<{ min_app_version: string }>('/api/v1/meta');
    const min = (meta.min_app_version || '').trim();
    if (!min) return false;
    const current = Constants.expoConfig?.version ?? '0.0.0';
    return compareSemver(current, min) < 0;
  } catch {
    return false;
  }
}
