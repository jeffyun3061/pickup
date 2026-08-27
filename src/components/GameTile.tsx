import * as Haptics from 'expo-haptics';
import { Image, Pressable, StyleSheet, View } from 'react-native';

import { useCatalogImage } from '@/src/assets/useCatalogImage';
import { AppText } from '@/src/components/AppText';
import type { Game } from '@/src/domain/models';
import { theme } from '@/src/theme/tokens';

type Props = {
  game: Game;
  selected?: boolean;
  onPress?: () => void;
};

/** 마이 픽 / 온보딩 선택 타일 — 커버 이미지 + 이니셜 폴백 */
export function GameTile({ game, selected, onPress }: Props) {
  const { source: cover, isFallback, isGeneratedGameArt, onError: onImageError } = useCatalogImage(
    game.imageUrl,
    game.imageKey,
    game.id,
  );

  return (
    <Pressable
      onPress={() => {
        void Haptics.selectionAsync();
        onPress?.();
      }}
      style={({ pressed }) => [
        styles.tile,
        selected && styles.selected,
        pressed && { opacity: 0.9 },
      ]}
    >
      <View style={styles.coverWrap}>
        {cover ? (
          <>
            <View
              pointerEvents="none"
              style={[styles.coverPlaceholder, { backgroundColor: game.color || theme.color.surfaceContainerHighest }]}
            >
              <AppText style={styles.placeholderInitial}>
                {game.initial || game.name.slice(0, 1)}
              </AppText>
            </View>
            <Image
              source={cover}
              style={styles.cover}
              resizeMode="cover"
              blurRadius={isFallback && game.themedFallback && !isGeneratedGameArt ? 3 : 0}
              onError={onImageError}
            />
            {isFallback && game.themedFallback && !isGeneratedGameArt ? (
              <View
                pointerEvents="none"
                style={[styles.mockTint, { backgroundColor: game.color }]}
              />
            ) : null}
          </>
        ) : (
          <View
            style={[
              styles.coverFallback,
              { backgroundColor: game.color || theme.color.surfaceContainerHighest },
            ]}
          >
            <AppText style={styles.initial}>{game.initial || game.name.slice(0, 1)}</AppText>
          </View>
        )}
        <View style={styles.coverScrim} />
        {selected ? (
          <View style={styles.check}>
            <AppText style={styles.checkText}>PICK</AppText>
          </View>
        ) : null}
      </View>
      <AppText variant="subtitle" numberOfLines={1} style={styles.name}>
        {game.name}
      </AppText>
      <AppText variant="data" numberOfLines={1}>
        {game.genre}
      </AppText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  tile: {
    width: '100%',
    backgroundColor: theme.color.surfaceContainer,
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.md,
    padding: 10,
    gap: 8,
    marginBottom: 12,
    overflow: 'hidden',
  },
  selected: {
    borderColor: theme.color.neonYellow,
  },
  coverWrap: {
    height: 96,
    borderRadius: theme.radius.sm,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    backgroundColor: theme.color.surfaceContainerHighest,
  },
  cover: {
    width: '100%',
    height: '100%',
  },
  coverPlaceholder: {
    ...StyleSheet.absoluteFill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderInitial: {
    fontFamily: theme.font.headline,
    color: 'rgba(255,255,255,0.82)',
    fontSize: 28,
  },
  mockTint: {
    ...StyleSheet.absoluteFill,
    opacity: 0.34,
  },
  coverFallback: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  coverScrim: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(19,19,20,0.18)',
  },
  initial: {
    fontFamily: theme.font.headline,
    color: theme.color.onSurface,
    fontSize: 22,
  },
  name: { marginTop: 2 },
  check: {
    position: 'absolute',
    top: 8,
    left: 8,
    backgroundColor: theme.color.primaryContainer,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 2,
  },
  checkText: {
    fontFamily: theme.font.label,
    fontSize: 10,
    color: theme.color.onPrimary,
  },
});
