import type { CatalogRepository } from '@/src/data/types';
import type {
  ContentItem,
  Game,
  RankingRow,
  ServiceAnnouncement,
} from '@/src/domain/models';

/**
 * 초기 구현체: 빈 카탈로그.
 * 샘플 게임/뉴스를 심지 않는다 (ADR-002).
 * 실서비스에서는 ApiCatalogRepository로 교체한다.
 */
export class EmptyCatalogRepository implements CatalogRepository {
  async listGames(): Promise<Game[]> {
    return [];
  }

  async listContent(
    _scope: 'all' | 'mine',
    _gameIds: string[],
  ): Promise<ContentItem[]> {
    return [];
  }

  async listRankings(): Promise<RankingRow[]> {
    return [];
  }

  async listAnnouncements(): Promise<ServiceAnnouncement[]> {
    return [];
  }
}
