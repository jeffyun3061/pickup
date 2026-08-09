import { useMemo, useRef, useState } from 'react';
import {
  FlatList,
  Modal,
  Pressable,
  StyleSheet,
  View,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
  type ViewToken,
} from 'react-native';

import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { GameRegisterSlot } from '@/src/components/GameRegisterSlot';
import { GameTile } from '@/src/components/GameTile';
import { PickSquadCard } from '@/src/components/PickSquadCard';
import { Screen } from '@/src/components/Screen';
import { EmptyState, LoadingState } from '@/src/components/StateBlocks';
import type { Game } from '@/src/domain/models';
import { useCatalog } from '@/src/hooks/useCatalog';
import { useApp } from '@/src/state/AppProvider';
import { useLayout } from '@/src/theme/useLayout';
import { theme } from '@/src/theme/tokens';

const SLOTS_PER_PAGE = 4;

type Slot =
  | { kind: 'game'; game: Game }
  | { kind: 'register'; key: string };

function chunkSlots(slots: Slot[], size: number): Slot[][] {
  if (slots.length === 0) {
    return [
      Array.from({ length: size }, (_, i) => ({
        kind: 'register' as const,
        key: `r-empty-${i}`,
      })),
    ];
  }
  const pages: Slot[][] = [];
  for (let i = 0; i < slots.length; i += size) {
    const page = slots.slice(i, i + size);
    while (page.length < size) {
      page.push({ kind: 'register', key: `r-pad-${i}-${page.length}` });
    }
    pages.push(page);
  }
  return pages;
}

