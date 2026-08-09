import { useMemo, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { FeedCard } from '@/src/components/FeedCard';
import { Screen } from '@/src/components/Screen';
import { SegmentedControl } from '@/src/components/SegmentedControl';
import { EmptyState, LoadingState } from '@/src/components/StateBlocks';
import { isOfflineKind } from '@/src/domain/models';
import { useCatalog } from '@/src/hooks/useCatalog';

type Segment = 'game' | 'offline';

/** 시안 feed_unified_refined */
export default function NewsScreen() {
  const [segment, setSegment] = useState<Segment>('game');
  const { loading, content } = useCatalog();

  const items = useMemo(() => {
    return content
      .filter((item) =>
        segment === 'game' ? !isOfflineKind(item.kind) : isOfflineKind(item.kind),
      )
      .sort((a, b) => +new Date(b.publishedAt) - +new Date(a.publishedAt));
  }, [content, segment]);

  return (
    <Screen>
      <AppHeader title="NEWS FEED" />
      <SegmentedControl
        value={segment}
        onChange={setSegment}
        options={[
          { value: 'game', label: '통합 소식' },
          { value: 'offline', label: '팝업&행사' },
        ]}
      />

      <View style={styles.count}>
        <AppText variant="data">{loading ? '…' : `${items.length} ITEMS`}</AppText>
      </View>

      {loading ? <LoadingState /> : null}

      {!loading && items.length === 0 ? (
        <EmptyState
          icon="newspaper-outline"
          title={segment === 'game' ? '통합 소식이 비어 있어요' : '팝업·행사가 비어 있어요'}
          description="검수 후 발행된 콘텐츠만 표시합니다. 앞으로 등록·발행하면 이 목록이 채워집니다."
        />
      ) : null}

      {items.map((item) => (
        <FeedCard key={item.id} item={item} />
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  count: { marginBottom: 8 },
});
