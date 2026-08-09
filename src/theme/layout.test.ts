import { describe, expect, it } from 'vitest';

import { resolveLayout } from '@/src/theme/layout';

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
});
