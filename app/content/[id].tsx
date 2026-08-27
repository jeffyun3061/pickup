import { Ionicons } from '@expo/vector-icons';
import * as Linking from 'expo-linking';
import { useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { Image, Pressable, Share, StyleSheet, View } from 'react-native';

import { useCatalogImage } from '@/src/assets/useCatalogImage';
import { imageAssets } from '@/src/assets/images';
import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { Screen } from '@/src/components/Screen';
import { EmptyState, LoadingState } from '@/src/components/StateBlocks';
import { catalogRepository } from '@/src/data/catalog';
import {
  formatKstDate,
  kindLabel,
  type ContentItem,
} from '@/src/domain/models';
import { bookmarkStore, readStore, useIdSet } from '@/src/state/idSetStore';
import { theme } from '@/src/theme/tokens';

function importanceLabel(value: 1 | 2 | 3): string {
  return value === 3 ? '높음' : value === 2 ? '보통' : '낮음';
}

function impactLabel(value: 'low' | 'medium' | 'high'): string {
  return value === 'high' ? '영향 큼' : value === 'medium' ? '일부 영향' : '영향 적음';
}

function communityLabel(value: 'positive' | 'mixed' | 'negative' | 'unknown'): string {
  switch (value) {
    case 'positive':
      return '긍정 반응';
    case 'mixed':
      return '의견이 엇갈림';
    case 'negative':
      return '아쉬운 반응';
    default:
      return '아직 확인 전';
  }
}

/** 한글 단어가 중간에서 끊기지 않도록 짧은 영향 문장을 두 줄로 나눈다. */
function formatImpactSummary(value: string): string {
  const text = value.replace(/\s+/g, ' ').trim();
  if (!text || text.includes('\n')) return text;
  const words = text.split(' ');
  if (words.length < 2) return text;

  const target = Math.ceil(text.length / 2);
  let cursor = 0;
  let splitAt = 1;
  let closest = Number.POSITIVE_INFINITY;
  for (let index = 1; index < words.length; index += 1) {
    cursor += words[index - 1].length + (index === 1 ? 0 : 1);
    const distance = Math.abs(cursor - target);
    if (cursor <= 20 && distance < closest) {
      splitAt = index;
      closest = distance;
    }
  }
  return `${words.slice(0, splitAt).join(' ')}\n${words.slice(splitAt).join(' ')}`;
}

export default function ContentDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [item, setItem] = useState<ContentItem | null>(null);
  const { source: cover, isFallback, onError: onImageError } = useCatalogImage(
    item?.imageUrl,
    item?.imageKey,
  );
  useIdSet(bookmarkStore);
  const bookmarked = item ? bookmarkStore.has(item.id) : false;

  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      try {
        const list = await catalogRepository.listContent('all', []);
        if (mounted) setItem(list.find((x) => x.id === id) ?? null);
      } catch {
        if (mounted) setItem(null);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [id]);

  useEffect(() => {
    if (item) readStore.add(item.id);
  }, [item]);

  const share = async () => {
    if (!item) return;
    try {
      await Share.share({
        message: `[${item.gameName}] ${item.title}\n${item.officialUrl}`,
      });
    } catch {
      /* 사용자가 공유 시트를 닫음 */
    }
  };

  if (loading) {
    return (
      <Screen>
        <AppHeader showBack brand title="소식 상세" rightSlot={null} />
        <LoadingState />
      </Screen>
    );
  }

  if (!item) {
    return (
      <Screen>
        <AppHeader showBack brand title="소식 상세" rightSlot={null} />
        <EmptyState
          title="소식을 찾을 수 없어요"
          description="아직 발행되지 않았거나 잘못된 링크입니다."
        />
      </Screen>
    );
  }

  return (
    <Screen>
      <AppHeader showBack brand title="소식 상세" rightSlot={null} />
      {cover ? (
        <View style={styles.coverWrap}>
          <Image
            source={cover}
            style={styles.cover}
            resizeMode="cover"
            blurRadius={isFallback && item.themedFallback ? 4 : 0}
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
          <View style={styles.coverBadge}>
            <AppText style={styles.coverBadgeText}>{kindLabel(item.kind)}</AppText>
          </View>
        </View>
      ) : null}
      <View style={styles.hero}>
        <View style={styles.heroTop}>
          <AppText variant="label" style={styles.heroGameName}>{item.gameName}</AppText>
          <View style={styles.heroActions}>
            <AppText variant="data" style={styles.publishedAt}>
              {formatKstDate(item.publishedAt)}
            </AppText>
            <Pressable
              onPress={() => bookmarkStore.toggle(item.id)}
              hitSlop={8}
              accessibilityRole="button"
              accessibilityLabel={bookmarked ? '북마크 해제' : '북마크'}
            >
              <Ionicons
                name={bookmarked ? 'bookmark' : 'bookmark-outline'}
                size={20}
                color={bookmarked ? theme.color.neonYellow : theme.color.textMuted}
              />
            </Pressable>
            <Pressable
              onPress={() => void share()}
              hitSlop={8}
              accessibilityRole="button"
              accessibilityLabel="공유"
            >
              <Ionicons name="share-social-outline" size={20} color={theme.color.textMuted} />
            </Pressable>
          </View>
        </View>
        <AppText variant="display" style={styles.title}>
          {item.title}
        </AppText>
      </View>

      {item.startsAt || item.endsAt || item.place ? (
        <View style={styles.block}>
          <AppText variant="label">일정·장소</AppText>
          {item.startsAt ? (
            <View style={styles.infoRow}>
              <Ionicons name="calendar-outline" size={15} color={theme.color.neonYellow} />
              <AppText variant="body">시작 {formatKstDate(item.startsAt)}</AppText>
            </View>
          ) : null}
          {item.endsAt ? (
            <View style={styles.infoRow}>
              <Ionicons name="time-outline" size={15} color={theme.color.neonYellow} />
              <AppText variant="body">종료 {formatKstDate(item.endsAt)}</AppText>
            </View>
          ) : null}
          {item.place ? (
            <View style={styles.infoRow}>
              <Ionicons name="location-outline" size={15} color={theme.color.neonYellow} />
              <AppText variant="body" style={{ flex: 1 }}>
                {item.place}
              </AppText>
            </View>
          ) : null}
          {item.reservationUrl ? (
            <Pressable
              onPress={() => void Linking.openURL(item.reservationUrl!)}
              style={styles.reserveBtn}
            >
              <Ionicons name="ticket-outline" size={16} color={theme.color.neonYellow} />
              <AppText style={styles.reserveText}>예약 페이지 열기</AppText>
            </Pressable>
          ) : null}
        </View>
      ) : null}
      <View style={styles.block}>
        <AppText variant="label">요약</AppText>
        {item.summaryPoints.map((point) => (
          <View key={point} style={styles.point}>
            <AppText style={{ color: theme.color.neonYellow }}>▶</AppText>
            <AppText variant="body" style={{ flex: 1 }}>
              {point}
            </AppText>
          </View>
        ))}
      </View>
      <View style={styles.analysisBlock}>
        <View style={styles.pikiHeader}>
          <Image source={imageAssets.pikiMascot} style={styles.pikiAvatar} resizeMode="contain" />
          <AppText style={styles.pikiName}>피키의 한마디</AppText>
        </View>
        <View style={styles.speechBubble}>
          <View style={styles.speechTail} />
        {item.analysis ? (
          <>
            <AppText variant="body" style={styles.analysisSummary} numberOfLines={3}>
              {formatImpactSummary(item.analysis.impactSummary)}
            </AppText>
            <View style={styles.analysisMetrics}>
              <View style={styles.analysisMetric}>
                <AppText style={styles.analysisKey}>중요도</AppText>
                <AppText style={styles.analysisValue}>
                  {importanceLabel(item.analysis.importance)} · {impactLabel(item.analysis.impactLevel)}
                </AppText>
              </View>
              <View style={styles.analysisMetric}>
                <AppText style={styles.analysisKey}>유저 반응</AppText>
                <AppText style={styles.analysisValue}>
                  {communityLabel(item.analysis.communitySentiment)}
                </AppText>
              </View>
            </View>
          </>
        ) : (
          <AppText variant="body" style={styles.analysisPending}>
            피키가 내용을 정리하고 있어요.
          </AppText>
        )}
        </View>
      </View>
      <Pressable
        onPress={() => void Linking.openURL(item.officialUrl)}
        style={styles.cta}
      >
        <Ionicons name="open-outline" size={18} color={theme.color.onPrimary} />
        <AppText style={styles.ctaText}>공식 원문 보기</AppText>
      </Pressable>
      <AppText variant="caption" style={styles.sourceNote} numberOfLines={2}>
        피키의 요약은 참고용이에요 · 자세한 내용은 공식 원문을 확인해 주세요.
      </AppText>
    </Screen>
  );
}

