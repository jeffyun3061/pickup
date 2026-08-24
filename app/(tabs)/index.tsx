import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { useMemo, useState } from 'react';
import { Image, Pressable, RefreshControl, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { imageAssets } from '@/src/assets/images';
import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { FeedCard } from '@/src/components/FeedCard';
import { OfflineBanner } from '@/src/components/OfflineBanner';
import { EmptyState, LoadingState } from '@/src/components/StateBlocks';
import { catalogMode } from '@/src/data/catalog';
import {
  eventCountdownLabel,
  formatRelativeTime,
  isActiveTimeBound,
  timeBoundTypeLabel,
  type ContentItem,
} from '@/src/domain/models';
import { useCatalog } from '@/src/hooks/useCatalog';
import { readStore, useIdSet } from '@/src/state/idSetStore';
import { useApp } from '@/src/state/AppProvider';
import { useLayout } from '@/src/theme/useLayout';
import { theme } from '@/src/theme/tokens';

type HomeTab = 'news' | 'events';
type NewsGroup = { gameId: string; gameName: string; items: ContentItem[]; missed: boolean };

function isToday(iso: string, now = new Date()): boolean {
  const date = new Date(iso);
  return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth() && date.getDate() === now.getDate();
}

function groupUnread(items: ContentItem[], readIds: string[]): NewsGroup[] {
  const groups = new Map<string, NewsGroup>();
  for (const item of items.filter((candidate) => !readIds.includes(candidate.id))) {
    const group = groups.get(item.gameId) ?? { gameId: item.gameId, gameName: item.gameName, items: [], missed: true };
    group.items.push(item);
    group.missed = group.missed && !isToday(item.publishedAt);
    groups.set(item.gameId, group);
  }
  return [...groups.values()]
    .map((group) => ({ ...group, items: [...group.items].sort((a, b) => (b.importance ?? 0) - (a.importance ?? 0) || +new Date(b.publishedAt) - +new Date(a.publishedAt)) }))
    .sort((a, b) => +new Date(b.items[0].publishedAt) - +new Date(a.items[0].publishedAt));
}

function NewsGroupCard({ group }: { group: NewsGroup }) {
  const featured = group.items[0];
  return (
    <View style={styles.group}>
      <FeedCard item={featured} density="home" groupCount={group.items.length} />
      {group.items.length > 1 ? (
        <View style={styles.moreItems}>
          {group.items.slice(1).map((item) => (
            <Pressable key={item.id} onPress={() => { readStore.add(item.id); router.push(`/content/${item.id}`); }} style={({ pressed }) => [styles.moreItem, pressed && styles.moreItemPressed]} accessibilityRole="button" accessibilityLabel={`${item.gameName} ${item.title}`}>
              <View style={styles.moreDot} />
              <AppText style={styles.moreTitle} numberOfLines={1}>{item.title}</AppText>
              <AppText style={styles.moreTime}>{formatRelativeTime(item.publishedAt)}</AppText>
            </Pressable>
          ))}
        </View>
      ) : null}
    </View>
  );
}

function EventPeriodCard({ item }: { item: ContentItem }) {
  const type = item.timeBoundType ?? (item.kind === 'event' ? 'event' : item.kind === 'popup' ? 'popup' : 'goods');
  return (
    <View style={styles.eventCard}>
      <View style={styles.eventTop}>
        <View style={styles.eventBadge}><AppText style={styles.eventBadgeText}>{timeBoundTypeLabel(type)}</AppText></View>
        <AppText style={styles.eventCountdown}>{eventCountdownLabel(item.endsAt)}</AppText>
      </View>
      <AppText style={styles.eventTitle} numberOfLines={2}>{item.title}</AppText>
      <AppText style={styles.eventGame} numberOfLines={1}>{item.gameName}</AppText>
    </View>
  );
}

/** 홈 — 매일 확인하는 개인화 요약 대시보드 */
export default function HomeScreen() {
  const layout = useLayout();
  const { preferences, setGameIds } = useApp();
  const { loading, refreshing, offline, lastUpdatedAt, mine, content, games, refresh } = useCatalog();
  const readIds = useIdSet(readStore);
  const [homeTab, setHomeTab] = useState<HomeTab>('news');
  const selectedCount = preferences.gameIds.length;
  const now = new Date();
  const previewBrowse = (catalogMode === 'preview' || catalogMode === 'api') && selectedCount === 0 && content.length > 0;
  const source = selectedCount > 0 ? mine : previewBrowse ? content : [];
  const groups = useMemo(() => groupUnread(source, readIds), [source, readIds]);
  const events = useMemo(() => source.filter((item) => isActiveTimeBound(item, now)).sort((a, b) => +new Date(a.endsAt ?? 0) - +new Date(b.endsAt ?? 0)), [source, now.getTime()]);
  const todayGroups = groups.filter((group) => !group.missed);
  const missedGroups = groups.filter((group) => group.missed);
  const popularGames = useMemo(() => [...games].sort((a, b) => b.interestCount - a.interestCount).slice(0, 3), [games]);

  return (
    <View style={styles.root}>
      <SafeAreaView style={styles.safe} edges={['top']}>
        <View style={{ paddingHorizontal: layout.margin }}><AppHeader title="홈" /></View>
        <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => void refresh()} tintColor={theme.color.neonYellow} colors={[theme.color.neonYellow]} progressBackgroundColor={theme.color.surfaceContainerHigh} />}>
          {offline ? <View style={{ paddingHorizontal: layout.margin }}><OfflineBanner lastUpdatedAt={lastUpdatedAt} onRetry={() => void refresh()} /></View> : null}
          <View style={[styles.hero, { marginHorizontal: layout.margin }]}>
            <Image source={imageAssets.heroRoom} style={styles.heroImage} resizeMode="cover" />
            <LinearGradient colors={['rgba(19,19,20,0.04)', 'rgba(19,19,20,0.08)', 'rgba(19,19,20,0.7)']} locations={[0, 0.6, 1]} style={StyleSheet.absoluteFill} />
            <View style={styles.heroCopy}><AppText style={styles.heroEyebrow}>YOUR GAME, YOUR NEWS</AppText><AppText style={styles.heroMessage}>좋아하는 게임 소식만 빠르게</AppText></View>
          </View>
          <View style={{ paddingHorizontal: layout.margin }}>
            <View style={styles.sectionHead}>
              <AppText style={styles.sectionTitle}>마이픽</AppText>
            </View>
            <View style={styles.segmentWrap}>
              <Pressable onPress={() => setHomeTab('news')} style={[styles.segmentItem, homeTab === 'news' && styles.segmentItemActive]} accessibilityRole="tab" accessibilityState={{ selected: homeTab === 'news' }}><AppText style={[styles.segmentText, homeTab === 'news' && styles.segmentTextActive]}>새 소식</AppText></Pressable>
              <Pressable onPress={() => setHomeTab('events')} style={[styles.segmentItem, homeTab === 'events' && styles.segmentItemActive]} accessibilityRole="tab" accessibilityState={{ selected: homeTab === 'events' }}><AppText style={[styles.segmentText, homeTab === 'events' && styles.segmentTextActive]}>이벤트 기간</AppText></Pressable>
            </View>
            {loading ? <LoadingState /> : null}
            {!loading && homeTab === 'news' ? <>
              {selectedCount === 0 ? <Pressable onPress={() => router.push('/(tabs)/games')} style={styles.pickPrompt} accessibilityRole="button"><View style={styles.pickPromptIcon}><Ionicons name="game-controller" size={22} color={theme.color.onPrimary} /></View><View style={styles.pickPromptBody}><AppText style={styles.pickPromptTitle}>관심 게임을 등록해보세요</AppText><AppText style={styles.pickPromptDesc}>고른 게임의 새 소식과 진행 중인 기간을 모아드려요</AppText></View><Ionicons name="chevron-forward" size={20} color={theme.color.textMuted} /></Pressable> : null}
              {todayGroups.map((group) => <NewsGroupCard key={group.gameId} group={group} />)}
              {missedGroups.length > 0 ? <View style={styles.missedSection}><View style={styles.subHead}><AppText style={styles.subTitle}>놓친 소식</AppText><AppText style={styles.subCount}>{missedGroups.reduce((sum, group) => sum + group.items.length, 0)}개</AppText></View>{missedGroups.map((group) => <NewsGroupCard key={`missed-${group.gameId}`} group={group} />)}</View> : null}
              {groups.length === 0 ? <EmptyState icon="checkmark-circle-outline" title={selectedCount > 0 ? '새로운 소식을 모두 확인했어요' : '오늘은 새로운 소식이 없어요'} description={selectedCount > 0 ? '새 업데이트가 올라오면 알려드릴게요.' : '내 게임을 등록하면 맞춤 소식을 받을 수 있어요.'} actionLabel={selectedCount === 0 ? '내 게임 고르기' : undefined} onAction={selectedCount === 0 ? () => router.push('/(tabs)/games') : undefined} /> : null}
            </> : null}
            {!loading && homeTab === 'events' ? events.length > 0 ? events.map((item) => <EventPeriodCard key={item.id} item={item} />) : <EmptyState icon="calendar-outline" title="진행 중인 이벤트가 없어요" description="공식 공지에 시작일과 종료일이 함께 확인된 콘텐츠만 표시합니다." /> : null}
            {!loading && selectedCount === 0 && popularGames.length > 0 && homeTab === 'news' ? <View style={styles.popularBlock}><AppText style={styles.popularTitle}>지금 인기 게임</AppText>{popularGames.map((game) => <View key={game.id} style={styles.popularRow}><View style={[styles.popularSwatch, { backgroundColor: game.color }]}><AppText style={styles.popularInitial}>{game.initial}</AppText></View><View style={styles.popularBody}><AppText style={styles.popularName} numberOfLines={1}>{game.name}</AppText><AppText style={styles.popularGenre} numberOfLines={1}>{game.genre} · 관심 {game.interestCount.toLocaleString('ko-KR')}</AppText></View><Pressable onPress={() => setGameIds([...preferences.gameIds, game.id])} style={styles.popularAdd} accessibilityRole="button" accessibilityLabel={`${game.name} 마이픽 추가`}><Ionicons name="add" size={18} color={theme.color.onPrimary} /></Pressable></View>)}</View> : null}
            {previewBrowse ? <AppText style={styles.previewLabel}>지금은 전체 소식을 미리 보여드려요</AppText> : null}
          </View>
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: theme.color.background }, safe: { flex: 1 }, scroll: { paddingBottom: 36 },
  hero: { height: 190, borderRadius: theme.radius.xl, overflow: 'hidden', marginBottom: 22, backgroundColor: theme.color.surfaceContainerLow }, heroImage: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, width: '100%', height: '100%' }, heroCopy: { position: 'absolute', left: 18, right: 18, bottom: 16, gap: 3 }, heroEyebrow: { fontFamily: theme.font.label, fontSize: 9, letterSpacing: 1.4, color: theme.color.neonYellow }, heroMessage: { fontFamily: theme.font.headlineSemi, fontSize: 18, color: theme.color.onSurface },
  sectionHead: { flexDirection: 'row', alignItems: 'center', paddingBottom: 0, marginBottom: 6 }, sectionTitle: { fontFamily: theme.font.headlineSemi, fontSize: 22, color: theme.color.onSurface },
  segmentWrap: { flexDirection: 'row', padding: 4, gap: 4, backgroundColor: theme.color.surfaceContainerHigh, borderWidth: 1, borderColor: theme.color.outlineVariant, borderRadius: theme.radius.sm, marginBottom: 13 }, segmentItem: { flex: 1, alignItems: 'center', paddingVertical: 10, borderRadius: 4 }, segmentItemActive: { backgroundColor: theme.color.primaryContainer }, segmentText: { fontFamily: theme.font.bodySemi, fontSize: 13, color: theme.color.textMuted }, segmentTextActive: { color: theme.color.onPrimary },
  group: { marginBottom: 12 },
  moreItems: { marginTop: -2, marginBottom: 3, backgroundColor: theme.color.surfaceContainer, borderBottomLeftRadius: theme.radius.xl, borderBottomRightRadius: theme.radius.xl, paddingHorizontal: 12, paddingBottom: 4 }, moreItem: { flexDirection: 'row', alignItems: 'center', minHeight: 38, gap: 8, borderTopWidth: 1, borderTopColor: theme.color.outlineVariant }, moreItemPressed: { opacity: 0.7 }, moreDot: { width: 4, height: 4, borderRadius: 2, backgroundColor: theme.color.textMuted }, moreTitle: { flex: 1, minWidth: 0, fontFamily: theme.font.body, fontSize: 13, color: theme.color.onSurface }, moreTime: { fontFamily: theme.font.body, fontSize: 11, color: theme.color.textMuted }, missedSection: { marginTop: 4 }, subHead: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10 }, subTitle: { fontFamily: theme.font.bodySemi, fontSize: 16, color: theme.color.onSurface }, subCount: { fontFamily: theme.font.body, fontSize: 12, color: theme.color.textMuted },
  eventCard: { marginBottom: 10, padding: 15, borderRadius: theme.radius.xl, backgroundColor: theme.color.surfaceContainer, borderWidth: 1, borderColor: theme.color.outlineVariant }, eventTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }, eventBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 5, backgroundColor: 'rgba(190,124,255,0.16)' }, eventBadgeText: { fontFamily: theme.font.bodySemi, fontSize: 11, color: theme.color.neonPurple }, eventCountdown: { fontFamily: theme.font.bodySemi, fontSize: 12, color: theme.color.neonYellow }, eventTitle: { fontFamily: theme.font.bodySemi, fontSize: 16, lineHeight: 22, color: theme.color.onSurface }, eventGame: { fontFamily: theme.font.body, fontSize: 12, color: theme.color.textMuted, marginTop: 5 },
  pickPrompt: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 16, padding: 14, backgroundColor: theme.color.surfaceContainer, borderWidth: 1, borderColor: theme.color.outlineVariant, borderRadius: theme.radius.xl }, pickPromptIcon: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.color.neonYellow }, pickPromptBody: { flex: 1, minWidth: 0, gap: 3 }, pickPromptTitle: { fontFamily: theme.font.bodySemi, fontSize: 15, color: theme.color.onSurface }, pickPromptDesc: { fontFamily: theme.font.body, fontSize: 12, lineHeight: 17, color: theme.color.textMuted }, popularBlock: { marginTop: 16, padding: 14, backgroundColor: theme.color.surfaceContainer, borderRadius: theme.radius.xl, gap: 10 }, popularTitle: { fontFamily: theme.font.bodySemi, fontSize: 14, color: theme.color.onSurface }, popularRow: { flexDirection: 'row', alignItems: 'center', gap: 10 }, popularSwatch: { width: 40, height: 40, borderRadius: theme.radius.md, alignItems: 'center', justifyContent: 'center' }, popularInitial: { fontFamily: theme.font.headlineSemi, fontSize: 16, color: theme.color.onPrimary }, popularBody: { flex: 1, minWidth: 0, gap: 2 }, popularName: { fontFamily: theme.font.bodySemi, fontSize: 14, color: theme.color.onSurface }, popularGenre: { fontFamily: theme.font.body, fontSize: 12, color: theme.color.textMuted }, popularAdd: { width: 34, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.color.neonYellow }, previewLabel: { marginTop: 12, fontFamily: theme.font.body, fontSize: 12, color: theme.color.textMuted },
});
