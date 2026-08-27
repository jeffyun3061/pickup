import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/src/components/AppText';
import { useLayout } from '@/src/theme/useLayout';
import { theme } from '@/src/theme/tokens';

type Props = {
  brand?: boolean;
  title?: string;
  subtitle?: string;
  showBack?: boolean;
  /** 전달 시( null 포함 ) 기본 알림 버튼 대신 사용 */
  rightSlot?: ReactNode;
  showNotificationPip?: boolean;
  onPressNotification?: () => void;
};

/** 시안 TopAppBar — 우측은 알림 벨 하나 + pip (설정 톱니 없음) */
export function AppHeader({
  brand = true,
  title,
  subtitle,
  showBack = false,
  rightSlot,
  showNotificationPip = true,
  onPressNotification,
}: Props) {
  const layout = useLayout();

  return (
    <View style={[styles.wrap, { marginHorizontal: -layout.margin, paddingHorizontal: layout.margin }]}>
      <View style={styles.row}>
        <View style={styles.left}>
          {showBack ? (
            <Pressable
              onPress={() => router.back()}
              hitSlop={12}
              accessibilityRole="button"
              accessibilityLabel="뒤로가기"
              style={({ pressed }) => [styles.iconBtn, pressed && { opacity: 0.7 }]}
            >
              <Ionicons name="arrow-back" size={20} color={theme.color.onSurface} />
            </Pressable>
          ) : (
            <Ionicons name="flash" size={22} color={theme.color.neonYellow} />
          )}
          <View style={styles.titles}>
            <View style={styles.titleLine}>
              {brand ? (
                <AppText style={[styles.brand, { fontSize: layout.isCompact ? 17 : 18 }]}>
                  게임픽업
                </AppText>
              ) : null}
              {title ? (
                <AppText style={styles.pageTitle} numberOfLines={1}>
                  {brand ? `· ${title}` : title}
                </AppText>
              ) : null}
            </View>
            {subtitle ? (
              <AppText variant="caption" numberOfLines={2}>
                {subtitle}
              </AppText>
            ) : null}
          </View>
        </View>
        <View style={styles.right}>
          {rightSlot !== undefined ? (
            rightSlot
          ) : (
            <Pressable
              onPress={onPressNotification ?? (() => router.push('/(tabs)/settings'))}
              hitSlop={12}
              accessibilityRole="button"
              accessibilityLabel="알림"
              style={({ pressed }) => [styles.notifyHit, pressed && { opacity: 0.7 }]}
            >
              <Ionicons name="notifications" size={24} color={theme.color.neonYellow} />
              {showNotificationPip ? <View style={styles.pip} /> : null}
            </Pressable>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    paddingVertical: 12,
    marginBottom: theme.space.gutter,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(68, 73, 51, 0.5)',
    backgroundColor: 'rgba(19, 19, 20, 0.92)',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  left: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
    minWidth: 0,
  },
  titles: { flex: 1, minWidth: 0, gap: 2 },
  titleLine: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    minWidth: 0,
  },
  brand: {
    fontFamily: theme.font.bodySemi,
    color: theme.color.neonYellow,
    letterSpacing: -0.4,
    flexShrink: 0,
  },
  pageTitle: {
    flexShrink: 1,
    fontFamily: theme.font.bodySemi,
    fontSize: 14,
    color: theme.color.onSurfaceVariant,
    letterSpacing: -0.2,
  },
  right: {
    flexShrink: 0,
  },
  iconBtn: {
    width: 36,
    height: 36,
    borderRadius: theme.radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.color.surfaceContainerHigh,
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
  },
  notifyHit: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pip: {
    position: 'absolute',
    top: 4,
    right: 5,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: theme.color.neonYellow,
    borderWidth: 1.5,
    borderColor: theme.color.background,
  },
});
