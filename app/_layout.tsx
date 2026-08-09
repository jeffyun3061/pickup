import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { View } from 'react-native';
import 'react-native-reanimated';

import { fontAssets } from '@/src/assets/fonts';
import { LoadingState } from '@/src/components/StateBlocks';
import { AppProvider, useApp } from '@/src/state/AppProvider';
import { theme } from '@/src/theme/tokens';

export { ErrorBoundary } from 'expo-router';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded, error] = useFonts(fontAssets);

  useEffect(() => {
    if (error) throw error;
  }, [error]);

  useEffect(() => {
    if (loaded) SplashScreen.hideAsync();
  }, [loaded]);

  if (!loaded) return null;

  return (
    <AppProvider>
      <StatusBar style="light" />
      <RootNavigator />
    </AppProvider>
  );
}

function RootNavigator() {
  const { ready } = useApp();

  if (!ready) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.color.background, justifyContent: 'center' }}>
        <LoadingState label="PIKY BOOT…" />
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
      <Stack.Screen name="content/[id]" />
      <Stack.Screen name="announcement/[id]" />
      <Stack.Screen name="inquiry" />
    </Stack>
  );
}
