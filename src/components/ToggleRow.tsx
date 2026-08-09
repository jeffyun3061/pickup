import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, Switch, View } from 'react-native';

import { AppText } from '@/src/components/AppText';
import { theme } from '@/src/theme/tokens';

type Props = {
  title: string;
  description: string;
  value: boolean;
  onValueChange: () => void;
  icon?: keyof typeof Ionicons.glyphMap;
};

/** 설정 시안 토글 행 */
export function ToggleRow({
  title,
  description,
  value,
  onValueChange,
  icon = 'notifications-outline',
}: Props) {
  return (
    <View style={styles.row}>
      <Ionicons name={icon} size={22} color={theme.color.cyberOrange} style={styles.icon} />
      <View style={styles.copy}>
        <AppText variant="subtitle" numberOfLines={2}>
          {title}
        </AppText>
        <AppText variant="caption" numberOfLines={3}>
          {description}
        </AppText>
      </View>
      <View style={styles.switchWrap}>
        <Switch
          value={value}
          onValueChange={onValueChange}
          trackColor={{ false: theme.color.surfaceContainerHighest, true: '#5A4200' }}
          thumbColor={value ? theme.color.cyberOrange : '#888'}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: 'rgba(32, 31, 32, 0.7)',
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.lg,
    padding: 16,
    marginBottom: 12,
  },
  icon: { marginTop: 2, flexShrink: 0 },
  copy: { flex: 1, minWidth: 0, gap: 4, paddingRight: 8 },
  switchWrap: { flexShrink: 0 },
});
