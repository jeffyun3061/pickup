import { describe, expect, it } from 'vitest';

import type { Game } from '@/src/domain/models';
import { chunkPickSlots, PICK_SLOTS_PER_PAGE } from '@/src/domain/pickSlots';

const games: Game[] = Array.from({ length: 8 }, (_, index) => ({
  id: `g${index + 1}`,
  name: `게임 ${index + 1}`,
  initial: `${index + 1}`,
  genre: 'RPG',
  color: '#111111',
  interestCount: 0,
}));

describe('chunkPickSlots', () => {
  it('선택 전에도 2×2 등록 폼을 유지한다', () => {
    const pages = chunkPickSlots([]);

    expect(pages).toHaveLength(1);
    expect(pages[0]).toHaveLength(PICK_SLOTS_PER_PAGE);
    expect(pages[0].every((slot) => slot.kind === 'empty')).toBe(true);
  });

  it('1~3개 선택 시 빈 슬롯을 채워 첫 페이지를 네 칸으로 맞춘다', () => {
    const pages = chunkPickSlots(games.slice(0, 3));

    expect(pages).toHaveLength(1);
    expect(pages[0].map((slot) => slot.kind)).toEqual([
      'game',
      'game',
      'game',
      'empty',
    ]);
  });

  it('최대 8개는 네 칸씩 두 페이지이고 추가 빈 페이지를 만들지 않는다', () => {
    const pages = chunkPickSlots(games);

    expect(pages).toHaveLength(2);
    expect(pages.every((page) => page.length === PICK_SLOTS_PER_PAGE)).toBe(true);
    expect(pages.flat().filter((slot) => slot.kind === 'game')).toHaveLength(8);
    expect(chunkPickSlots(games.slice(0, 5))[1].map((slot) => slot.kind)).toEqual([
      'game',
      'empty',
      'empty',
      'empty',
    ]);
  });

  it('잘못된 슬롯 수는 조기에 거부한다', () => {
    expect(() => chunkPickSlots([], 0)).toThrow(RangeError);
    expect(() => chunkPickSlots([], 1.5)).toThrow(RangeError);
  });
});
