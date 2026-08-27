import { useCallback, useEffect, useRef, useState } from 'react';

import { catalogRepository } from '@/src/data/catalog';
import { loadCatalogSnapshot, saveCatalogSnapshot } from '@/src/data/catalogCache';
import type {
  ContentItem,
  Game,
  RankingRow,
  ServiceAnnouncement,
} from '@/src/domain/models';
import { useApp } from '@/src/state/AppProvider';

type CatalogState = {
  loading: boolean;
  refreshing: boolean;
  /** true면 네트워크 실패로 캐시(또는 빈 데이터)를 보여주는 중 */
  offline: boolean;
  /** 마지막으로 데이터를 성공적으로 받은 시각 (캐시 폴백 시 캐시 저장 시각) */
  lastUpdatedAt: number | null;
  games: Game[];
  content: ContentItem[];
  mine: ContentItem[];
  rankings: RankingRow[];
  announcements: ServiceAnnouncement[];
  refresh: () => Promise<void>;
};

export function useCatalog(): CatalogState {
  const { preferences } = useApp();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [offline, setOffline] = useState(false);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<number | null>(null);
  const [games, setGames] = useState<Game[]>([]);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [mine, setMine] = useState<ContentItem[]>([]);
  const [rankings, setRankings] = useState<RankingRow[]>([]);
  const [announcements, setAnnouncements] = useState<ServiceAnnouncement[]>([]);
  const mounted = useRef(true);

  const gameIdsKey = preferences.gameIds.join(',');

  const load = useCallback(
    async (mode: 'initial' | 'refresh') => {
      if (mode === 'initial') setLoading(true);
      else setRefreshing(true);
      const gameIds = gameIdsKey ? gameIdsKey.split(',') : [];
      try {
        const [g, all, mineList, r, a] = await Promise.all([
          catalogRepository.listGames(),
          catalogRepository.listContent('all', gameIds),
          catalogRepository.listContent('mine', gameIds),
          catalogRepository.listRankings(),
          catalogRepository.listAnnouncements(),
        ]);
        if (!mounted.current) return;
        setGames(g);
        setContent(all);
        setMine(mineList);
        setRankings(r);
        setAnnouncements(a);
        setOffline(false);
        setLastUpdatedAt(Date.now());
        void saveCatalogSnapshot({ games: g, content: all, rankings: r, announcements: a });
      } catch {
        // 네트워크/서버 장애 — 마지막 성공 스냅샷으로 폴백
        const snapshot = await loadCatalogSnapshot();
        if (!mounted.current) return;
        if (snapshot) {
          setGames(snapshot.games);
          setContent(snapshot.content);
          setMine(snapshot.content.filter((item) => gameIds.includes(item.gameId)));
          setRankings(snapshot.rankings);
          setAnnouncements(snapshot.announcements);
          setLastUpdatedAt(snapshot.savedAt || null);
        }
        setOffline(true);
      } finally {
        if (mounted.current) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    [gameIdsKey],
  );

  useEffect(() => {
    mounted.current = true;
    void load('initial');
    return () => {
      mounted.current = false;
    };
  }, [load]);

  const refresh = useCallback(() => load('refresh'), [load]);

  return {
    loading,
    refreshing,
    offline,
    lastUpdatedAt,
    games,
    content,
    mine,
    rankings,
    announcements,
    refresh,
  };
}
