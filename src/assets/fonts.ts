/**
 * 폰트 인덱스 매핑.
 * - 화면/레이아웃은 여기 키만 참조한다.
 * - .ttf는 사용하는 weight만 require (배럴 import 금지 — Metro/Windows 해석 이슈).
 * - theme.tokens.font 이름과 키를 일치시킨다.
 */
export const fontAssets = {
  SpaceGrotesk_600SemiBold: require('@expo-google-fonts/space-grotesk/600SemiBold/SpaceGrotesk_600SemiBold.ttf'),
  SpaceGrotesk_700Bold: require('@expo-google-fonts/space-grotesk/700Bold/SpaceGrotesk_700Bold.ttf'),
  Manrope_400Regular: require('@expo-google-fonts/manrope/400Regular/Manrope_400Regular.ttf'),
  Manrope_600SemiBold: require('@expo-google-fonts/manrope/600SemiBold/Manrope_600SemiBold.ttf'),
  JetBrainsMono_400Regular: require('@expo-google-fonts/jetbrains-mono/400Regular/JetBrainsMono_400Regular.ttf'),
  JetBrainsMono_500Medium: require('@expo-google-fonts/jetbrains-mono/500Medium/JetBrainsMono_500Medium.ttf'),
} as const;

export type AppFontName = keyof typeof fontAssets;
