import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { GameTile } from '@/src/components/GameTile';
import { Screen } from '@/src/components/Screen';
import { EmptyState, LoadingState } from '@/src/components/StateBlocks';
import { MAX_SELECTED_GAMES } from '@/src/domain/models';
import { useCatalog } from '@/src/hooks/useCatalog';
import { useApp } from '@/src/state/AppProvider';
import { theme } from '@/src/theme/tokens';

/**
 * 게임 카탈로그가 비어 있으면(운영 미등록) 선택 없이 진입 가능.
 * 카탈로그가 생기면 최소 1개 선택 후에만 시작 (제품 요구).
 */
export default function OnboardingScreen() {
  const { completeOnboarding } = useApp();
  const { loading, games } = useCatalog();
  const [selected, setSelected] = useState<string[]>([]);

  const catalogEmpty = !loading && games.length === 0;
  const canContinue = catalogEmpty || selected.length >= 1;

  const toggle = (id: string) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= MAX_SELECTED_GAMES) return prev;
      return [...prev, id];
    });
  };

  return (
    <Screen contentStyle={styles.content}>
      <AppHeader title="마이픽 시작" />
      <AppText variant="display" style={styles.hero}>
        관심 게임을{'\n'}고르세요
      </AppText>
      <AppText variant="caption" style={styles.desc}>
        선택한 게임 소식만 홈·알림에 모입니다. 게임 목록은 운영자가 등록한 뒤
        여기에 표시됩니다. 최대 {MAX_SELECTED_GAMES}개까지 고를 수 있어요.
      </AppText>

      {loading ? <LoadingState /> : null}

      {!loading && catalogEmpty ? (
        <EmptyState
          icon="construct-outline"
          title="등록된 게임이 아직 없어요"
          description="관리자가 게임을 등록하면 마이 픽에서 선택할 수 있어요. 지금은 앱 구조만 둘러볼 수 있습니다."
        />
      ) : null}

      <View style={styles.grid}>
        {games.map((game) => (
          <View key={game.id} style={styles.cell}>
            <GameTile
              game={game}
              selected={selected.includes(game.id)}
              onPress={() => toggle(game.id)}
            />
          </View>
        ))}
      </View>

      <Pressable
        disabled={!canContinue}
        onPress={async () => {
          await completeOnboarding(selected);
          router.replace('/(tabs)');
        }}
        style={({ pressed }) => [
          styles.cta,
          !canContinue && styles.ctaDisabled,
          pressed && canContinue && { opacity: 0.9 },
        ]}
      >
        <AppText style={styles.ctaText}>
          {catalogEmpty ? '둘러보기 시작' : '시작하기'}
        </AppText>
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: { paddingBottom: 48 },
  hero: {
    color: theme.color.onSurface,
    marginBottom: 8,
  },
  desc: { marginBottom: 20 },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -6,
  },
  cell: {
    width: '50%',
    paddingHorizontal: 6,
  },
  cta: {
    marginTop: 24,
    backgroundColor: theme.color.primaryContainer,
    borderRadius: theme.radius.sm,
    alignItems: 'center',
    paddingVertical: 16,
  },
  ctaDisabled: { backgroundColor: theme.color.surfaceContainerHighest },
  ctaText: {
    fontFamily: theme.font.label,
    color: theme.color.onPrimary,
    letterSpacing: 1.2,
  },
});
