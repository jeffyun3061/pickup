/**
 * commonjs 엔트리로 고정 로드.
 * 패키지 root의 "react-native": "src/index.ts" 필드는 Metro가 간헐적으로 해석 실패한다.
 */
import AsyncStorage from '@react-native-async-storage/async-storage/lib/commonjs/index.js';

import type { Preferences } from '@/src/domain/models';

/**
 * 비민감 설치 환경설정 저장소.
 * - 온보딩 완료, 관심 gameIds, 알림 3종
 * - 회원가입/비밀번호가 아니므로 SecureStore에 넣지 않는다 (ADR-007).
 */
export const PREFERENCES_STORAGE_KEY = 'gamepickup.preferences.v1';

export const defaultPreferences: Preferences = {
  onboardingCompleted: false,
  gameIds: [],
  notifications: {
    selectedGameNews: true,
    eventEnding: true,
    serviceNotices: true,
  },
};

export function serializePreferences(preferences: Preferences): string {
  return JSON.stringify(preferences);
}

export function parsePreferences(raw: string | null): Preferences {
  if (!raw) return defaultPreferences;
  try {
    const parsed = JSON.parse(raw) as Partial<Preferences>;
    return {
      ...defaultPreferences,
      ...parsed,
      gameIds: Array.isArray(parsed.gameIds) ? parsed.gameIds.filter((id) => typeof id === 'string') : [],
      notifications: {
        ...defaultPreferences.notifications,
        ...parsed.notifications,
      },
    };
  } catch {
    return defaultPreferences;
  }
}

export type PreferencesStore = {
  load(): Promise<Preferences>;
  save(preferences: Preferences): Promise<void>;
  clear(): Promise<void>;
};

export const preferencesStore: PreferencesStore = {
  async load() {
    const raw = await AsyncStorage.getItem(PREFERENCES_STORAGE_KEY);
    return parsePreferences(raw);
  },
  async save(preferences) {
    await AsyncStorage.setItem(PREFERENCES_STORAGE_KEY, serializePreferences(preferences));
  },
  async clear() {
    await AsyncStorage.removeItem(PREFERENCES_STORAGE_KEY);
  },
};