const styles = StyleSheet.create({
  coverWrap: {
    height: 180,
    borderRadius: theme.radius.lg,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    marginBottom: 14,
    backgroundColor: theme.color.surfaceContainerHighest,
  },
  cover: { width: '100%', height: '100%' },
  mockTint: {
    ...StyleSheet.absoluteFill,
    opacity: 0.34,
  },
  coverBadge: {
    position: 'absolute',
    top: 12,
    left: 12,
    backgroundColor: theme.color.primaryContainer,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 2,
  },
  coverBadgeText: {
    fontFamily: theme.font.label,
    fontSize: 10,
    color: theme.color.onPrimary,
  },
  hero: {
    backgroundColor: theme.color.surfaceContainer,
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.lg,
    padding: 18,
    gap: 10,
    marginBottom: 16,
  },
  heroTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
  },
  heroGameName: { flex: 1, minWidth: 0 },
  heroActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flexShrink: 0,
  },
  publishedAt: { color: theme.color.textMuted },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  reserveBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 4,
    paddingVertical: 12,
    borderRadius: theme.radius.sm,
    borderWidth: 1,
    borderColor: theme.color.neonYellow,
  },
  reserveText: {
    fontFamily: theme.font.label,
    fontSize: 12,
    letterSpacing: 1,
    color: theme.color.neonYellow,
  },
  title: { fontSize: 24, lineHeight: 30 },
  block: {
    backgroundColor: theme.color.surfaceContainer,
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.lg,
    padding: 16,
    gap: 10,
    marginBottom: 16,
  },
  point: { flexDirection: 'row', gap: 8, alignItems: 'flex-start' },
  analysisBlock: {
    backgroundColor: theme.color.surfaceContainer,
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.lg,
    padding: 14,
    gap: 8,
    marginBottom: 16,
  },
  pikiHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  pikiAvatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    borderWidth: 2,
    borderColor: theme.color.neonYellow,
    backgroundColor: 'rgba(208, 91, 255, 0.08)',
  },
  pikiName: {
    color: theme.color.neonYellow,
    fontFamily: theme.font.label,
    fontSize: 13,
  },
  speechBubble: {
    position: 'relative',
    backgroundColor: 'rgba(208, 91, 255, 0.09)',
    borderWidth: 1,
    borderColor: 'rgba(208, 91, 255, 0.3)',
    borderRadius: theme.radius.md,
    padding: 12,
    gap: 8,
  },
  speechTail: {
    position: 'absolute',
    top: -7,
    left: 20,
    width: 14,
    height: 14,
    backgroundColor: 'rgba(208, 91, 255, 0.09)',
    borderLeftWidth: 1,
    borderTopWidth: 1,
    borderColor: 'rgba(208, 91, 255, 0.3)',
    transform: [{ rotate: '45deg' }],
  },
  analysisMetrics: {
    flexDirection: 'row',
    gap: 8,
  },
  analysisMetric: {
    flex: 1,
    minWidth: 0,
    padding: 10,
    gap: 4,
    borderRadius: theme.radius.sm,
    backgroundColor: 'rgba(14, 14, 15, 0.34)',
  },
  analysisRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  analysisKey: {
    width: 92,
    color: theme.color.textMuted,
    fontFamily: theme.font.label,
    fontSize: 12,
  },
  analysisValue: {
    flex: 1,
    color: theme.color.onSurface,
    fontFamily: theme.font.label,
    fontSize: 13,
  },
  analysisSummary: { color: theme.color.onSurface, lineHeight: 21 },
  analysisPending: { color: theme.color.textMuted, lineHeight: 21 },
  cta: {
    backgroundColor: theme.color.primaryContainer,
    borderRadius: theme.radius.sm,
    paddingVertical: 14,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  ctaText: {
    fontFamily: theme.font.label,
    color: theme.color.onPrimary,
    letterSpacing: 1,
  },
  sourceNote: {
    marginTop: 8,
    marginBottom: 8,
    textAlign: 'center',
    color: theme.color.textMuted,
  },
});
