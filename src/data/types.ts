import type {
  ContentItem,
  Game,
  RankingRow,
  ServiceAnnouncement,
} from '@/src/domain/models';

/**
 * 데이터 접근 계약.
 * UI/훅은 구현체가 Empty인지 API인지 모른다 → 교체·테스트가 쉽다.
 */
export type CatalogRepository = {
  listGames(): Promise<Game[]>;
  listContent(scope: 'all' | 'mine', gameIds: string[]): Promise<ContentItem[]>;
  listRankings(): Promise<RankingRow[]>;
  listAnnouncements(): Promise<ServiceAnnouncement[]>;
};
