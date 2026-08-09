import { Platform } from 'react-native';

import {
  ensureInstallation,
  syncInstallationPreferences,
  upsertDeviceToken,
} from '@/src/data/installationApi';
import type { Preferences } from '@/src/domain/models';

/**
 * 설치 credential + preference 동기 + (가능 시) device token 등록.
 * FCM 콘솔/네이티브 빌드가 없으면 토큰 단계는 건너뛰고 서버 계약만 유지한다.
 */
export async function bootstrapInstallationChannel(preferences: Preferences): Promise<void> {
  try {
    await ensureInstallation();
    await syncInstallationPreferences(preferences);
  } catch {
    // API 미기동·오프라인 시 앱 사용은 계속 (preview 모드 포함)
    return;
  }

  try {
    await registerPushTokenIfAvailable();
  } catch {
    /* 권한 거부·Expo Go 제한 — preference 동기만으로도 타겟팅 준비는 됨 */
  }
}

async function registerPushTokenIfAvailable(): Promise<void> {
  // 동적 import: 웹/테스트 환경에서 네이티브 모듈 부재를 허용
  const Notifications = await import('expo-notifications');
  const permission = await Notifications.getPermissionsAsync();
  let final = permission;
  if (permission.status !== 'granted') {
    final = await Notifications.requestPermissionsAsync();
  }
  if (final.status !== 'granted') return;

  const device = await Notifications.getDevicePushTokenAsync();
  const token = typeof device.data === 'string' ? device.data : null;
  if (!token || token.length < 8) return;

  const platform =
    Platform.OS === 'ios' ? 'ios' : Platform.OS === 'android' ? 'android' : 'web';
  await upsertDeviceToken({ platform, token });
}
