import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { View } from 'react-native';
import 'react-native-reanimated';

import { fontAssets } from '@/src/assets/fonts';
import { LoadingState } from '@/src/components/StateBlocks';
import { setupNotificationNavigation } from '@/src/data/pushBootstrap';
import { AppProvider, useApp } from '@/src/state/AppProvider';
import { theme } from '@/src/theme/tokens';

export { ErrorBoundary } from 'expo-router';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded, error] = useFonts(fontAssets);
  const [fontLoadTimedOut, setFontLoadTimedOut] = useState(false);

  // 폰트 에셋 하나 때문에 앱 진입이 무한히 막히면 안 된다.
  // 콜드 스타트·저사양 기기에서 Metro/에셋 전달이 늦어져도 네이티브
  // 스플래시를 오래 붙잡지 않고 시스템 폴백 글꼴로 먼저 화면을 연다.
  useEffect(() => {
    const timer = setTimeout(() => setFontLoadTimedOut(true), 8000);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (error && !__DEV__) {
      console.warn('GamePickup 글꼴을 불러오지 못해 시스템 폴백을 사용합니다.', error);
    }
  }, [error]);

  const fontReady = loaded || Boolean(error) || fontLoadTimedOut;

  useEffect(() => {
    if (fontReady) void SplashScreen.hideAsync();
  }, [fontReady]);

  if (!fontReady) return null;

  return (
    <AppProvider>
      <StatusBar style="light" />
      <RootNavigator />
    </AppProvider>
  );
}

function RootNavigator() {
  const { ready } = useApp();

  useEffect(() => {
    if (!ready) return;
    let cleanup: (() => void) | undefined;
    setupNotificationNavigation()
      .then((fn) => {
        cleanup = fn;
      })
      .catch(() => {
        /* Expo Go 등 알림 미지원 환경 */
      });
    return () => cleanup?.();
  }, [ready]);

  if (!ready) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.color.background, justifyContent: 'center' }}>
        <LoadingState label="게임픽업 준비 중…" />
      </View>
    );
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: theme.color.background },
      }}
    >
      <Stack.Screen name="index" />
      <Stack.Screen name="onboarding" />
      <Stack.Screen name="(tabs)" />
      <Stack.Screen name="game/[id]" />
      <Stack.Screen name="content/[id]" />
      <Stack.Screen name="announcement/[id]" />
      <Stack.Screen name="inquiry" />
    </Stack>
  );
}
