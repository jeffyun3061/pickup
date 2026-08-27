/**
 * Android 실기기 폭 기준 레이아웃 스케일 (순수 함수).
 * 360(소형) / 393(일반) / 412+(대형)
 */
export type LayoutScale = {
  width: number;
  isCompact: boolean;
  margin: number;
  feedThumb: number;
  /** 홈 마이 픽업 소식용 — 더 큰 썸네일 */
  homeFeedThumb: number;
  titleSize: number;
  displaySize: number;
  tabLabel: 'short' | 'full';
  gridGap: number;
};

export type PickGridMetrics = {
  /** 2×2 마이픽 카드 한 장의 높이 */
  cardHeight: number;
  /** 카드 두 줄과 세로 간격을 포함한 페이지 높이 */
  gridHeight: number;
  /** 페이지 + 아래쪽 페이지 인디케이터를 포함한 래퍼 높이 */
  pagerHeight: number;
};

export function resolveLayout(width: number): LayoutScale {
  const isCompact = width < 380;
  return {
    width,
    isCompact,
    margin: isCompact ? 16 : width >= 412 ? 24 : 20,
    feedThumb: isCompact ? 84 : 96,
    homeFeedThumb: isCompact ? 92 : 100,
    titleSize: isCompact ? 20 : 22,
    displaySize: isCompact ? 24 : 28,
    tabLabel: isCompact ? 'short' : 'full',
    gridGap: isCompact ? 8 : 12,
  };
}

/**
 * 마이픽 2×2 카드의 세로 크기를 화면 폭에 맞춰 계산한다.
 *
 * 고정 530dp 페이지는 360dp 폭/짧은 화면에서 하단 탭과 겹칠 수 있다.
 * 카드 비율은 시안의 세로형 카드 비율을 유지하되, 너무 작거나 커지지
 * 않도록 경계를 둔다. 실제 화면은 Screen의 세로 스크롤로 보완한다.
 */
export function resolvePickGrid(trackWidth: number): PickGridMetrics {
  const width = Number.isFinite(trackWidth) ? Math.max(0, trackWidth) : 0;
  const cardHeight = width > 0 ? Math.min(260, Math.max(188, Math.round(width * 0.72))) : 220;
  const rowGap = width > 0 && width < 340 ? 10 : 12;
  const gridHeight = cardHeight * 2 + rowGap;
  return {
    cardHeight,
    gridHeight,
    pagerHeight: gridHeight + 40,
  };
}
