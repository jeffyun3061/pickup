import { describe, expect, it } from 'vitest';

import {
  eventCountdownLabel,
  isActiveTimeBound,
  isOfflineKind,
  kindLabel,
  MAX_SELECTED_GAMES,
  normalizeGameIds,
} from '@/src/domain/models';
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

describe('home rules', () => {
  const now = new Date('2026-08-24T12:00:00+09:00');

  it('limits selected games to eight unique ids', () => {
    expect(normalizeGameIds(['a', 'a', ...Array.from({ length: 10 }, (_, i) => `g${i}`)])).toHaveLength(MAX_SELECTED_GAMES);
  });

  it('shows only started, explicitly bounded content in event period', () => {
    expect(isActiveTimeBound({ kind: 'event', startsAt: '2026-08-23T00:00:00+09:00', endsAt: '2026-08-25T00:00:00+09:00' }, now)).toBe(true);
    expect(isActiveTimeBound({ kind: 'event', startsAt: '2026-08-25T00:00:00+09:00', endsAt: '2026-08-26T00:00:00+09:00' }, now)).toBe(false);
    expect(isActiveTimeBound({ kind: 'event', startsAt: '2026-08-23T00:00:00+09:00' }, now)).toBe(false);
  });

  it('uses the product countdown copy', () => {
    expect(eventCountdownLabel('2026-08-24T23:59:00+09:00', now)).toBe('오늘 종료');
    expect(eventCountdownLabel('2026-08-25T23:59:00+09:00', now)).toBe('내일 종료');
    expect(eventCountdownLabel('2026-08-27T23:59:00+09:00', now)).toBe('종료 D-3');
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
