import { Ionicons } from '@expo/vector-icons';
import * as Linking from 'expo-linking';
import { useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { Image, Pressable, StyleSheet, View } from 'react-native';

import { resolveImage, type AppImageName } from '@/src/assets/images';
import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { Screen } from '@/src/components/Screen';
import { EmptyState, LoadingState } from '@/src/components/StateBlocks';
import { catalogRepository } from '@/src/data/catalog';
import {
  formatKstDate,
  kindLabel,
  type ContentItem,
} from '@/src/domain/models';
import { theme } from '@/src/theme/tokens';

export default function ContentDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [item, setItem] = useState<ContentItem | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      const list = await catalogRepository.listContent('all', []);
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
        <AppHeader showBack brand title="DETAIL" rightSlot={null} />
        <LoadingState />
      </Screen>
    );
  }

  if (!item) {
    return (
      <Screen>
        <AppHeader showBack brand title="DETAIL" rightSlot={null} />
        <EmptyState
          title="소식을 찾을 수 없어요"
          description="아직 발행되지 않았거나 잘못된 링크입니다."
        />
      </Screen>
    );
  }

  const cover = resolveImage(item.imageKey as AppImageName | undefined);

  return (
    <Screen>
      <AppHeader showBack brand title="DETAIL" subtitle={item.gameName} rightSlot={null} />
      {cover ? (
        <View style={styles.coverWrap}>
          <Image source={cover} style={styles.cover} resizeMode="cover" />
          <View style={styles.coverBadge}>
            <AppText style={styles.coverBadgeText}>{kindLabel(item.kind)}</AppText>
          </View>
        </View>
      ) : null}
      <View style={styles.hero}>
        <AppText variant="label">{item.gameName}</AppText>
        <AppText variant="display" style={styles.title}>
          {item.title}
        </AppText>
        <AppText variant="data">발행 {formatKstDate(item.publishedAt)}</AppText>
      </View>
      <View style={styles.block}>
        <AppText variant="label">요약</AppText>
        {item.summaryPoints.map((point) => (
          <View key={point} style={styles.point}>
            <AppText style={{ color: theme.color.neonYellow }}>▶</AppText>
            <AppText variant="body" style={{ flex: 1 }}>
              {point}
            </AppText>
          </View>
        ))}
      </View>
      <Pressable
        onPress={() => void Linking.openURL(item.officialUrl)}
        style={styles.cta}
      >
        <Ionicons name="open-outline" size={18} color={theme.color.onPrimary} />
        <AppText style={styles.ctaText}>공식 원문 보기</AppText>
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  coverWrap: {
    height: 180,
    borderRadius: theme.radius.lg,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    marginBottom: 14,
    backgroundColor: theme.color.surfaceContainerHighest,
  },
  cover: { width: '100%', height: '100%' },
  coverBadge: {
    position: 'absolute',
    top: 12,
    left: 12,
    backgroundColor: theme.color.primaryContainer,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 2,
  },
  coverBadgeText: {
    fontFamily: theme.font.label,
    fontSize: 10,
    color: theme.color.onPrimary,
  },
  hero: {
    backgroundColor: theme.color.surfaceContainer,
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.lg,
    padding: 18,
    gap: 10,
    marginBottom: 16,
  },
  title: { fontSize: 24, lineHeight: 30 },
  block: {
    backgroundColor: theme.color.surfaceContainer,
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.lg,
    padding: 16,
    gap: 10,
    marginBottom: 16,
  },
  point: { flexDirection: 'row', gap: 8, alignItems: 'flex-start' },
  cta: {
    backgroundColor: theme.color.primaryContainer,
    borderRadius: theme.radius.sm,
    paddingVertical: 14,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  ctaText: {
    fontFamily: theme.font.label,
    color: theme.color.onPrimary,
    letterSpacing: 1,
  },
});
