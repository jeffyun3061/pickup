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
