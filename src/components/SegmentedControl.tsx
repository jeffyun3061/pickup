import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/src/components/AppText';
import { theme } from '@/src/theme/tokens';

type Option<T extends string> = { value: T; label: string };

type Props<T extends string> = {
  value: T;
  options: Option<T>[];
  onChange: (value: T) => void;
};

/** 시안: 통합 소식 / 팝업&행사 */
export function SegmentedControl<T extends string>({
  value,
  options,
  onChange,
}: Props<T>) {
  return (
    <View style={styles.wrap}>
      {options.map((option) => {
        const active = option.value === value;
        return (
          <Pressable
            key={option.value}
            onPress={() => onChange(option.value)}
            style={[styles.item, active && styles.itemActive]}
          >
            <AppText style={[styles.label, active && styles.labelActive]}>
              {option.label}
            </AppText>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: 'row',
    backgroundColor: theme.color.surfaceContainerHigh,
    borderRadius: theme.radius.sm,
    borderWidth: 1,
    borderColor: 'rgba(68, 73, 51, 0.5)',
    padding: 4,
    gap: 4,
    marginBottom: theme.space.gutter,
  },
  item: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
    borderRadius: 2,
  },
  itemActive: {
    backgroundColor: theme.color.primaryContainer,
  },
  label: {
    fontFamily: theme.font.label,
    fontSize: 11,
    letterSpacing: 1,
    color: theme.color.onSurfaceVariant,
  },
  labelActive: {
    color: theme.color.onPrimary,
  },
});
