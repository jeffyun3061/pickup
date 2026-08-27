import { MAX_SELECTED_GAMES, type Game } from '@/src/domain/models';

/** 마이픽 한 페이지의 고정 슬롯 수. 최대 8개를 4개씩 두 페이지로 보여준다. */
export const PICK_SLOTS_PER_PAGE = 4;
export const PICK_PAGE_COUNT = Math.ceil(MAX_SELECTED_GAMES / PICK_SLOTS_PER_PAGE);

export type PickSlot =
  | { kind: 'game'; game: Game }
  | { kind: 'empty'; key: string };

/**
 * 선택 게임을 2×2 페이지로 배치한다.
 * 선택 전에도 등록 슬롯 두 페이지를 유지해 최대 8칸을 좌우로 확인할 수 있게 한다.
 */
export function chunkPickSlots(
  games: readonly Game[],
  size = PICK_SLOTS_PER_PAGE,
  minPages = 1,
): PickSlot[][] {
  if (!Number.isInteger(size) || size < 1) {
    throw new RangeError('마이픽 슬롯 수는 1 이상의 정수여야 합니다.');
  }
  if (!Number.isInteger(minPages) || minPages < 1) {
    throw new RangeError('마이픽 페이지 수는 1 이상의 정수여야 합니다.');
  }

  const pageCount = Math.max(minPages, Math.ceil(games.length / size), 1);
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
