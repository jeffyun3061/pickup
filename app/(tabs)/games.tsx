import { router, type Href } from 'expo-router';
import { useEffect, useMemo, useRef, useState } from 'react';
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
import { Ionicons } from '@expo/vector-icons';

import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { GameTile } from '@/src/components/GameTile';
import { GameRegisterSlot } from '@/src/components/GameRegisterSlot';
import { PickSquadCard } from '@/src/components/PickSquadCard';
import { Screen } from '@/src/components/Screen';
import { EmptyState, LoadingState } from '@/src/components/StateBlocks';
import {
  countUnreadByGame,
  MAX_SELECTED_GAMES,
  reconcileGameIds,
  type Game,
} from '@/src/domain/models';
import {
  chunkPickSlots,
  PICK_PAGE_COUNT,
  PICK_SLOTS_PER_PAGE,
  type PickSlot,
} from '@/src/domain/pickSlots';
import { useCatalog } from '@/src/hooks/useCatalog';
import { readStore, useIdSet } from '@/src/state/idSetStore';
import { useApp } from '@/src/state/AppProvider';
import { resolvePickGrid } from '@/src/theme/layout';
import { theme } from '@/src/theme/tokens';

/** 마이픽 — 2×2(4칸) 페이지 두 장 + 가로 스와이프 + 게임 등록 슬롯 */
export default function GamesScreen() {
  const { preferences, setGameIds } = useApp();
  const { loading, offline, games, content } = useCatalog();
  const readIds = useIdSet(readStore);
  const [trackWidth, setTrackWidth] = useState(0);
  const [pageIndex, setPageIndex] = useState(0);
  const [pickerOpen, setPickerOpen] = useState(false);
  const pagerRef = useRef<FlatList<PickSlot[]> | null>(null);

  const selected = preferences.gameIds;
  const selectedKey = selected.join(',');
  const availableGameIdsKey = games.map((game) => game.id).join(',');

  // 오래된 설치에 남은 retired/삭제 게임을 API 성공 시에만 정리한다.
  // offline 캐시에서는 서버가 최신 카탈로그인지 알 수 없으므로 선택을 보존한다.
  useEffect(() => {
    if (loading || offline) return;
    const reconciled = reconcileGameIds(selected, games.map((game) => game.id));
    if (reconciled.join(',') !== selectedKey) void setGameIds(reconciled);
  }, [availableGameIdsKey, loading, offline, selectedKey, setGameIds]);

  const selectedGames = useMemo(
    () => selected.map((id) => games.find((g) => g.id === id)).filter(Boolean) as Game[],
    [selected, games],
  );
  const availableGames = useMemo(
    () => games.filter((g) => !selected.includes(g.id)),
    [games, selected],
  );

  const pages = useMemo(
    () => chunkPickSlots(selectedGames, PICK_SLOTS_PER_PAGE, PICK_PAGE_COUNT),
    [selectedGames],
  );
  const pickGrid = useMemo(() => resolvePickGrid(trackWidth), [trackWidth]);

  // 게임을 해제해 페이지 수가 줄어도 스크롤 인디케이터가 유효한 페이지를 가리키게 한다.
  useEffect(() => {
    const nextPage = Math.min(pageIndex, Math.max(0, pages.length - 1));
    if (nextPage !== pageIndex) setPageIndex(nextPage);
    if (trackWidth > 0) {
      requestAnimationFrame(() => {
        pagerRef.current?.scrollToOffset({
          offset: nextPage * trackWidth,
          animated: false,
        });
      });
    }
  }, [pages.length, trackWidth]);

  const unreadCountByGame = useMemo(
    () => countUnreadByGame(content, readIds),
    [content, readIds],
  );

  const removeGame = async (id: string) => {
    await setGameIds(selected.filter((x) => x !== id));
  };

  const addGame = async (id: string) => {
    if (selected.includes(id)) return;
    if (selected.length >= MAX_SELECTED_GAMES) return;
    // 선택 피드백은 로컬 상태로 즉시 반영한다. 서버 동기화가 느리거나
    // 오프라인이어도 선택창이 남아 사용자가 추가 실패로 오해하지 않게 한다.
    setPickerOpen(false);
    await setGameIds([...selected, id]);
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
    <Screen contentStyle={styles.screenBody}>
      <AppHeader title="마이픽" />
      <View style={styles.featureIntro}>
        <View style={styles.featureTitleLine}>
          <AppText style={styles.featureTitle}>MY PICK</AppText>
          <View style={styles.featureActions}>
            <AppText variant="data" style={styles.featureCount}>
              {selected.length}/{MAX_SELECTED_GAMES} GAMES
            </AppText>
            {selected.length < MAX_SELECTED_GAMES ? (
              <Pressable
                onPress={() => setPickerOpen(true)}
                accessibilityRole="button"
                accessibilityLabel="게임 추가"
                hitSlop={8}
                style={({ pressed }) => [styles.addButton, pressed && { opacity: 0.72 }]}
              >
                <Ionicons name="add" size={18} color={theme.color.onPrimary} />
              </Pressable>
            ) : null}
          </View>
        </View>
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
          style={[styles.pagerWrap, { height: pickGrid.pagerHeight }]}
          onLayout={(e) => setTrackWidth(e.nativeEvent.layout.width)}
        >
          {trackWidth > 0 ? (
            <FlatList
              ref={pagerRef}
              data={pages}
              style={[styles.pager, { height: pickGrid.gridHeight }]}
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
                <View style={[styles.page, { width: trackWidth, height: pickGrid.gridHeight }]}>
                  <View style={[styles.grid, { height: pickGrid.gridHeight }]}>
                    {page.map((slot) => (
                      <View
                        key={slot.kind === 'game' ? slot.game.id : slot.key}
                        style={[styles.cell, { height: pickGrid.cardHeight }]}
                      >
                        {slot.kind === 'game' ? (
                          <PickSquadCard
                            game={slot.game}
                            selected
                            hasNew={(unreadCountByGame.get(slot.game.id) ?? 0) > 0}
                            onPress={() => router.push(`/game/${slot.game.id}` as Href)}
                            onRemove={() => void removeGame(slot.game.id)}
                          />
                        ) : (
                          <GameRegisterSlot onPress={() => setPickerOpen(true)} />
                        )}
                      </View>
                    ))}
                  </View>
                </View>
              )}
            />
          ) : null}

          <View style={styles.pagerFooter}>
            <View style={styles.dots}>
              {pages.map((_, i) => (
                <View key={`dot-${i}`} style={[styles.dot, i === pageIndex && styles.dotActive]} />
              ))}
            </View>
            {pages.length > 1 ? (
              <AppText variant="data" style={styles.pagerHint}>
                {pageIndex + 1}/{pages.length} · 좌우로 넘겨 8칸 보기
              </AppText>
            ) : null}
          </View>
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
    flexGrow: 1,
    // 탭바가 콘텐츠 위에 떠도 페이지 안내가 가려지지 않게 한다.
    paddingBottom: 112,
  },
  featureIntro: {
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(68,73,51,0.45)',
    paddingBottom: 10,
    marginBottom: 10,
  },
  featureTitleLine: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  featureTitle: {
    fontFamily: theme.font.headline,
    fontSize: 32,
    lineHeight: 38,
    letterSpacing: -0.8,
    color: theme.color.onSurface,
  },
  featureCount: {
    color: theme.color.neonYellow,
    fontSize: 12,
    lineHeight: 16,
  },
  featureActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  addButton: {
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.color.primaryContainer,
  },
  pagerWrap: {
    // 카드 2×2와 페이지 안내를 함께 포함한다.
    flexShrink: 0,
  },
  pager: {
    flexGrow: 0,
  },
  page: {
    flexShrink: 0,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    alignContent: 'flex-start',
    gap: 12,
  },
  cell: {
    width: '48%',
    flexGrow: 0,
    flexShrink: 0,
  },
  pagerFooter: {
    alignItems: 'center',
    gap: 6,
    minHeight: 44,
    marginTop: 6,
    paddingBottom: 2,
  },
  dots: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 10,
  },
  pagerHint: {
    color: theme.color.onSurfaceVariant,
    fontSize: 9,
    lineHeight: 11,
    letterSpacing: 0.2,
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
