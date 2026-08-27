import { apiFetch } from '@/src/data/apiClient';
import { isAppImageName } from '@/src/assets/images';
import type { CatalogRepository } from '@/src/data/types';
import type {
  ContentItem,
  ContentKind,
  ContentAnalysis,
  Game,
  RankingRow,
  ServiceAnnouncement,
} from '@/src/domain/models';

type ApiGame = {
  id: string;
  name: string;
  initial: string;
  genre: string;
  color: string;
  interest_count: number;
  image_url?: string | null;
  image_rights_status?: string | null;
  fallback_image_key?: string | null;
};

type ApiContent = {
  id: string;
  game_id: string;
  game_name: string;
  kind: ContentKind;
  title: string;
  summary_points: string[];
  analysis?: {
    importance: 1 | 2 | 3;
    impact_level: 'low' | 'medium' | 'high';
    impact_summary: string;
    confidence: 'low' | 'medium' | 'high';
    community_sentiment?: 'positive' | 'mixed' | 'negative' | 'unknown';
    community_summary?: string | null;
    community_sample_count?: number | null;
    generated_at?: string | null;
  } | null;
  official_url: string;
  image_url?: string | null;
  image_rights_status?: string | null;
  fallback_image_key?: string | null;
  fallback_color?: string | null;
  place?: string | null;
  reservation_url?: string | null;
  starts_at?: string | null;
  ends_at?: string | null;
  published_at?: string | null;
};

type ApiRanking = {
  game_id: string;
  game_name: string;
  interest_count: number;
  rank: number;
  initial: string;
  color: string;
  image_url?: string | null;
  image_rights_status?: string | null;
  fallback_image_key?: string | null;
};

type ApiAnnouncement = {
  id: string;
  title: string;
  body: string;
  published_at: string;
};

function isApprovedImage(status?: string | null) {
  return status === 'official' || status === 'licensed' || status === 'original';
}

function fallbackImageKey(value?: string | null) {
  return isAppImageName(value) ? value : 'coverTactical';
}

function mapGame(g: ApiGame): Game {
  const imageApproved = isApprovedImage(g.image_rights_status);
  return {
    id: g.id,
    name: g.name,
    initial: g.initial,
    genre: g.genre,
    color: g.color,
    interestCount: g.interest_count,
    imageUrl: imageApproved ? g.image_url ?? undefined : undefined,
    imageKey: fallbackImageKey(g.fallback_image_key),
    themedFallback: true,
  };
}

function mapContent(c: ApiContent): ContentItem {
  const imageApproved = isApprovedImage(c.image_rights_status);
  return {
    id: c.id,
    gameId: c.game_id,
    gameName: c.game_name,
    kind: c.kind,
    title: c.title,
    summaryPoints: c.summary_points ?? [],
    analysis: c.analysis
      ? ({
          importance: c.analysis.importance,
          impactLevel: c.analysis.impact_level,
          impactSummary: c.analysis.impact_summary,
          confidence: c.analysis.confidence,
          communitySentiment: c.analysis.community_sentiment ?? 'unknown',
          communitySummary: c.analysis.community_summary ?? undefined,
          communitySampleCount: c.analysis.community_sample_count ?? undefined,
          generatedAt: c.analysis.generated_at ?? undefined,
        } satisfies ContentAnalysis)
      : undefined,
    officialUrl: c.official_url,
    imageUrl: imageApproved ? c.image_url ?? undefined : undefined,
    imageKey: fallbackImageKey(c.fallback_image_key),
    fallbackColor: c.fallback_color ?? '#2A2A2B',
    themedFallback: true,
    place: c.place ?? undefined,
    reservationUrl: c.reservation_url ?? undefined,
    startsAt: c.starts_at ?? undefined,
    endsAt: c.ends_at ?? undefined,
    publishedAt: c.published_at ?? new Date().toISOString(),
  };
}

/**
 * 실서비스 CatalogRepository.
 * 공개 API만 호출한다 (관리자 시크릿 없음).
 */
export class ApiCatalogRepository implements CatalogRepository {
  async listGames(): Promise<Game[]> {
    const rows = await apiFetch<ApiGame[]>('/api/v1/games');
    return rows.map(mapGame);
  }

  async listContent(scope: 'all' | 'mine', gameIds: string[]): Promise<ContentItem[]> {
    const qs = new URLSearchParams({ scope });
    if (scope === 'mine') qs.set('game_ids', gameIds.join(','));
    const rows = await apiFetch<ApiContent[]>(`/api/v1/contents?${qs.toString()}`);
    return rows.map(mapContent);
  }

  async listRankings(): Promise<RankingRow[]> {
    const rows = await apiFetch<ApiRanking[]>('/api/v1/rankings');
    return rows.map((r) => ({
      gameId: r.game_id,
      gameName: r.game_name,
      interestCount: r.interest_count,
      rank: r.rank,
      initial: r.initial,
      color: r.color,
      imageUrl:
        isApprovedImage(r.image_rights_status)
          ? r.image_url ?? undefined
          : undefined,
      imageKey: fallbackImageKey(r.fallback_image_key),
      themedFallback: true,
    }));
  }

  async listAnnouncements(): Promise<ServiceAnnouncement[]> {
    const rows = await apiFetch<ApiAnnouncement[]>('/api/v1/announcements');
    return rows.map((a) => ({
      id: a.id,
      title: a.title,
      body: a.body,
      publishedAt: a.published_at,
    }));
  }
}
