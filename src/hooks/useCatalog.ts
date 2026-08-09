import { useCallback, useEffect, useState } from 'react';

import { catalogRepository } from '@/src/data/catalog';
import type {
  ContentItem,
  Game,
  RankingRow,
  ServiceAnnouncement,
} from '@/src/domain/models';
import { useApp } from '@/src/state/AppProvider';

type CatalogState = {
  loading: boolean;
  games: Game[];
  content: ContentItem[];
  mine: ContentItem[];
  rankings: RankingRow[];
  announcements: ServiceAnnouncement[];
  refresh: () => void;
};

export function useCatalog(): CatalogState {
  const { preferences } = useApp();
  const [loading, setLoading] = useState(true);
  const [games, setGames] = useState<Game[]>([]);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [mine, setMine] = useState<ContentItem[]>([]);
  const [rankings, setRankings] = useState<RankingRow[]>([]);
  const [announcements, setAnnouncements] = useState<ServiceAnnouncement[]>([]);
  const [tick, setTick] = useState(0);

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      try {
        const [g, all, mineList, r, a] = await Promise.all([
          catalogRepository.listGames(),
          catalogRepository.listContent('all', preferences.gameIds),
          catalogRepository.listContent('mine', preferences.gameIds),
          catalogRepository.listRankings(),
          catalogRepository.listAnnouncements(),
        ]);
        if (!mounted) return;
        setGames(g);
        setContent(all);
        setMine(mineList);
        setRankings(r);
        setAnnouncements(a);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [preferences.gameIds, tick]);

  return { loading, games, content, mine, rankings, announcements, refresh };
}
