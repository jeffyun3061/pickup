import { Text, type TextProps, type TextStyle } from 'react-native';

import { theme } from '@/src/theme/tokens';

type Variant = 'display' | 'title' | 'subtitle' | 'body' | 'caption' | 'label' | 'data';

const styles: Record<Variant, TextStyle> = {
  display: {
    fontFamily: theme.font.headline,
    fontSize: 28,
    lineHeight: 34,
    color: theme.color.onSurface,
    letterSpacing: -0.5,
  },
  title: {
    fontFamily: theme.font.headlineSemi,
    fontSize: 22,
    lineHeight: 28,
    color: theme.color.onSurface,
    letterSpacing: -0.3,
  },
  subtitle: {
    fontFamily: theme.font.headlineSemi,
    fontSize: 16,
    lineHeight: 22,
    color: theme.color.onSurface,
  },
  body: {
    fontFamily: theme.font.body,
    fontSize: 15,
    lineHeight: 22,
    color: theme.color.onSurface,
  },
  caption: {
    fontFamily: theme.font.body,
    fontSize: 13,
    lineHeight: 18,
    color: theme.color.onSurfaceVariant,
  },
  label: {
    fontFamily: theme.font.label,
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 1.2,
    color: theme.color.neonYellow,
    textTransform: 'uppercase',
  },
  data: {
    fontFamily: theme.font.labelReg,
    fontSize: 10,
    lineHeight: 12,
    color: theme.color.textMuted,
  },
};

/**
 * 앱 전역 텍스트.
 * 접근성 확대 시에도 레이아웃 붕괴를 막기 위해 배율을 제한한다.
 */
export function AppText({
  variant = 'body',
  style,
  maxFontSizeMultiplier = 1.2,
  ...props
}: TextProps & { variant?: Variant }) {
  return (
    <Text
      {...props}
      maxFontSizeMultiplier={maxFontSizeMultiplier}
      style={[styles[variant], style]}
    />
  );
}
