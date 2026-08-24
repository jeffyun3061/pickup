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

/** 시안 BottomNav — 360dp에서도 라벨이 잘리지 않게 short/full 전환 */
export function CustomTabBar({ state, navigation }: TabBarProps) {
  const insets = useSafeAreaInsets();
  const layout = useLayout();

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
          const label = layout.tabLabel === 'short' ? meta.shortLabel : meta.label;

          return (
            <Pressable
              key={route.key}
              accessibilityRole="button"
              accessibilityLabel={meta.label}
              accessibilityState={focused ? { selected: true } : {}}
              onPress={() => {
                void Haptics.selectionAsync();
                const event = navigation.emit({
                  type: 'tabPress',
                  target: route.key,
                  canPreventDefault: true,
                });
                if (!focused && !event.defaultPrevented) {
                  navigation.navigate(route.name, route.params);
                }
              }}
              style={styles.item}
            >
              <View style={[styles.pill, focused && styles.pillActive]}>
                <Ionicons
                  name={focused ? meta.activeIcon ?? meta.icon : meta.icon}
                  size={layout.isCompact ? 18 : 20}
                  color={focused ? theme.color.onPrimary : theme.color.textMuted}
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
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: 6,
  },
  bar: {
    flexDirection: 'row',
    alignItems: 'stretch',
    backgroundColor: 'rgba(14, 14, 15, 0.96)',
    borderTopLeftRadius: theme.radius.xl,
    borderTopRightRadius: theme.radius.xl,
    borderWidth: 1,
    borderColor: 'rgba(68, 73, 51, 0.6)',
    paddingTop: 6,
    paddingBottom: 4,
    paddingHorizontal: 2,
  },
  item: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 0,
  },
  pill: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
    paddingVertical: 6,
    borderRadius: theme.radius.md,
    gap: 2,
    width: '100%',
    maxWidth: 72,
  },
  pillActive: {
    backgroundColor: theme.color.primaryContainer,
    shadowColor: theme.color.neonYellow,
    shadowOpacity: 0.4,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 0 },
    elevation: 5,
    transform: [{ translateY: -2 }],
  },
  label: {
    fontFamily: theme.font.labelReg,
    fontSize: 9,
    color: theme.color.textMuted,
    textAlign: 'center',
    width: '100%',
  },
  labelActive: {
    color: theme.color.onPrimary,
    fontFamily: theme.font.label,
  },
});
