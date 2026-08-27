import { describe, expect, it } from 'vitest';

import {
  PREVIEW_CONTENT,
  PREVIEW_GAMES,
  PREVIEW_ANNOUNCEMENTS,
  PREVIEW_RANKINGS,
} from '@/src/data/previewCatalog';

describe('미리보기 게임 카탈로그', () => {
  it('권리 검토 전 보류 게임을 제외한 서비스 후보 12개를 중복 없이 노출한다', () => {
    expect(PREVIEW_GAMES).toHaveLength(12);
    expect(new Set(PREVIEW_GAMES.map((game) => game.id)).size).toBe(12);
    expect(PREVIEW_GAMES.map((game) => game.name)).toEqual([
      '붕괴: 스타레일',
      '원신',
      '블루 아카이브',
      '니케',
      '세븐나이츠',
      '포켓몬 GO',
      '소녀전선 2',
      '이환',
      '에픽세븐',
      '트릭컬 리바이브',
      '명일방주',
      '우마무스메',
    ]);
  });

  it('랭킹은 관심 등록 수 내림차순으로 카탈로그 전체를 연결한다', () => {
    expect(PREVIEW_RANKINGS).toHaveLength(PREVIEW_GAMES.length);
    expect(PREVIEW_RANKINGS.map((row) => row.rank)).toEqual(
      PREVIEW_GAMES.map((_, index) => index + 1),
    );
    expect(PREVIEW_RANKINGS.map((row) => row.interestCount)).toEqual(
      [...PREVIEW_GAMES]
        .sort((a, b) => b.interestCount - a.interestCount)
        .map((game) => game.interestCount),
    );
    expect(PREVIEW_RANKINGS[0].gameName).toBe('블루 아카이브');
  });

  it('샘플 소식도 새 카탈로그 게임 ID만 참조한다', () => {
    const gameIds = new Set(PREVIEW_GAMES.map((game) => game.id));
    expect(PREVIEW_CONTENT.every((item) => gameIds.has(item.gameId))).toBe(true);
  });

  it('운영 공지는 API에서만 받아오고 미리보기 데이터에는 포함하지 않는다', () => {
    expect(PREVIEW_ANNOUNCEMENTS).toEqual([]);
  });
});
