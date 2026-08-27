import Constants from 'expo-constants';
import { router, type Href } from 'expo-router';
import { Platform } from 'react-native';

import {
  ensureInstallation,
  syncInstallationPreferences,
  upsertDeviceToken,
} from '@/src/data/installationApi';
import type { Preferences } from '@/src/domain/models';

/**
 * 설치 credential + preference 동기 + (가능 시) device token 등록.
 * Expo 프로젝트 연결/네이티브 빌드가 없으면 토큰 단계는 건너뛰고 서버 계약만 유지한다.
 */
export async function bootstrapInstallationChannel(preferences: Preferences): Promise<void> {
  try {
    await ensureInstallation();
    await syncInstallationPreferences(preferences);
  } catch {
    // API 미기동·오프라인 시 앱 사용은 계속 (preview 모드 포함)
    return;
  }

  // 첫 실행에서 바로 권한을 묻지 않는다. 사용자가 관심 게임을 고른 뒤
  // 알림의 가치를 이해한 시점에만 네이티브 권한 대화상자를 연다.
  if (preferences.gameIds.length === 0) return;
  try {
    await registerPushTokenIfAvailable();
  } catch {
    /* 권한 거부·Expo Go 제한 — preference 동기만으로도 타겟팅 준비는 됨 */
  }
}

async function registerPushTokenIfAvailable(): Promise<void> {
  // Expo Go SDK 53+ Android는 remote push API가 제거되어 import 시점에 throw 한다.
  // 실서비스 네이티브 빌드에서만 토큰을 등록한다.
  if (Constants.appOwnership === 'expo') return;

  // 동적 import: 웹/테스트 환경에서 네이티브 모듈 부재를 허용
  const Notifications = await import('expo-notifications');
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: '게임 소식',
      importance: Notifications.AndroidImportance.DEFAULT,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FFD700',
    });
  }
  const permission = await Notifications.getPermissionsAsync();
  let final = permission;
  if (permission.status !== 'granted') {
    final = await Notifications.requestPermissionsAsync();
  }
  if (final.status !== 'granted') return;

  // 서버가 Expo Push API로 발송하므로 Expo push token을 등록한다 (FCM 토큰 아님)
  const projectId =
    Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;
  const expoToken = await Notifications.getExpoPushTokenAsync(
    projectId ? { projectId } : undefined,
  );
  const token = typeof expoToken.data === 'string' ? expoToken.data : null;
  if (!token || token.length < 8) return;

  const platform =
    Platform.OS === 'ios' ? 'ios' : Platform.OS === 'android' ? 'android' : 'web';
  await upsertDeviceToken({ platform, token });
}

type NotificationData = Record<string, unknown> | undefined;

function routeFromNotification(data: NotificationData): void {
  if (!data) return;
  const contentId = typeof data.content_id === 'string' ? data.content_id : null;
  const announcementId =
    typeof data.announcement_id === 'string' ? data.announcement_id : null;
  const contentCount = typeof data.content_count === 'number' ? data.content_count : 1;
  if (contentId && contentCount > 1) router.push('/(tabs)/news' as Href);
  else if (contentId) router.push(`/content/${contentId}`);
  else if (announcementId) router.push(`/announcement/${announcementId}`);
}

/**
 * 알림 탭 딥링크: 포그라운드 표시 정책 + 탭 리스너 + cold start 알림 처리.
 * 내비게이션이 준비된 뒤(루트 레이아웃)에서 호출한다. 해제 함수를 돌려준다.
 */
export async function setupNotificationNavigation(): Promise<() => void> {
  if (Constants.appOwnership === 'expo') return () => {};

  const Notifications = await import('expo-notifications');

  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      // 앱을 보고 있는 중에도 새 소식 알림을 놓치지 않도록 기본음을 사용한다.
      // 백그라운드 알림은 서버 payload의 sound: "default"와 Android 채널 설정을 따른다.
      shouldPlaySound: true,
      shouldSetBadge: false,
      shouldShowBanner: true,
      shouldShowList: true,
    }),
  });

  const subscription = Notifications.addNotificationResponseReceivedListener((response) => {
    routeFromNotification(
      response.notification.request.content.data as NotificationData,
    );
  });

  // 앱이 꺼진 상태에서 알림을 탭해 실행된 경우
  const last = await Notifications.getLastNotificationResponseAsync();
  if (last) {
    routeFromNotification(last.notification.request.content.data as NotificationData);
  }

  return () => subscription.remove();
}
