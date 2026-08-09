/**
 * Stitch Neon-Tactical 토큰.
 * 출처: design-ref/DESIGN.md — 임의 색/폰트 추가 금지.
 */
export const theme = {
  color: {
    background: '#131314',
    surface: '#131314',
    surfaceContainer: '#201F20',
    surfaceContainerLow: '#1C1B1C',
    surfaceContainerHigh: '#2A2A2B',
    surfaceContainerHighest: '#353436',
    surfaceLowest: '#0E0E0F',
    onSurface: '#E5E2E3',
    onSurfaceVariant: '#C4C9AC',
    outline: '#999077',
    outlineVariant: '#444933',
    neonYellow: '#FFD700',
    neonYellowDim: '#E9C400',
    neonPurple: '#D05BFF',
    cyberOrange: '#FFB300',
    onPrimary: '#3A3000',
    primaryContainer: '#FFD700',
    textMuted: '#C4C9AC',
    error: '#FFB4AB',
    gridLine: 'rgba(255, 215, 0, 0.05)',
  },
  space: {
    base: 4,
    gutter: 16,
    margin: 20,
    section: 24,
  },
  radius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
  },
  font: {
    headline: 'SpaceGrotesk_700Bold',
    headlineSemi: 'SpaceGrotesk_600SemiBold',
    body: 'Manrope_400Regular',
    bodySemi: 'Manrope_600SemiBold',
    label: 'JetBrainsMono_500Medium',
    labelReg: 'JetBrainsMono_400Regular',
  },
} as const;
