import AsyncStorage from '@react-native-async-storage/async-storage/lib/commonjs/index.js';

import type {
  ContentItem,
  Game,
  RankingRow,
  ServiceAnnouncement,
} from '@/src/domain/models';

/**
 * 카탈로그 오프라인 캐시 — 마지막 성공 응답을 저장해 서버 장애/오프라인에도
 * 빈 화면 대신 최근 데이터를 보여준다.
 */
export type CatalogSnapshot = {
  savedAt: number;
  games: Game[];
  content: ContentItem[];
  rankings: RankingRow[];
  announcements: ServiceAnnouncement[];
};

const CACHE_KEY = 'gamepickup.catalog.cache.v1';

export async function clearCatalogSnapshot(): Promise<void> {
  try {
    await AsyncStorage.removeItem(CACHE_KEY);
  } catch {
    /* 캐시 삭제 실패는 다음 기동 때 다시 시도하지 않음 */
  }
}

export async function saveCatalogSnapshot(
  snapshot: Omit<CatalogSnapshot, 'savedAt'>,
): Promise<void> {
  try {
    await AsyncStorage.setItem(
      CACHE_KEY,
      JSON.stringify({ ...snapshot, savedAt: Date.now() }),
    );
  } catch {
    /* 캐시 실패는 치명적이지 않음 */
  }
}

export async function loadCatalogSnapshot(): Promise<CatalogSnapshot | null> {
  try {
    const raw = await AsyncStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CatalogSnapshot;
    if (!Array.isArray(parsed.games) || !Array.isArray(parsed.content)) return null;
    return {
      savedAt: typeof parsed.savedAt === 'number' ? parsed.savedAt : 0,
      games: parsed.games,
      content: parsed.content,
      rankings: Array.isArray(parsed.rankings) ? parsed.rankings : [],
      announcements: Array.isArray(parsed.announcements) ? parsed.announcements : [],
    };
  } catch {
    return null;
  }
}
