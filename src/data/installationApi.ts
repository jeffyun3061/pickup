import { apiFetch } from '@/src/data/apiClient';
import {
  credentialStore,
  type InstallationCredential,
} from '@/src/data/credentialStore';
import type { Preferences } from '@/src/domain/models';

type InstallationCreateResponse = {
  installation_id: string;
  secret: string;
};

function authHeaders(credential: InstallationCredential): Record<string, string> {
  return {
    'X-Installation-Id': credential.installationId,
    'X-Installation-Secret': credential.secret,
  };
}

/** 없으면 서버에서 발급받아 SecureStore에 저장. */
export async function ensureInstallation(): Promise<InstallationCredential> {
  const existing = await credentialStore.load();
  if (existing) return existing;

  const created = await apiFetch<InstallationCreateResponse>('/api/v1/installations', {
    method: 'POST',
  });
  const credential: InstallationCredential = {
    installationId: created.installation_id,
    secret: created.secret,
  };
  await credentialStore.save(credential);
  return credential;
}

export async function syncInstallationPreferences(preferences: Preferences): Promise<void> {
  const credential = await ensureInstallation();
  await apiFetch('/api/v1/installations/me/preferences', {
    method: 'PUT',
    headers: authHeaders(credential),
    body: JSON.stringify({
      game_ids: preferences.gameIds,
      notifications: {
        selected_game_news: preferences.notifications.selectedGameNews,
        event_ending: preferences.notifications.eventEnding,
        service_notices: preferences.notifications.serviceNotices,
      },
    }),
  });
}

export async function upsertDeviceToken(params: {
  platform: 'android' | 'ios' | 'web';
  token: string;
}): Promise<void> {
  const credential = await ensureInstallation();
  await apiFetch('/api/v1/installations/me/device-token', {
    method: 'PUT',
    headers: authHeaders(credential),
    body: JSON.stringify(params),
  });
}

/** 앱 데이터 초기화 시 서버의 푸시 토큰·관심 게임도 함께 해지한다. */
export async function revokeInstallation(): Promise<void> {
  const credential = await credentialStore.load();
  if (!credential) return;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 1500);
  try {
    await apiFetch<void>('/api/v1/installations/me', {
      method: 'DELETE',
      headers: authHeaders(credential),
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
    await credentialStore.clear();
  }
}
