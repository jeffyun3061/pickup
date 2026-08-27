import { describe, expect, it } from 'vitest';

import { resolveLayout, resolvePickGrid } from '@/src/theme/layout';

describe('resolveLayout', () => {
  it('uses compact scale under 380dp (e.g. 360)', () => {
    const layout = resolveLayout(360);
    expect(layout.isCompact).toBe(true);
    expect(layout.margin).toBe(16);
    expect(layout.feedThumb).toBe(84);
    expect(layout.homeFeedThumb).toBe(92);
    expect(layout.tabLabel).toBe('short');
    expect(layout.displaySize).toBe(24);
  });

  it('uses default scale around 393dp', () => {
    const layout = resolveLayout(393);
    expect(layout.isCompact).toBe(false);
    expect(layout.margin).toBe(20);
    expect(layout.homeFeedThumb).toBe(100);
    expect(layout.tabLabel).toBe('full');
  });

  it('widens margin on 412dp+', () => {
    const layout = resolveLayout(412);
    expect(layout.margin).toBe(24);
    expect(layout.feedThumb).toBe(96);
    expect(layout.homeFeedThumb).toBe(100);
  });

  it('keeps the 2x2 pick grid within readable bounds across phone widths', () => {
    const compact = resolvePickGrid(328);
    const regular = resolvePickGrid(353);
    const large = resolvePickGrid(364);

    expect(compact.cardHeight).toBeGreaterThanOrEqual(136);
    expect(compact.gridHeight).toBe(compact.cardHeight * 2 + 10);
    expect(regular.cardHeight).toBeGreaterThan(compact.cardHeight);
    expect(large.cardHeight).toBeLessThanOrEqual(164);
    expect(large.pagerHeight).toBe(large.gridHeight + 50);
  });

  it('uses a safe fallback before the pager has measured its width', () => {
    expect(resolvePickGrid(0)).toEqual({
      cardHeight: 150,
      gridHeight: 311,
      pagerHeight: 361,
    });
  });
});
