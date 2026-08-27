import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { Pressable, StyleSheet, View } from 'react-native';

import { theme } from '@/src/theme/tokens';

type Props = {
  onPress?: () => void;
  disabled?: boolean;
};

/** 시안 my_pick — 점선 테두리 '게임 등록' 슬롯 */
export function GameRegisterSlot({ onPress, disabled }: Props) {
  return (
    <Pressable
      disabled={disabled}
      onPress={() => {
        void Haptics.selectionAsync();
        onPress?.();
      }}
      accessibilityRole="button"
      accessibilityLabel="게임 등록"
      style={({ pressed }) => [
        styles.slot,
        pressed && !disabled && styles.pressed,
        disabled && styles.disabled,
      ]}
    >
      <View style={styles.circle}>
        <Ionicons
          name="add"
          size={26}
          color={disabled ? theme.color.outline : theme.color.onSurfaceVariant}
        />
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  slot: {
    flex: 1,
    minHeight: 0,
    borderRadius: theme.radius.lg,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: theme.color.outlineVariant,
    backgroundColor: 'rgba(32,31,32,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  pressed: {
    borderColor: 'rgba(255,215,0,0.55)',
    backgroundColor: 'rgba(255,215,0,0.06)',
  },
  disabled: {
    opacity: 0.45,
  },
  circle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
