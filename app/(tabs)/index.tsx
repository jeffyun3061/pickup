import { Image, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';

import { imageAssets } from '@/src/assets/images';
import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { FeedCard } from '@/src/components/FeedCard';
import { Screen } from '@/src/components/Screen';
import { EmptyState, LoadingState } from '@/src/components/StateBlocks';
import { catalogMode } from '@/src/data/catalog';
import { useCatalog } from '@/src/hooks/useCatalog';
import { useApp } from '@/src/state/AppProvider';
import { useLayout } from '@/src/theme/useLayout';
import { theme } from '@/src/theme/tokens';

/** 시안 _2 홈: Piky 가이드 + 마이 픽업 소식 */
export default function HomeScreen() {
  const { preferences } = useApp();
  const { loading, mine, content } = useCatalog();
  const layout = useLayout();
  const selectedCount = preferences.gameIds.length;
  const previewBrowse =
    (catalogMode === 'preview' || catalogMode === 'api') &&
    selectedCount === 0 &&
    content.length > 0;
  const feed = selectedCount > 0 ? mine : previewBrowse ? content.slice(0, 5) : [];

  return (
    <Screen contentStyle={styles.screenContent}>
      <AppHeader title="HOME" />

      <View style={styles.guide}>
        <View style={styles.avatar}>
          <Image source={imageAssets.mascot} style={styles.avatarImage} resizeMode="cover" />
        </View>
        <View style={{ flex: 1 }}>
          <AppText variant="label" style={{ marginBottom: 6 }}>
            피키 가이드
          </AppText>
          <AppText variant="body" style={styles.guideBody}>
            {selectedCount === 0
              ? previewBrowse
                ? '안녕! 시안 미리보기 소식을 먼저 보여줄게. 마이 픽을 고르면 맞춤 피드로 바뀌어.'
                : '안녕! 마이 픽에서 관심 게임을 고르면, 피키가 검수된 소식만 모아줄게.'
              : `관심 게임 ${selectedCount}개 기준으로 홈을 구성해둘게. 오늘 확인할 소식이 ${mine.length}건이야.`}
          </AppText>
        </View>
      </View>

      <View style={styles.sectionHead}>
        <View style={styles.sectionTitles}>
          <AppText variant="title" style={{ fontSize: layout.titleSize }} numberOfLines={1}>
            마이 픽업 소식
          </AppText>
          <AppText variant="caption" style={styles.sectionCaption}>
            선택한 게임의 검수된 업데이트만 모아요
          </AppText>
        </View>
        <AppText variant="data" style={styles.sectionStatus}>
          {loading
            ? '동기화'
            : previewBrowse
              ? '미리보기'
              : mine.length === 0
                ? '대기'
                : `${feed.length}건`}
        </AppText>
      </View>

      {loading ? <LoadingState /> : null}

      {!loading && selectedCount === 0 && !previewBrowse ? (
        <EmptyState
          icon="game-controller-outline"
          title="마이 픽이 비어 있어요"
          description="내 게임을 선택하면 홈에 해당 소식만 모입니다."
          actionLabel="마이 픽으로"
          onAction={() => router.push('/(tabs)/games')}
        />
      ) : null}

      {!loading && selectedCount > 0 && mine.length === 0 ? (
        <EmptyState
          icon="newspaper-outline"
          title="아직 발행된 소식이 없어요"
          description="운영자가 검수·발행하면 여기에 표시됩니다."
          actionLabel="뉴스 피드 보기"
          onAction={() => router.push('/(tabs)/news')}
        />
      ) : null}

      {previewBrowse ? (
        <View style={styles.banner}>
          <AppText variant="data" style={{ color: theme.color.neonYellow }}>
            PREVIEW · 마이 픽을 고르면 맞춤으로 전환
          </AppText>
        </View>
      ) : null}

      <View style={styles.feedList}>
        {feed.map((item) => (
          <FeedCard key={item.id} item={item} showSummary density="home" />
        ))}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screenContent: {
    paddingBottom: 120,
  },
  guide: {
    flexDirection: 'row',
    gap: 14,
    padding: 16,
    backgroundColor: 'rgba(32, 31, 32, 0.85)',
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.lg,
    marginBottom: theme.space.section,
  },
  guideBody: {
    lineHeight: 22,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    borderWidth: 2,
    borderColor: theme.color.neonYellow,
    overflow: 'hidden',
    backgroundColor: theme.color.surfaceContainerHigh,
  },
  avatarImage: {
    width: '100%',
    height: '100%',
  },
  sectionHead: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    borderBottomWidth: 1,
    borderBottomColor: theme.color.outlineVariant,
    paddingBottom: 14,
    marginBottom: 18,
    gap: 12,
  },
  sectionTitles: {
    flex: 1,
    minWidth: 0,
    gap: 6,
  },
  sectionCaption: {
    color: theme.color.textMuted,
  },
  sectionStatus: {
    marginBottom: 2,
    color: theme.color.neonYellow,
  },
  banner: {
    marginBottom: 16,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,215,0,0.35)',
    backgroundColor: 'rgba(255,215,0,0.08)',
    borderRadius: theme.radius.sm,
  },
  feedList: {
    gap: 0,
    paddingBottom: 16,
  },
});
