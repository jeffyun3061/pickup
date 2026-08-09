import { Redirect } from 'expo-router';

import { LoadingState } from '@/src/components/StateBlocks';
import { Screen } from '@/src/components/Screen';
import { useApp } from '@/src/state/AppProvider';

export default function GateScreen() {
  const { ready, preferences } = useApp();

  if (!ready) {
    return (
      <Screen scroll={false}>
        <LoadingState />
      </Screen>
    );
  }

  if (!preferences.onboardingCompleted) {
    return <Redirect href="/onboarding" />;
  }

  return <Redirect href="/(tabs)" />;
}
