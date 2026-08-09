import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import {
  defaultPreferences,
  preferencesStore,
} from '@/src/data/preferencesStore';
import type { Preferences } from '@/src/domain/models';

type AppContextValue = {
  ready: boolean;
  preferences: Preferences;
  completeOnboarding: (gameIds: string[]) => Promise<void>;
  setGameIds: (gameIds: string[]) => Promise<void>;
  setNotifications: (notifications: Preferences['notifications']) => Promise<void>;
  resetLocalData: () => Promise<void>;
};

const AppContext = createContext<AppContextValue | null>(null);

/**
 * 설치 단위 로컬 상태.
 * - 비민감 환경설정만 담당 → preferencesStore (AsyncStorage)
 * - 설치 secret은 credentialStore (SecureStore) — 별도 계층, 여기 섞지 않음
 */
export function AppProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [preferences, setPreferences] = useState<Preferences>(defaultPreferences);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const loaded = await preferencesStore.load();
        if (mounted) setPreferences(loaded);
      } finally {
        if (mounted) setReady(true);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const completeOnboarding = useCallback(async (gameIds: string[]) => {
    const next = { ...preferences, onboardingCompleted: true, gameIds };
    setPreferences(next);
    await preferencesStore.save(next);
  }, [preferences]);

  const setGameIds = useCallback(async (gameIds: string[]) => {
    const next = { ...preferences, gameIds };
    setPreferences(next);
    await preferencesStore.save(next);
  }, [preferences]);

  const setNotifications = useCallback(
    async (notifications: Preferences['notifications']) => {
      const next = { ...preferences, notifications };
      setPreferences(next);
      await preferencesStore.save(next);
    },
    [preferences],
  );

  const resetLocalData = useCallback(async () => {
    setPreferences(defaultPreferences);
    await preferencesStore.clear();
  }, []);

  const value = useMemo(
    () => ({
      ready,
      preferences,
      completeOnboarding,
      setGameIds,
      setNotifications,
      resetLocalData,
    }),
    [ready, preferences, completeOnboarding, setGameIds, setNotifications, resetLocalData],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