/** 시안 my_pick — 2×2(4칸) 페이지 + 가로 스와이프 + 게임 등록 슬롯 */
export default function GamesScreen() {
  const { preferences, setGameIds } = useApp();
  const { loading, games, content } = useCatalog();
  const layout = useLayout();
  const [trackWidth, setTrackWidth] = useState(0);
  const [pageIndex, setPageIndex] = useState(0);
  const [pickerOpen, setPickerOpen] = useState(false);

  const selected = preferences.gameIds;
  const selectedGames = useMemo(
    () => selected.map((id) => games.find((g) => g.id === id)).filter(Boolean) as Game[],
    [selected, games],
  );
  const availableGames = useMemo(
    () => games.filter((g) => !selected.includes(g.id)),
    [games, selected],
  );

  const pages = useMemo(() => {
    const slots: Slot[] = selectedGames.map((game) => ({ kind: 'game', game }));
    const registerCount =
      availableGames.length === 0
        ? selectedGames.length === 0
          ? SLOTS_PER_PAGE
          : 0
        : Math.max(availableGames.length, selectedGames.length === 0 ? SLOTS_PER_PAGE : 1);
    for (let i = 0; i < registerCount; i += 1) {
      slots.push({ kind: 'register', key: `r-${i}` });
    }
    return chunkSlots(slots, SLOTS_PER_PAGE);
  }, [selectedGames, availableGames.length]);

  const newsCountByGame = useMemo(() => {
    const map = new Map<string, number>();
    for (const item of content) {
      map.set(item.gameId, (map.get(item.gameId) ?? 0) + 1);
    }
    return map;
  }, [content]);

  const removeGame = async (id: string) => {
    await setGameIds(selected.filter((x) => x !== id));
  };

  const addGame = async (id: string) => {
    if (selected.includes(id)) return;
    await setGameIds([...selected, id]);
    setPickerOpen(false);
  };

  const onMomentumEnd = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    if (trackWidth <= 0) return;
    const next = Math.round(e.nativeEvent.contentOffset.x / trackWidth);
    setPageIndex(Math.min(Math.max(next, 0), pages.length - 1));
  };

  const onViewableItemsChanged = useRef(
    ({ viewableItems }: { viewableItems: ViewToken[] }) => {
      const idx = viewableItems[0]?.index;
      if (typeof idx === 'number') setPageIndex(idx);
    },
  ).current;

  return (
    <Screen scroll={false} contentStyle={styles.screenBody}>
      <AppHeader title="MY PICK" />
      <View style={styles.heroBlock}>
        <AppText variant="display" style={[styles.hero, { fontSize: layout.displaySize }]}>
          마이픽
        </AppText>
        <AppText variant="label" style={styles.sub}>
          피키가 관리하는 내 게임들
        </AppText>
        <AppText variant="caption">
          선택 {selected.length}개 · 한 화면 4칸 · 옆으로 넘겨 등록
        </AppText>
      </View>

      {loading ? <LoadingState /> : null}

      {!loading && games.length === 0 ? (
        <EmptyState
          icon="apps-outline"
          title="선택 가능한 게임이 없어요"
          description="운영자가 게임을 등록하면 여기에서 마이 픽을 고를 수 있어요."
        />
      ) : null}

      {!loading && games.length > 0 ? (
        <View
          style={styles.pagerWrap}
          onLayout={(e) => setTrackWidth(e.nativeEvent.layout.width)}
        >
          {trackWidth > 0 ? (
            <FlatList
              data={pages}
              keyExtractor={(_, index) => `page-${index}`}
              horizontal
              pagingEnabled
              decelerationRate="fast"
              showsHorizontalScrollIndicator={false}
              onMomentumScrollEnd={onMomentumEnd}
              onViewableItemsChanged={onViewableItemsChanged}
              viewabilityConfig={{ itemVisiblePercentThreshold: 60 }}
              getItemLayout={(_, index) => ({
                length: trackWidth,
                offset: trackWidth * index,
                index,
              })}
              renderItem={({ item: page }) => (
                <View style={[styles.page, { width: trackWidth }]}>
                  <View style={styles.grid}>
                    {page.map((slot) => (
                      <View
                        key={slot.kind === 'game' ? slot.game.id : slot.key}
                        style={styles.cell}
                      >
                        {slot.kind === 'game' ? (
                          <PickSquadCard
                            game={slot.game}
                            selected
                            badgeLabel={
                              (newsCountByGame.get(slot.game.id) ?? 0) > 0
                                ? newsCountByGame.get(slot.game.id) === 1
                                  ? '새로운 소식'
                                  : `${newsCountByGame.get(slot.game.id)} 알림`
                                : undefined
                            }
                            badgeTone={
                              (newsCountByGame.get(slot.game.id) ?? 0) > 1
                                ? 'purple'
                                : 'yellow'
                            }
                            onPress={() => void removeGame(slot.game.id)}
                            onLongPress={() => void removeGame(slot.game.id)}
                          />
                        ) : (
                          <GameRegisterSlot
                            disabled={availableGames.length === 0}
                            onPress={() => setPickerOpen(true)}
                          />
                        )}
                      </View>
                    ))}
                  </View>
                </View>
              )}
            />
          ) : null}

          <View style={styles.dots}>
            {pages.map((_, i) => (
              <View key={`dot-${i}`} style={[styles.dot, i === pageIndex && styles.dotActive]} />
            ))}
          </View>
          <AppText variant="data" style={styles.hint}>
            카드를 탭하면 해제 · 빈 칸에서 게임 등록
          </AppText>
        </View>
      ) : null}

      <Modal
        visible={pickerOpen}
        animationType="slide"
        transparent
        onRequestClose={() => setPickerOpen(false)}
      >
        <Pressable style={styles.modalBackdrop} onPress={() => setPickerOpen(false)}>
          <Pressable style={styles.sheet} onPress={(e) => e.stopPropagation()}>
            <View style={styles.sheetHandle} />
            <AppText variant="title" style={styles.sheetTitle}>
              게임 등록
            </AppText>
            <AppText variant="caption" style={styles.sheetSub}>
              관심 게임을 고르면 마이픽 칸에 들어갑니다
            </AppText>
            {availableGames.length === 0 ? (
              <EmptyState
                icon="checkmark-circle-outline"
                title="더 등록할 게임이 없어요"
                description="카탈로그에 남은 게임이 없습니다."
              />
            ) : (
              <FlatList
                data={availableGames}
                keyExtractor={(g) => g.id}
                numColumns={2}
                columnWrapperStyle={styles.pickerRow}
                contentContainerStyle={styles.pickerList}
                renderItem={({ item }) => (
                  <View style={styles.pickerCell}>
                    <GameTile game={item} onPress={() => void addGame(item.id)} />
                  </View>
                )}
              />
            )}
            <Pressable style={styles.closeBtn} onPress={() => setPickerOpen(false)}>
              <AppText style={styles.closeText}>닫기</AppText>
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screenBody: {
    flex: 1,
  },
  heroBlock: {
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(68,73,51,0.45)',
    paddingBottom: 14,
    marginBottom: 16,
  },
  hero: {
    color: theme.color.onSurface,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  sub: { marginBottom: 6 },
  pagerWrap: {
    flex: 1,
    minHeight: 380,
  },
  page: {
    height: 500,
  },
  grid: {
    flex: 1,
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    alignContent: 'space-between',
    gap: 12,
    height: 500,
  },
  cell: {
    width: '48%',
    height: '48%',
  },
  dots: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 10,
    marginTop: 18,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: theme.color.surfaceContainerHighest,
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
  },
  dotActive: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: theme.color.neonYellow,
    borderColor: theme.color.neonYellow,
  },
  hint: {
    textAlign: 'center',
    marginTop: 12,
    color: theme.color.textMuted,
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.55)',
    justifyContent: 'flex-end',
  },
  sheet: {
    maxHeight: '78%',
    backgroundColor: theme.color.surfaceContainer,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    borderTopWidth: 1,
    borderColor: theme.color.outlineVariant,
    paddingHorizontal: 16,
    paddingBottom: 28,
    paddingTop: 10,
  },
  sheetHandle: {
    alignSelf: 'center',
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: theme.color.outlineVariant,
    marginBottom: 14,
  },
  sheetTitle: {
    color: theme.color.onSurface,
    marginBottom: 6,
  },
  sheetSub: { marginBottom: 14 },
  pickerList: { paddingBottom: 8 },
  pickerRow: { gap: 10 },
  pickerCell: { flex: 1 },
  closeBtn: {
    marginTop: 8,
    alignItems: 'center',
    paddingVertical: 14,
    borderRadius: theme.radius.sm,
    backgroundColor: theme.color.surfaceContainerHigh,
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
  },
  closeText: {
    fontFamily: theme.font.label,
    color: theme.color.onSurface,
    letterSpacing: 1,
  },
});
