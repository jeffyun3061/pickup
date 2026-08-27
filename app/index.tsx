import { Ionicons } from '@expo/vector-icons';
import { Redirect } from 'expo-router';
import { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { AppText } from '@/src/components/AppText';
import { LoadingState } from '@/src/components/StateBlocks';
import { Screen } from '@/src/components/Screen';
import { checkUpdateRequired } from '@/src/data/appMeta';
import { useApp } from '@/src/state/AppProvider';
import { theme } from '@/src/theme/tokens';

export default function GateScreen() {
  const { ready } = useApp();
  const [updateRequired, setUpdateRequired] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    checkUpdateRequired()
      .then((required) => {
        if (mounted) setUpdateRequired(required);
      })
      .catch(() => {
        if (mounted) setUpdateRequired(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  if (!ready || updateRequired === null) {
    return (
      <Screen scroll={false}>
        <LoadingState />
      </Screen>
    );
  }

  if (updateRequired) {
    return (
      <Screen scroll={false}>
        <View style={styles.updateWrap}>
          <Ionicons name="arrow-up-circle-outline" size={44} color={theme.color.neonYellow} />
          <AppText variant="subtitle" style={styles.center}>
            업데이트가 필요해요
          </AppText>
          <AppText variant="caption" style={styles.center}>
            안정적인 사용을 위해 스토어에서 최신 버전으로 업데이트해 주세요.
          </AppText>
        </View>
      </Screen>
    );
  }

  return <Redirect href="/(tabs)" />;
}

const styles = StyleSheet.create({
  updateWrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    padding: 24,
  },
  center: { textAlign: 'center' },
});
