import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useMemo, useState } from 'react';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';

import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { FeedCard } from '@/src/components/FeedCard';
import { OfflineBanner } from '@/src/components/OfflineBanner';
import { Screen } from '@/src/components/Screen';
import { SegmentedControl } from '@/src/components/SegmentedControl';
import { EmptyState, LoadingState } from '@/src/components/StateBlocks';
import { isOfflineKind, kindLabel, type ContentKind } from '@/src/domain/models';
import { useCatalog } from '@/src/hooks/useCatalog';
import { useApp } from '@/src/state/AppProvider';
import { theme } from '@/src/theme/tokens';

type Segment = 'mine' | 'all' | 'offline';

const KIND_CHIPS: Record<Segment, ContentKind[]> = {
  mine: ['update', 'event', 'popup', 'goods'],
  all: ['update', 'event'],
  offline: ['popup', 'goods'],
};

function isToday(iso: string): boolean {
  const d = new Date(iso);
  const now = new Date();
  return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate();
}

/** 소식 — 내 게임 기록을 기본으로 두고 전체/팝업·행사를 탐색한다. */
export default function NewsScreen() {
  const [segment, setSegment] = useState<Segment>('mine');
  const [kindFilter, setKindFilter] = useState<ContentKind | 'all'>('all');
  const [query, setQuery] = useState('');
  const { preferences } = useApp();
  const { loading, refreshing, offline, lastUpdatedAt, content, refresh } = useCatalog();

  const items = useMemo(() => {
    const q = query.trim().toLowerCase();
    return content
      .filter((item) => {
        if (segment === 'mine') return preferences.gameIds.includes(item.gameId);
        if (segment === 'offline') return isOfflineKind(item.kind);
        return !isOfflineKind(item.kind);
      })
      .filter((item) => (kindFilter === 'all' ? true : item.kind === kindFilter))
      .filter((item) => !q || item.title.toLowerCase().includes(q) || item.gameName.toLowerCase().includes(q))
      .sort((a, b) => +new Date(b.publishedAt) - +new Date(a.publishedAt));
  }, [content, segment, kindFilter, query, preferences.gameIds]);

  const todayCount = useMemo(() => items.filter((item) => isToday(item.publishedAt)).length, [items]);
  const chips = KIND_CHIPS[segment];

  return (
    <Screen refreshing={refreshing} onRefresh={() => void refresh()}>
      <AppHeader title="새 소식" />
      {offline ? <OfflineBanner lastUpdatedAt={lastUpdatedAt} onRetry={() => void refresh()} /> : null}
      <SegmentedControl
        value={segment}
        onChange={(next) => { setSegment(next); setKindFilter('all'); }}
        options={[{ value: 'mine', label: '내 게임' }, { value: 'all', label: '통합 소식' }, { value: 'offline', label: '팝업·행사' }]}
      />
      <View style={styles.searchBox}>
        <Ionicons name="search" size={16} color={theme.color.textMuted} />
        <TextInput value={query} onChangeText={setQuery} placeholder="게임·소식 검색" placeholderTextColor={theme.color.textMuted} style={styles.searchInput} returnKeyType="search" autoCorrect={false} />
        {query ? <Pressable onPress={() => setQuery('')} hitSlop={8}><Ionicons name="close-circle" size={16} color={theme.color.textMuted} /></Pressable> : null}
      </View>
      <View style={styles.chipRow}>
        {(['all', ...chips] as const).map((chip) => {
          const active = kindFilter === chip;
          return <Pressable key={chip} onPress={() => setKindFilter(chip)} style={[styles.chip, active && styles.chipActive]}><AppText style={[styles.chipText, active && styles.chipTextActive]}>{chip === 'all' ? '전체' : kindLabel(chip)}</AppText></Pressable>;
        })}
      </View>
      <View style={styles.count}><AppText variant="data">{loading ? '…' : `${items.length}건`}</AppText>{!loading && todayCount > 0 ? <AppText style={styles.today}>오늘 새 소식 {todayCount}건</AppText> : null}</View>
      {loading ? <LoadingState /> : null}
      {!loading && items.length === 0 ? query.trim() ? <EmptyState icon="search-outline" title="검색 결과가 없어요" description="다른 키워드로 검색해보세요." /> : <EmptyState icon="newspaper-outline" title={segment === 'mine' ? '내 게임 소식이 없어요' : segment === 'all' ? '통합 소식이 비어 있어요' : '팝업·행사가 비어 있어요'} description={segment === 'mine' ? '게임을 등록하면 해당 게임의 전체 기록이 모입니다.' : '검수 후 발행된 콘텐츠만 표시합니다.'} actionLabel={segment === 'mine' ? '내 게임 고르기' : undefined} onAction={segment === 'mine' ? () => router.push('/(tabs)/games') : undefined} /> : null}
      {items.map((item) => <FeedCard key={item.id} item={item} />)}
    </Screen>
  );
}

const styles = StyleSheet.create({
  searchBox: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: theme.color.surfaceContainer, borderWidth: 1, borderColor: theme.color.outlineVariant, borderRadius: theme.radius.sm, paddingHorizontal: 12, marginBottom: 12 },
  searchInput: { flex: 1, minWidth: 0, paddingVertical: 11, fontFamily: theme.font.body, fontSize: 13, color: theme.color.onSurface },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginBottom: 12 },
  chip: { paddingHorizontal: 11, paddingVertical: 7, borderRadius: 5, borderWidth: 1, borderColor: theme.color.outlineVariant, backgroundColor: theme.color.surfaceContainer },
  chipActive: { borderColor: theme.color.neonYellow, backgroundColor: 'rgba(202,255,0,0.12)' },
  chipText: { fontFamily: theme.font.bodySemi, fontSize: 11, color: theme.color.textMuted },
  chipTextActive: { color: theme.color.neonYellow },
  count: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8 },
  today: { fontFamily: theme.font.body, fontSize: 12, color: theme.color.neonYellow },
});
