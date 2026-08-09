import { describe, expect, it } from 'vitest';

import { isOfflineKind, kindLabel } from '@/src/domain/models';
import { EmptyCatalogRepository } from '@/src/data/EmptyCatalogRepository';
import { PreviewCatalogRepository } from '@/src/data/PreviewCatalogRepository';

describe('domain labels', () => {
  it('maps content kinds for UI badges', () => {
    expect(kindLabel('update')).toBe('업데이트');
    expect(kindLabel('popup')).toBe('팝업');
    expect(isOfflineKind('goods')).toBe(true);
    expect(isOfflineKind('event')).toBe(false);
  });
});

describe('EmptyCatalogRepository', () => {
  it('returns empty arrays for empty mode', async () => {
    const repo = new EmptyCatalogRepository();
    await expect(repo.listGames()).resolves.toEqual([]);
    await expect(repo.listContent('all', [])).resolves.toEqual([]);
    await expect(repo.listRankings()).resolves.toEqual([]);
    await expect(repo.listAnnouncements()).resolves.toEqual([]);
  });
});

describe('PreviewCatalogRepository', () => {
  it('serves fiction catalog with image keys for UI preview', async () => {
    const repo = new PreviewCatalogRepository();
    const games = await repo.listGames();
    const all = await repo.listContent('all', []);
    const mine = await repo.listContent('mine', [games[0].id]);
    expect(games.length).toBeGreaterThan(0);
    expect(all.every((c) => Boolean(c.imageKey))).toBe(true);
    expect(mine.every((c) => c.gameId === games[0].id)).toBe(true);
  });
});
