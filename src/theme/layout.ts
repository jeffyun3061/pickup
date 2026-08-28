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
 * 카드 2줄과 페이지 점이 하단 탭바에 가리지 않도록 카드 높이를
 * 폭과 페이지 구조에 맞춰 제한한다. 등록 전에도 4개 슬롯과 점을
 * 한 화면에서 확인할 수 있도록 넓게 쓰되, 작은 기기에서는 스크롤로
 * 안전하게 끝까지 접근할 수 있는 범위를 유지한다.
 */
export function resolvePickGrid(trackWidth: number): PickGridMetrics {
  const width = Number.isFinite(trackWidth) ? Math.max(0, trackWidth) : 0;
  const cardHeight = width > 0 ? Math.min(250, Math.max(218, Math.round(width * 0.68))) : 220;
  const rowGap = width > 0 && width < 340 ? 10 : 11;
  const gridHeight = cardHeight * 2 + rowGap;
  return {
    cardHeight,
    gridHeight,
    // 점과 최소 여백까지 자식 레이아웃에 포함한다.
    pagerHeight: gridHeight + 50,
  };
}
