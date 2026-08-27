import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { bootstrapInstallationChannel } from '@/src/data/pushBootstrap';
import {
  defaultPreferences,
  preferencesStore,
} from '@/src/data/preferencesStore';
import {
  revokeInstallation,
  syncInstallationPreferences,
} from '@/src/data/installationApi';
import { clearCatalogSnapshot } from '@/src/data/catalogCache';
import { normalizeGameIds, type Preferences } from '@/src/domain/models';
import { bookmarkStore, readStore } from '@/src/state/idSetStore';

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

        // 앱 화면은 네트워크를 기다리지 않는다.
        // API 미기동·오프라인이어도 먼저 진입하고 설치/푸시 동기화는 백그라운드에서 수행한다.
        void bootstrapInstallationChannel(loaded);
      } finally {
        if (mounted) setReady(true);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const persistAndSync = useCallback(async (next: Preferences) => {
    setPreferences(next);
    await preferencesStore.save(next);
    try {
      await syncInstallationPreferences(next);
    } catch {
      /* 오프라인 시 로컬만 유지, 다음 기동/변경 때 재동기 */
    }
  }, []);

  const completeOnboarding = useCallback(async (gameIds: string[]) => {
    const next = {
      ...preferences,
      onboardingCompleted: true,
      gameIds: normalizeGameIds(gameIds),
    };
    await persistAndSync(next);
    void bootstrapInstallationChannel(next);
  }, [preferences, persistAndSync]);

  const setGameIds = useCallback(async (gameIds: string[]) => {
    const next = { ...preferences, gameIds: normalizeGameIds(gameIds) };
    await persistAndSync(next);
    if (next.gameIds.length > 0) {
      void bootstrapInstallationChannel(next);
    }
  }, [preferences, persistAndSync]);

  const setNotifications = useCallback(
    async (notifications: Preferences['notifications']) => {
      await persistAndSync({ ...preferences, notifications });
    },
    [preferences, persistAndSync],
  );

  const resetLocalData = useCallback(async () => {
    // 네트워크가 끊겨도 revokeInstallation 내부 1.5초 타임아웃 뒤에는
    // 로컬 데이터를 항상 삭제한다. 해지 함수가 credential도 정리한다.
    await revokeInstallation().catch(() => undefined);
    setPreferences(defaultPreferences);
    await preferencesStore.clear();
    bookmarkStore.clear();
    readStore.clear();
    await clearCatalogSnapshot();
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
