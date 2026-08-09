import type { CatalogRepository } from '@/src/data/types';
import {
  PREVIEW_ANNOUNCEMENTS,
  PREVIEW_CONTENT,
  PREVIEW_GAMES,
  PREVIEW_RANKINGS,
} from '@/src/data/previewCatalog';
import type {
  ContentItem,
  Game,
  RankingRow,
  ServiceAnnouncement,
} from '@/src/domain/models';

/**
 * UI/시안 검증용 카탈로그.
 * 실서비스 Empty → API 교체 전, Neon-Tactical 퀄리티 확인에만 쓴다 (ADR-002 보완).
 */
export class PreviewCatalogRepository implements CatalogRepository {
  async listGames(): Promise<Game[]> {
    return PREVIEW_GAMES;
  }

  async listContent(
    scope: 'all' | 'mine',
    gameIds: string[],
  ): Promise<ContentItem[]> {
    const sorted = [...PREVIEW_CONTENT].sort(
      (a, b) => +new Date(b.publishedAt) - +new Date(a.publishedAt),
    );
    if (scope === 'all') return sorted;
    if (gameIds.length === 0) return [];
    return sorted.filter((item) => gameIds.includes(item.gameId));
  }

  async listRankings(): Promise<RankingRow[]> {
    return PREVIEW_RANKINGS;
  }

  async listAnnouncements(): Promise<ServiceAnnouncement[]> {
    return PREVIEW_ANNOUNCEMENTS;
  }
}
