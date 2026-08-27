import { useLocalSearchParams } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { FeedCard } from '@/src/components/FeedCard';
import { Screen } from '@/src/components/Screen';
import { EmptyState, LoadingState } from '@/src/components/StateBlocks';
import { useCatalog } from '@/src/hooks/useCatalog';
import { theme } from '@/src/theme/tokens';

/** 마이픽 카드에서 진입하는 게임별 소식 요약 */
export default function GameNewsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { loading, games, content } = useCatalog();
  const game = games.find((item) => item.id === id);
  const items = content
    .filter((item) => item.gameId === id)
    .sort((a, b) => +new Date(b.publishedAt) - +new Date(a.publishedAt));

  return (
    <Screen>
      <AppHeader showBack title="게임 소식" rightSlot={null} />

      {loading ? <LoadingState /> : null}

      {!loading && game ? (
        <View style={styles.summary}>
          <View style={[styles.dot, { backgroundColor: game.color }]} />
          <View style={styles.summaryText}>
            <AppText style={styles.gameName} numberOfLines={1}>
              {game.name}
            </AppText>
            <AppText variant="caption">
              최신 소식 {items.length}건을 모아봤어요
            </AppText>
          </View>
        </View>
      ) : null}

      {!loading && !game ? (
        <EmptyState
          icon="game-controller-outline"
          title="게임을 찾을 수 없어요"
          description="카탈로그에서 제거됐거나 아직 동기화되지 않았습니다."
        />
      ) : null}

      {!loading && game && items.length === 0 ? (
        <EmptyState
          icon="newspaper-outline"
          title="아직 새 소식이 없어요"
          description="검수된 소식이 발행되면 여기에 표시됩니다."
        />
      ) : null}

      {items.map((item) => (
        <FeedCard key={item.id} item={item} />
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  summary: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingBottom: 14,
    marginBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: theme.color.outlineVariant,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  summaryText: {
    flex: 1,
    minWidth: 0,
    gap: 2,
  },
  gameName: {
    fontFamily: theme.font.bodySemi,
    fontSize: 18,
    color: theme.color.onSurface,
  },
});
