import { useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { Screen } from '@/src/components/Screen';
import { EmptyState, LoadingState } from '@/src/components/StateBlocks';
import { catalogRepository } from '@/src/data/catalog';
import { formatKstDate, type ServiceAnnouncement } from '@/src/domain/models';
import { theme } from '@/src/theme/tokens';

export default function AnnouncementDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [item, setItem] = useState<ServiceAnnouncement | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const list = await catalogRepository.listAnnouncements();
      if (mounted) {
        setItem(list.find((x) => x.id === id) ?? null);
        setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [id]);

  if (loading) {
    return (
      <Screen>
        <AppHeader showBack brand title="공지" />
        <LoadingState />
      </Screen>
    );
  }

  if (!item) {
    return (
      <Screen>
        <AppHeader showBack brand title="공지" />
        <EmptyState title="공지를 찾을 수 없어요" description="잘못된 링크입니다." />
      </Screen>
    );
  }

  return (
    <Screen>
      <AppHeader showBack brand title="공지" />
      <View style={styles.card}>
        <AppText variant="display">{item.title}</AppText>
        <AppText variant="data">발행 {formatKstDate(item.publishedAt)}</AppText>
        <AppText variant="body" style={{ marginTop: 12 }}>
          {item.body}
        </AppText>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: theme.color.surfaceContainer,
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.lg,
    padding: 18,
    gap: 8,
  },
});
