import { useMemo } from 'react';
import { useWindowDimensions } from 'react-native';

import { resolveLayout, type LayoutScale } from '@/src/theme/layout';

export function useLayout(): LayoutScale {
  const { width } = useWindowDimensions();
  return useMemo(() => resolveLayout(width), [width]);
}
