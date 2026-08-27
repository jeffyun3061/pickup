import { type ReactNode } from 'react';
import {
  RefreshControl,
  ScrollView,
  StyleSheet,
  View,
  type ViewStyle,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useLayout } from '@/src/theme/useLayout';
import { theme } from '@/src/theme/tokens';

type Props = {
  children: ReactNode;
  scroll?: boolean;
  contentStyle?: ViewStyle;
  edges?: ('top' | 'right' | 'bottom' | 'left')[];
  /** 당겨서 새로고침 (scroll=true일 때만) */
  refreshing?: boolean;
  onRefresh?: () => void;
};

/** SafeArea + 폭별 margin. 하단 탭(≈72+inset)만큼 여백 확보 */
export function Screen({
  children,
  scroll = true,
  contentStyle,
  edges = ['top'],
  refreshing = false,
  onRefresh,
}: Props) {
  const layout = useLayout();

  return (
    <View style={styles.root}>
      <SafeAreaView style={styles.safe} edges={edges}>
        {scroll ? (
          <ScrollView
            contentContainerStyle={[
              styles.content,
              { paddingHorizontal: layout.margin, paddingBottom: 36 },
              contentStyle,
            ]}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
            refreshControl={
              onRefresh ? (
                <RefreshControl
                  refreshing={refreshing}
                  onRefresh={onRefresh}
                  tintColor={theme.color.neonYellow}
                  colors={[theme.color.neonYellow]}
                  progressBackgroundColor={theme.color.surfaceContainerHigh}
                />
              ) : undefined
            }
          >
            {children}
          </ScrollView>
        ) : (
          <View
            style={[
              styles.content,
              styles.fill,
              { paddingHorizontal: layout.margin, paddingBottom: 36 },
              contentStyle,
            ]}
          >
            {children}
          </View>
        )}
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: theme.color.background,
  },
  safe: { flex: 1 },
  fill: { flex: 1 },
  content: {
    flexGrow: 1,
  },
});
