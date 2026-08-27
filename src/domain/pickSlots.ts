import type { Game } from '@/src/domain/models';

/** 마이픽 한 페이지의 고정 슬롯 수. 5~8개는 두 번째 페이지로 넘긴다. */
export const PICK_SLOTS_PER_PAGE = 4;

export type PickSlot =
  | { kind: 'game'; game: Game }
  | { kind: 'empty'; key: string };

/**
 * 선택 게임을 2×2 페이지로 배치한다.
 * 선택 전에도 첫 페이지 네 칸을 유지해 등록 폼이 사라지지 않게 한다.
 */
export function chunkPickSlots(
  games: readonly Game[],
  size = PICK_SLOTS_PER_PAGE,
): PickSlot[][] {
  if (!Number.isInteger(size) || size < 1) {
    throw new RangeError('마이픽 슬롯 수는 1 이상의 정수여야 합니다.');
  }

  const pageCount = Math.max(1, Math.ceil(games.length / size));
  const pages: PickSlot[][] = [];

  for (let pageIndex = 0; pageIndex < pageCount; pageIndex += 1) {
    const page: PickSlot[] = games
      .slice(pageIndex * size, pageIndex * size + size)
      .map((game) => ({ kind: 'game' as const, game }));

    while (page.length < size) {
      page.push({ kind: 'empty', key: `empty-${pageIndex}-${page.length}` });
    }
    pages.push(page);
  }

  return pages;
}
