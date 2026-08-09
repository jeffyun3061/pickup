import { Link, Stack } from 'expo-router';
import { StyleSheet } from 'react-native';

import { AppText } from '@/src/components/AppText';
import { Screen } from '@/src/components/Screen';
import { theme } from '@/src/theme/tokens';

export default function NotFoundScreen() {
  return (
    <>
      <Stack.Screen options={{ title: '없음', headerShown: false }} />
      <Screen>
        <AppText variant="display">화면을 찾을 수 없어요</AppText>
        <Link href="/" style={styles.link}>
          <AppText style={styles.linkText}>홈으로 돌아가기</AppText>
        </Link>
      </Screen>
    </>
  );
}

const styles = StyleSheet.create({
  link: {
    marginTop: theme.space.section,
  },
  linkText: {
    fontFamily: theme.font.bodySemi,
    color: theme.color.neonYellow,
  },
});
