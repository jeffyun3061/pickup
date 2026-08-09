import { Ionicons } from '@expo/vector-icons';
import { ActivityIndicator, Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/src/components/AppText';
import { theme } from '@/src/theme/tokens';

export function LoadingState({ label = '동기화 중…' }: { label?: string }) {
  return (
    <View style={styles.block}>
      <ActivityIndicator color={theme.color.neonYellow} />
      <AppText variant="label">{label}</AppText>
    </View>
  );
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon = 'cube-outline',
}: {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: keyof typeof Ionicons.glyphMap;
}) {
  return (
    <View style={styles.panel}>
      <View style={styles.bracket} />
      <Ionicons name={icon} size={28} color={theme.color.neonYellow} />
      <AppText variant="subtitle" style={styles.center}>
        {title}
      </AppText>
      <AppText variant="caption" style={styles.center}>
        {description}
      </AppText>
      {actionLabel && onAction ? (
        <Pressable
          onPress={onAction}
          style={({ pressed }) => [styles.cta, pressed && { opacity: 0.85 }]}
        >
          <AppText style={styles.ctaText}>{actionLabel}</AppText>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  block: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
    gap: 12,
  },
  panel: {
    alignItems: 'center',
    gap: 10,
    padding: 24,
    marginTop: 12,
    backgroundColor: 'rgba(32, 31, 32, 0.85)',
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.lg,
  },
  bracket: {
    position: 'absolute',
    top: 8,
    left: 8,
    width: 12,
    height: 12,
    borderTopWidth: 2,
    borderLeftWidth: 2,
    borderColor: theme.color.neonYellow,
  },
  center: { textAlign: 'center' },
  cta: {
    marginTop: 8,
    backgroundColor: theme.color.primaryContainer,
    paddingHorizontal: 18,
    paddingVertical: 12,
    borderRadius: theme.radius.sm,
  },
  ctaText: {
    fontFamily: theme.font.label,
    color: theme.color.onPrimary,
    fontSize: 12,
    letterSpacing: 1,
  },
});
