import { type ReactNode } from 'react';
import { ScrollView, StyleSheet, View, type ViewStyle } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useLayout } from '@/src/theme/useLayout';
import { theme } from '@/src/theme/tokens';

type Props = {
  children: ReactNode;
  scroll?: boolean;
  contentStyle?: ViewStyle;
  edges?: ('top' | 'right' | 'bottom' | 'left')[];
};

/** SafeArea + 폭별 margin. 하단 탭(≈72+inset)만큼 여백 확보 */
export function Screen({
  children,
  scroll = true,
  contentStyle,
  edges = ['top'],
}: Props) {
  const layout = useLayout();

  return (
    <View style={styles.root}>
      <SafeAreaView style={styles.safe} edges={edges}>
        {scroll ? (
          <ScrollView
            contentContainerStyle={[
              styles.content,
              { paddingHorizontal: layout.margin, paddingBottom: 112 },
              contentStyle,
            ]}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
          >
            {children}
          </ScrollView>
        ) : (
          <View
            style={[
              styles.content,
              styles.fill,
              { paddingHorizontal: layout.margin, paddingBottom: 112 },
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
