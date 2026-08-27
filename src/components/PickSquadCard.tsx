import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { Image, Pressable, StyleSheet, View } from 'react-native';

import { useCatalogImage } from '@/src/assets/useCatalogImage';
import { AppText } from '@/src/components/AppText';
import type { Game } from '@/src/domain/models';
import { theme } from '@/src/theme/tokens';

type Props = {
  game: Game;
  /** 새 소식이 하나라도 있으면 좌측 상단 N 표시 */
  hasNew?: boolean;
  selected?: boolean;
  onPress?: () => void;
  onRemove?: () => void;
};

/** 시안 my_pick 스쿼드 카드 — 풀블리드 커버 + 하단 메타 */
export function PickSquadCard({
  game,
  hasNew = false,
  selected,
  onPress,
  onRemove,
}: Props) {
  const { source: cover, isFallback, onError: onImageError } = useCatalogImage(
    game.imageUrl,
    game.imageKey,
  );

  return (
    <Pressable
      onPress={() => {
        void Haptics.selectionAsync();
        onPress?.();
      }}
      accessibilityRole="button"
      accessibilityLabel={`${game.name} 소식 보기`}
      style={({ pressed }) => [
        styles.card,
        selected && styles.selected,
        pressed && { opacity: 0.92 },
      ]}
    >
      {cover ? (
        <>
          <Image
            source={cover}
            style={styles.cover}
            resizeMode="cover"
            blurRadius={isFallback && game.themedFallback ? 3 : 0}
            onError={onImageError}
          />
          {isFallback && game.themedFallback ? (
            <View
              pointerEvents="none"
              style={[styles.mockTint, { backgroundColor: game.color }]}
            />
          ) : null}
        </>
      ) : (
        <View style={[styles.coverFallback, { backgroundColor: game.color }]}>
          <AppText style={styles.initial}>{game.initial}</AppText>
        </View>
      )}
      <View style={styles.scrim} />
      {hasNew ? (
        <View style={styles.newBadge}>
          <AppText style={styles.newBadgeText}>N</AppText>
        </View>
      ) : null}
      {onRemove ? (
        <Pressable
          onPress={(event) => {
            event.stopPropagation();
            void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            onRemove();
          }}
          hitSlop={8}
          accessibilityRole="button"
          accessibilityLabel={`${game.name} 마이픽에서 제거`}
          style={({ pressed }) => [styles.removeButton, pressed && { opacity: 0.7 }]}
        >
          <Ionicons name="remove" size={18} color={theme.color.onSurface} />
        </Pressable>
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
  mockTint: {
    ...StyleSheet.absoluteFill,
    opacity: 0.34,
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
  newBadge: {
    position: 'absolute',
    top: 10,
    left: 10,
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.color.neonYellow,
    zIndex: 2,
  },
  newBadgeText: {
    fontFamily: theme.font.label,
    fontSize: 11,
    color: theme.color.onPrimary,
  },
  removeButton: {
    position: 'absolute',
    top: 9,
    right: 9,
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(14,14,15,0.82)',
    borderWidth: 1,
    borderColor: 'rgba(229,226,227,0.45)',
    zIndex: 3,
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
