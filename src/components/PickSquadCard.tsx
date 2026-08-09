import * as Haptics from 'expo-haptics';
import { Image, Pressable, StyleSheet, View } from 'react-native';

import { resolveImage, type AppImageName } from '@/src/assets/images';
import { AppText } from '@/src/components/AppText';
import type { Game } from '@/src/domain/models';
import { theme } from '@/src/theme/tokens';

type Props = {
  game: Game;
  /** 시안 배지: 새 소식 / N 알림 */
  badgeLabel?: string;
  badgeTone?: 'yellow' | 'purple' | 'alert';
  selected?: boolean;
  onPress?: () => void;
  onLongPress?: () => void;
};

/** 시안 my_pick 스쿼드 카드 — 풀블리드 커버 + 하단 메타 */
export function PickSquadCard({
  game,
  badgeLabel,
  badgeTone = 'yellow',
  selected,
  onPress,
  onLongPress,
}: Props) {
  const local = resolveImage(game.imageKey as AppImageName | undefined);
  const cover = game.imageUrl ? { uri: game.imageUrl } : local;
  const badgeBg =
    badgeTone === 'purple'
      ? theme.color.neonPurple
      : badgeTone === 'alert'
        ? theme.color.error
        : theme.color.primaryContainer;
  const badgeFg =
    badgeTone === 'purple' || badgeTone === 'alert'
      ? '#FFFFFF'
      : theme.color.onPrimary;

  return (
    <Pressable
      onPress={() => {
        void Haptics.selectionAsync();
        onPress?.();
      }}
      onLongPress={() => {
        void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
        onLongPress?.();
      }}
      accessibilityRole="button"
      accessibilityLabel={game.name}
      style={({ pressed }) => [
        styles.card,
        selected && styles.selected,
        pressed && { opacity: 0.92 },
      ]}
    >
      {cover ? (
        <Image source={cover} style={styles.cover} resizeMode="cover" />
      ) : (
        <View style={[styles.coverFallback, { backgroundColor: game.color }]}>
          <AppText style={styles.initial}>{game.initial}</AppText>
        </View>
      )}
      <View style={styles.scrim} />
      {badgeLabel ? (
        <View style={[styles.badge, { backgroundColor: badgeBg }]}>
          <AppText style={[styles.badgeText, { color: badgeFg }]} numberOfLines={1}>
            {badgeLabel}
          </AppText>
        </View>
      ) : null}
      <View style={styles.footer}>
        <AppText style={styles.name} numberOfLines={1}>
          {game.name}
        </AppText>
        <AppText variant="data" numberOfLines={1} style={styles.genre}>
          {game.genre}
        </AppText>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    borderRadius: theme.radius.lg,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    backgroundColor: theme.color.surfaceContainerHigh,
    minHeight: 0,
  },
  selected: {
    borderColor: theme.color.neonYellow,
  },
  cover: {
    ...StyleSheet.absoluteFill,
    opacity: 0.72,
  },
  coverFallback: {
    ...StyleSheet.absoluteFill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  initial: {
    fontFamily: theme.font.headline,
    fontSize: 36,
    color: theme.color.onSurface,
  },
  scrim: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(14,14,15,0.22)',
  },
  badge: {
    position: 'absolute',
    top: 10,
    right: 10,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 4,
    zIndex: 2,
  },
  badgeText: {
    fontFamily: theme.font.label,
    fontSize: 10,
    letterSpacing: 0.4,
  },
  footer: {
    marginTop: 'auto',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(68,73,51,0.55)',
    backgroundColor: 'rgba(19,19,20,0.55)',
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 4,
    zIndex: 2,
  },
  name: {
    fontFamily: theme.font.headlineSemi,
    fontSize: 16,
    color: theme.color.onSurface,
  },
  genre: {
    color: theme.color.onSurfaceVariant,
  },
});
