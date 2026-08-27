import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/src/components/AppText';
import { formatRelativeTime } from '@/src/domain/models';
import { theme } from '@/src/theme/tokens';

type Props = {
  lastUpdatedAt: number | null;
  onRetry?: () => void;
};

/** 네트워크 실패 시 캐시 데이터 위에 띄우는 상태 배너 */
export function OfflineBanner({ lastUpdatedAt, onRetry }: Props) {
  return (
    <View style={styles.banner}>
      <Ionicons name="cloud-offline-outline" size={16} color={theme.color.neonYellow} />
      <AppText style={styles.text} numberOfLines={1}>
        연결 안 됨
        {lastUpdatedAt
          ? ` · 마지막 업데이트 ${formatRelativeTime(new Date(lastUpdatedAt).toISOString())}`
          : ' · 저장된 데이터가 없어요'}
      </AppText>
      {onRetry ? (
        <Pressable onPress={onRetry} hitSlop={8}>
          <AppText style={styles.retry}>재시도</AppText>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 10,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.35)',
    backgroundColor: 'rgba(255, 215, 0, 0.08)',
  },
  text: {
    flex: 1,
    minWidth: 0,
    fontFamily: theme.font.body,
    fontSize: 12,
    color: theme.color.onSurface,
  },
  retry: {
    fontFamily: theme.font.bodySemi,
    fontSize: 12,
    color: theme.color.neonYellow,
  },
});
