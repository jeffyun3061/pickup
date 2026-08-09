import { Image, StyleSheet, View } from 'react-native';

import { resolveImage, type AppImageName } from '@/src/assets/images';
import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { Screen } from '@/src/components/Screen';
import { EmptyState, LoadingState } from '@/src/components/StateBlocks';
import type { RankingRow } from '@/src/domain/models';
import { useCatalog } from '@/src/hooks/useCatalog';
import { theme } from '@/src/theme/tokens';

function PodiumAvatar({
  row,
  size,
  borderColor,
}: {
  row: RankingRow;
  size: number;
  borderColor: string;
}) {
  const local = resolveImage(row.imageKey as AppImageName | undefined);
  const src = row.imageUrl ? { uri: row.imageUrl } : local;
  return (
    <View
      style={[
        styles.avatar,
        {
          width: size,
          height: size,
          borderRadius: size / 2,
          borderColor,
        },
      ]}
    >
      {src ? (
        <Image source={src} style={styles.avatarImg} resizeMode="cover" />
      ) : (
        <View style={[styles.avatarFallback, { backgroundColor: row.color }]}>
          <AppText style={styles.initial}>{row.initial}</AppText>
        </View>
      )}
    </View>
  );
}

/** 시안 ranking — 포디움 + 순위표 */
export default function RankingScreen() {
  const { loading, rankings } = useCatalog();
  const top1 = rankings.find((r) => r.rank === 1);
  const top2 = rankings.find((r) => r.rank === 2);
  const top3 = rankings.find((r) => r.rank === 3);
  const rest = rankings.filter((r) => r.rank > 3);

  return (
    <Screen>
      <AppHeader title="RANKING" />
      <View style={styles.hero}>
        <AppText variant="display" style={styles.title}>
          오늘의 PICK
        </AppText>
        <View style={styles.liveRow}>
          <View style={styles.liveDot} />
          <AppText variant="label">실시간 데일리 랭킹</AppText>
        </View>
      </View>

      {loading ? <LoadingState /> : null}

      {!loading && rankings.length === 0 ? (
        <EmptyState
          icon="trophy-outline"
          title="랭킹 데이터가 아직 없어요"
          description="사용자 관심 등록이 쌓이고 서버 집계가 연결되면 포디움·순위표가 채워집니다."
        />
      ) : null}

      {!loading && rankings.length > 0 ? (
        <View style={styles.podium}>
          {top2 ? (
            <View style={[styles.podCol, styles.podSide]}>
              <PodiumAvatar row={top2} size={56} borderColor={theme.color.neonPurple} />
              <AppText style={[styles.podRank, { color: theme.color.neonPurple }]}>2</AppText>
              <View style={[styles.podBlock, styles.podBlock2]}>
                <AppText variant="data" numberOfLines={1} style={styles.podName}>
                  {top2.gameName}
                </AppText>
                <AppText variant="data" style={{ color: theme.color.neonYellow }}>
                  {top2.interestCount.toLocaleString('ko-KR')}
                </AppText>
              </View>
            </View>
          ) : (
            <View style={styles.podSide} />
          )}

          {top1 ? (
            <View style={[styles.podCol, styles.podCenter]}>
              <AppText style={styles.star}>★</AppText>
              <PodiumAvatar row={top1} size={64} borderColor={theme.color.neonYellow} />
              <AppText style={[styles.podRank, { color: theme.color.neonYellow, fontSize: 26 }]}>
                1
              </AppText>
              <View style={[styles.podBlock, styles.podBlock1]}>
                <AppText variant="data" numberOfLines={1} style={[styles.podName, { fontWeight: '700' }]}>
                  {top1.gameName}
                </AppText>
                <AppText variant="data" style={{ color: theme.color.neonYellow }}>
                  {top1.interestCount.toLocaleString('ko-KR')}
                </AppText>
              </View>
            </View>
          ) : null}

          {top3 ? (
            <View style={[styles.podCol, styles.podSide]}>
              <PodiumAvatar row={top3} size={48} borderColor={theme.color.cyberOrange} />
              <AppText style={[styles.podRank, { color: theme.color.cyberOrange }]}>3</AppText>
              <View style={[styles.podBlock, styles.podBlock3]}>
                <AppText variant="data" numberOfLines={1} style={styles.podName}>
                  {top3.gameName}
                </AppText>
                <AppText variant="data" style={{ color: theme.color.neonYellow }}>
                  {top3.interestCount.toLocaleString('ko-KR')}
                </AppText>
              </View>
            </View>
          ) : (
            <View style={styles.podSide} />
          )}
        </View>
      ) : null}

      {rest.map((row) => {
        const local = resolveImage(row.imageKey as AppImageName | undefined);
        const src = row.imageUrl ? { uri: row.imageUrl } : local;
        return (
          <View key={row.gameId} style={styles.row}>
            <AppText style={styles.rank}>{row.rank}</AppText>
            <View style={styles.rowAvatar}>
              {src ? (
                <Image source={src} style={styles.rowImg} resizeMode="cover" />
              ) : (
                <View style={[styles.rowFallback, { backgroundColor: row.color }]}>
                  <AppText style={styles.initial}>{row.initial}</AppText>
                </View>
              )}
            </View>
            <View style={{ flex: 1, minWidth: 0 }}>
              <AppText variant="subtitle" numberOfLines={1}>
                {row.gameName}
              </AppText>
              <AppText variant="data">
                관심 {row.interestCount.toLocaleString('ko-KR')}
              </AppText>
            </View>
          </View>
        );
      })}
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: {
    alignItems: 'center',
    marginBottom: 20,
    paddingTop: 8,
  },
  title: {
    color: theme.color.onSurface,
    marginBottom: 10,
  },
  liveRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  liveDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: theme.color.neonYellow,
  },
  podium: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 24,
    minHeight: 200,
  },
  podCol: {
    alignItems: 'center',
    flex: 1,
  },
  podSide: { maxWidth: 110 },
  podCenter: { maxWidth: 130 },
  star: {
    color: theme.color.neonYellow,
    fontSize: 18,
    marginBottom: 4,
  },
  avatar: {
    borderWidth: 2,
    overflow: 'hidden',
    marginBottom: 6,
    backgroundColor: theme.color.surfaceContainerHigh,
  },
  avatarImg: { width: '100%', height: '100%' },
  avatarFallback: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  initial: {
    fontFamily: theme.font.headlineSemi,
    color: '#fff',
  },
  podRank: {
    fontFamily: theme.font.headline,
    fontSize: 20,
    marginBottom: 4,
  },
  podBlock: {
    width: '100%',
    alignItems: 'center',
    justifyContent: 'flex-start',
    paddingTop: 8,
    paddingHorizontal: 4,
    backgroundColor: theme.color.surfaceContainer,
    borderTopWidth: 1,
    gap: 2,
  },
  podBlock1: {
    height: 88,
    borderTopWidth: 2,
    borderTopColor: theme.color.neonYellow,
  },
  podBlock2: {
    height: 64,
    borderTopColor: theme.color.neonPurple,
  },
  podBlock3: {
    height: 52,
    borderTopColor: theme.color.cyberOrange,
  },
  podName: {
    color: theme.color.onSurface,
    textAlign: 'center',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: 'rgba(32, 31, 32, 0.8)',
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderLeftWidth: 2,
    borderRadius: theme.radius.md,
    padding: 12,
    marginBottom: 10,
  },
  rank: {
    width: 28,
    textAlign: 'center',
    fontFamily: theme.font.headline,
    fontSize: 20,
    color: theme.color.neonYellow,
  },
  rowAvatar: {
    width: 40,
    height: 40,
    borderRadius: 6,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
  },
  rowImg: { width: '100%', height: '100%' },
  rowFallback: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
