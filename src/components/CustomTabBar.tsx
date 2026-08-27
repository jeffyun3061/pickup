import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { Pressable, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { AppText } from '@/src/components/AppText';
import { useLayout } from '@/src/theme/useLayout';
import { theme } from '@/src/theme/tokens';

const META: Record<
  string,
  {
    label: string;
    shortLabel: string;
    icon: keyof typeof Ionicons.glyphMap;
    activeIcon?: keyof typeof Ionicons.glyphMap;
  }
> = {
  news: {
    label: '새 소식',
    shortLabel: '뉴스',
    icon: 'newspaper-outline',
    activeIcon: 'newspaper',
  },
  games: {
    label: '마이 픽',
    shortLabel: '마이픽',
    icon: 'game-controller-outline',
    activeIcon: 'game-controller',
  },
  index: { label: '홈', shortLabel: '홈', icon: 'home-outline', activeIcon: 'home' },
  ranking: {
    label: '랭킹',
    shortLabel: '랭킹',
    icon: 'trophy-outline',
    activeIcon: 'trophy',
  },
  settings: {
    label: '설정',
    shortLabel: '설정',
    icon: 'settings-outline',
    activeIcon: 'settings',
  },
};

/** 가운데 원형으로 띄우는 핵심 탭 */
const CENTER_ROUTE = 'index';

type TabBarProps = {
  state: {
    index: number;
    routes: { key: string; name: string; params?: object }[];
  };
  navigation: {
    emit: (event: {
      type: string;
      target: string;
      canPreventDefault: boolean;
    }) => { defaultPrevented: boolean };
    navigate: (name: string, params?: object) => void;
  };
};

/**
 * BottomNav — 홈이 서비스의 핵심이라 가운데 원형 버튼으로 승격.
 * 360dp에서도 라벨이 잘리지 않게 short/full 전환 유지.
 */
export function CustomTabBar({ state, navigation }: TabBarProps) {
  const insets = useSafeAreaInsets();
  const layout = useLayout();

  const onPress = (route: { key: string; name: string; params?: object }, focused: boolean) => {
    void Haptics.selectionAsync();
    const event = navigation.emit({
      type: 'tabPress',
      target: route.key,
      canPreventDefault: true,
    });
    if (!focused && !event.defaultPrevented) {
      navigation.navigate(route.name, route.params);
    }
  };

  return (
    <View style={[styles.shell, { paddingBottom: Math.max(insets.bottom, 8) }]}>
      <View style={styles.bar}>
        {state.routes.map((route, index) => {
          const focused = state.index === index;
          const meta = META[route.name] ?? {
            label: route.name,
            shortLabel: route.name,
            icon: 'ellipse-outline' as const,
          };

          if (route.name === CENTER_ROUTE) {
            return (
              <View key={route.key} style={styles.centerSlot}>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel={meta.label}
                  accessibilityState={focused ? { selected: true } : {}}
                  onPress={() => onPress(route, focused)}
                  style={({ pressed }) => [
                    styles.centerButton,
                    focused && styles.centerButtonActive,
                    pressed && styles.centerButtonPressed,
                  ]}
                >
                  <Ionicons
                    name={focused ? meta.activeIcon ?? meta.icon : meta.icon}
                    size={26}
                    color={focused ? theme.color.onPrimary : theme.color.neonYellow}
                  />
                </Pressable>
                <AppText style={[styles.label, focused && styles.centerLabelActive]}>
                  {meta.shortLabel}
                </AppText>
              </View>
            );
          }

          const label = layout.tabLabel === 'short' ? meta.shortLabel : meta.label;

          return (
            <Pressable
              key={route.key}
              accessibilityRole="button"
              accessibilityLabel={meta.label}
              accessibilityState={focused ? { selected: true } : {}}
              onPress={() => onPress(route, focused)}
              style={styles.item}
            >
              <View style={styles.pill}>
                <Ionicons
                  name={focused ? meta.activeIcon ?? meta.icon : meta.icon}
                  size={layout.isCompact ? 19 : 21}
                  color={focused ? theme.color.neonYellow : theme.color.textMuted}
                />
                <AppText
                  style={[styles.label, focused && styles.labelActive]}
                  numberOfLines={1}
                  adjustsFontSizeToFit
                  minimumFontScale={0.85}
                >
                  {label}
                </AppText>
              </View>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  shell: {
    paddingHorizontal: 6,
    paddingTop: 30,
    backgroundColor: theme.color.background,
  },
  bar: {
    flexDirection: 'row',
    alignItems: 'stretch',
    backgroundColor: 'rgba(14, 14, 15, 0.97)',
    borderTopLeftRadius: theme.radius.xl,
    borderTopRightRadius: theme.radius.xl,
    borderWidth: 1,
    borderColor: 'rgba(68, 73, 51, 0.6)',
    paddingTop: 8,
    paddingBottom: 6,
    paddingHorizontal: 2,
  },
  item: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'flex-end',
    minWidth: 0,
  },
  pill: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
    paddingVertical: 4,
    gap: 3,
    width: '100%',
    maxWidth: 72,
  },
  centerSlot: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'flex-end',
    minWidth: 0,
    gap: 3,
    paddingVertical: 4,
  },
  centerButton: {
    width: 54,
    height: 54,
    borderRadius: 27,
    marginTop: -30,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.color.surfaceLowest,
    borderWidth: 1.5,
    borderColor: theme.color.neonYellow,
  },
  centerButtonActive: {
    backgroundColor: theme.color.primaryContainer,
    borderColor: theme.color.primaryContainer,
  },
  centerButtonPressed: {
    transform: [{ scale: 0.94 }],
  },
  centerLabelActive: {
    color: theme.color.neonYellow,
    fontFamily: theme.font.label,
  },
  label: {
    fontFamily: theme.font.labelReg,
    fontSize: 9,
    color: theme.color.textMuted,
    textAlign: 'center',
  },
  labelActive: {
    color: theme.color.neonYellow,
    fontFamily: theme.font.label,
  },
});
