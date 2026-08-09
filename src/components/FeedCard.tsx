import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Image, Pressable, StyleSheet, View } from 'react-native';

import { resolveImage, type AppImageName } from '@/src/assets/images';
import { AppText } from '@/src/components/AppText';
import { formatKstDate, kindLabel, type ContentItem } from '@/src/domain/models';
import { useLayout } from '@/src/theme/useLayout';
import { theme } from '@/src/theme/tokens';

type Props = {
  item: ContentItem;
  showSummary?: boolean;
  /** home: 홈 마이픽업용 큰 카드 / compact: 뉴스 피드 목록 */
  density?: 'compact' | 'home';
};

/**
 * 피드/홈 공용 카드.
 * 홈(density=home)은 썸네일·타이포·카드 간격을 넓혀 가독성을 우선한다.
 */
export function FeedCard({
  item,
  showSummary = false,
  density = 'compact',
}: Props) {
  const layout = useLayout();
  const isHome = density === 'home';
  const accent =
    item.kind === 'popup' || item.kind === 'goods'
      ? theme.color.neonPurple
      : theme.color.neonYellow;
  const localThumb = resolveImage(item.imageKey as AppImageName | undefined);
  const thumb = item.imageUrl
    ? { uri: item.imageUrl }
    : localThumb;
  const thumbWidth = isHome ? layout.homeFeedThumb : layout.feedThumb;
  const summaryPoints = showSummary
    ? item.summaryPoints.slice(0, isHome ? 2 : 3)
    : [];

  return (
    <Pressable
      onPress={() => router.push(`/content/${item.id}`)}
      accessibilityRole="button"
      accessibilityLabel={`${item.gameName} ${item.title}`}
      style={({ pressed }) => [
        styles.card,
        isHome && styles.cardHome,
        pressed && styles.pressed,
      ]}
    >
      <View style={[styles.stripe, { backgroundColor: accent }]} />
      <View
        style={[
          styles.thumb,
          isHome && styles.thumbHome,
          {
            width: thumbWidth,
            backgroundColor: theme.color.surfaceContainerHighest,
          },
        ]}
      >
        {thumb ? (
          <Image source={thumb} style={styles.thumbImage} resizeMode="cover" />
        ) : (
          <AppText style={[styles.thumbText, isHome && { fontSize: 32 }]}>
            {item.gameName.slice(0, 1)}
          </AppText>
        )}
        <View style={[styles.badge, isHome && styles.badgeHome, { backgroundColor: accent }]}>
          <AppText style={[styles.badgeText, isHome && styles.badgeTextHome]} numberOfLines={1}>
            {kindLabel(item.kind)}
          </AppText>
        </View>
      </View>
      <View style={[styles.body, isHome && styles.bodyHome]}>
        <View style={styles.meta}>
          <AppText
            style={[styles.game, isHome && styles.gameHome, { color: accent }]}
            numberOfLines={1}
          >
            {item.gameName}
          </AppText>
          <AppText
            variant="data"
            style={[styles.time, isHome && styles.timeHome]}
            numberOfLines={1}
          >
            {formatKstDate(item.publishedAt)}
          </AppText>
        </View>
        <AppText
          variant="subtitle"
          numberOfLines={2}
          style={[styles.title, isHome && styles.titleHome]}
        >
          {item.title}
        </AppText>
        {summaryPoints.length > 0 ? (
          <View style={[styles.points, isHome && styles.pointsHome]}>
            {summaryPoints.map((p) => (
              <View key={p} style={[styles.point, isHome && styles.pointHome]}>
                <AppText style={{ color: accent, fontSize: 10, marginTop: 1 }}>
                  ▶
                </AppText>
                <AppText
                  style={[styles.pointText, isHome && styles.pointTextHome]}
                  numberOfLines={isHome ? 2 : 2}
                >
                  {p}
                </AppText>
              </View>
            ))}
          </View>
        ) : null}
        <View style={[styles.footer, isHome && styles.footerHome]}>
          <AppText style={[styles.more, isHome && styles.moreHome, { color: accent }]}>
            정보
          </AppText>
          <Ionicons name="arrow-forward" size={isHome ? 16 : 14} color={accent} />
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    backgroundColor: 'rgba(32, 31, 32, 0.88)',
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.lg,
    overflow: 'hidden',
    marginBottom: theme.space.gutter,
    minHeight: 112,
  },
  cardHome: {
    minHeight: 124,
    marginBottom: 14,
    borderRadius: theme.radius.lg,
    backgroundColor: theme.color.surfaceContainer,
  },
  pressed: {
    opacity: 0.92,
  },
  stripe: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 2,
    zIndex: 2,
  },
  thumb: {
    justifyContent: 'center',
    alignItems: 'center',
    borderRightWidth: 1,
    borderRightColor: theme.color.outlineVariant,
    flexShrink: 0,
    overflow: 'hidden',
    alignSelf: 'stretch',
  },
  thumbHome: {
    borderRightWidth: 0,
  },
  thumbImage: {
    ...StyleSheet.absoluteFill,
    opacity: 1,
  },
  thumbText: {
    fontFamily: theme.font.headline,
    fontSize: 26,
    color: theme.color.onSurface,
  },
  badge: {
    position: 'absolute',
    top: 8,
    left: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 2,
    zIndex: 1,
  },
  badgeHome: {
    top: 10,
    left: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  badgeText: {
    fontFamily: theme.font.labelReg,
    fontSize: 9,
    color: theme.color.onPrimary,
  },
  badgeTextHome: {
    fontSize: 10,
  },
  body: {
    flex: 1,
    minWidth: 0,
    padding: 12,
    gap: 6,
    justifyContent: 'space-between',
  },
  bodyHome: {
    paddingVertical: 11,
    paddingHorizontal: 12,
    gap: 5,
  },
  meta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 8,
  },
  game: {
    fontFamily: theme.font.label,
    fontSize: 10,
    letterSpacing: 1,
    flex: 1,
    minWidth: 0,
  },
  gameHome: {
    fontSize: 11,
    letterSpacing: 1.2,
  },
  time: {
    flexShrink: 0,
  },
  timeHome: {
    fontSize: 11,
    lineHeight: 14,
  },
  title: {
    color: theme.color.onSurface,
    flexShrink: 1,
  },
  titleHome: {
    fontSize: 15,
    lineHeight: 21,
    letterSpacing: -0.2,
  },
  points: {
    gap: 4,
  },
  pointsHome: {
    gap: 4,
    marginTop: 0,
    paddingLeft: 0,
    borderLeftWidth: 0,
    paddingVertical: 0,
  },
  point: {
    flexDirection: 'row',
    gap: 6,
    alignItems: 'flex-start',
  },
  pointHome: {
    gap: 6,
    paddingLeft: 0,
  },
  pointText: {
    flex: 1,
    minWidth: 0,
    fontFamily: theme.font.body,
    fontSize: 13,
    lineHeight: 18,
    color: theme.color.onSurfaceVariant,
  },
  pointTextHome: {
    fontSize: 12,
    lineHeight: 17,
    color: theme.color.onSurfaceVariant,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    alignItems: 'center',
    gap: 4,
  },
  footerHome: {
    marginTop: 2,
    paddingTop: 4,
    borderTopWidth: 0,
  },
  more: {
    fontFamily: theme.font.label,
    fontSize: 10,
    letterSpacing: 1,
  },
  moreHome: {
    fontSize: 10,
  },
});
