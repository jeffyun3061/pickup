import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Image, Pressable, StyleSheet, View } from 'react-native';

import { useCatalogImage } from '@/src/assets/useCatalogImage';
import { AppText } from '@/src/components/AppText';
import { formatRelativeTime, kindLabel, type ContentItem } from '@/src/domain/models';
import { bookmarkStore, readStore, useIdSet } from '@/src/state/idSetStore';
import { theme } from '@/src/theme/tokens';

type Props = {
  item: ContentItem;
  showSummary?: boolean;
  /** home: 홈 마이픽업용 / compact: 뉴스 피드 목록 */
  density?: 'compact' | 'home';
  /** 같은 게임의 읽지 않은 소식 묶음 개수. 홈 카드 안에서만 표시한다. */
  groupCount?: number;
};

/**
 * 피드/홈 공용 카드 — 토스식 가독성.
 * 정보 우선순위: 제목 > 요약 한 줄 > 게임·시간 메타.
 * 장식(스트라이프·HUD 배지·푸터 링크)은 걷어내고 여백과 타이포로만 위계를 만든다.
 */
export function FeedCard({
  item,
  showSummary = true,
  density = 'compact',
  groupCount,
}: Props) {
  const isHome = density === 'home';
  const accent =
    item.kind === 'popup' || item.kind === 'goods'
      ? theme.color.neonPurple
      : theme.color.neonYellow;
  const { source: thumb, isFallback, onError: onImageError } = useCatalogImage(
    item.imageUrl,
    item.imageKey,
  );
  const summary = showSummary ? item.summaryPoints[0] : undefined;
  useIdSet(readStore);
  useIdSet(bookmarkStore);
  const isRead = readStore.has(item.id);
  const isBookmarked = bookmarkStore.has(item.id);

  return (
    <Pressable
      onPress={() => {
        readStore.add(item.id);
        router.push(`/content/${item.id}`);
      }}
      accessibilityRole="button"
      accessibilityLabel={`${item.gameName} ${item.title}`}
      style={({ pressed }) => [
        styles.card,
        isHome && styles.cardHome,
        pressed && styles.pressed,
      ]}
    >
      <View style={[styles.thumb, isHome && styles.thumbHome]}>
        {thumb ? (
          <>
            <Image
              source={thumb}
              style={styles.thumbImage}
              resizeMode="cover"
              blurRadius={isFallback && item.themedFallback ? 3 : 0}
              onError={onImageError}
            />
            {isFallback && item.themedFallback ? (
              <View
                pointerEvents="none"
                style={[
                  styles.mockTint,
                  { backgroundColor: item.fallbackColor ?? theme.color.neonPurple },
                ]}
              />
            ) : null}
          </>
        ) : (
          <AppText style={styles.thumbText}>{item.gameName.slice(0, 1)}</AppText>
        )}
      </View>

      <View style={styles.body}>
        <View style={styles.metaRow}>
          <View style={[styles.dot, { backgroundColor: accent }]} />
          <AppText style={styles.game} numberOfLines={1}>
            {item.gameName} · {kindLabel(item.kind)}
          </AppText>
          {typeof groupCount === 'number' ? (
            <View style={styles.groupCount}>
              <AppText style={styles.groupCountText}>{groupCount}</AppText>
            </View>
          ) : null}
          {isBookmarked ? (
            <Ionicons name="bookmark" size={12} color={theme.color.neonYellow} />
          ) : null}
          <AppText style={styles.time} numberOfLines={1}>
            {formatRelativeTime(item.publishedAt)}
          </AppText>
        </View>

        <AppText
          style={[styles.title, isHome && styles.titleHome, isRead && styles.readTitle]}
          numberOfLines={2}
        >
          {item.title}
        </AppText>

        {summary ? (
          <AppText style={styles.summary} numberOfLines={1}>
            {summary}
          </AppText>
        ) : null}

      </View>

      <Ionicons
        name="chevron-forward"
        size={18}
        color={theme.color.textMuted}
        style={styles.chevron}
      />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.color.surfaceContainer,
    borderRadius: theme.radius.xl,
    padding: 10,
    marginBottom: 8,
    gap: 10,
  },
  cardHome: {
    padding: 12,
    marginBottom: 10,
  },
  pressed: {
    backgroundColor: theme.color.surfaceContainerHigh,
  },
  thumb: {
    width: 52,
    height: 52,
    borderRadius: theme.radius.md,
    backgroundColor: theme.color.surfaceContainerHighest,
    overflow: 'hidden',
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'flex-start',
    marginTop: 2,
  },
  thumbHome: {
    width: 58,
    height: 58,
  },
  thumbImage: {
    width: '100%',
    height: '100%',
  },
  mockTint: {
    ...StyleSheet.absoluteFill,
    opacity: 0.32,
  },
  thumbText: {
    fontFamily: theme.font.headline,
    fontSize: 22,
    color: theme.color.onSurface,
  },
  body: {
    flex: 1,
    minWidth: 0,
    gap: 4,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  game: {
    flex: 1,
    minWidth: 0,
    fontFamily: theme.font.bodySemi,
    fontSize: 12,
    color: theme.color.textMuted,
  },
  time: {
    flexShrink: 0,
    fontFamily: theme.font.body,
    fontSize: 11,
    color: theme.color.textMuted,
    opacity: 0.8,
  },
  title: {
    fontFamily: theme.font.bodySemi,
    fontSize: 15,
    lineHeight: 21,
    letterSpacing: -0.2,
    color: theme.color.onSurface,
  },
  titleHome: {
    fontSize: 16,
    lineHeight: 22,
  },
  summary: {
    fontFamily: theme.font.body,
    fontSize: 13,
    lineHeight: 18,
    color: theme.color.textMuted,
  },
  readTitle: {
    color: theme.color.textMuted,
  },
  groupCount: {
    minWidth: 16,
    alignItems: 'flex-end',
  },
  groupCountText: {
    fontFamily: theme.font.bodySemi,
    fontSize: 12,
    color: theme.color.neonYellow,
  },
  chevron: {
    flexShrink: 0,
  },
});
