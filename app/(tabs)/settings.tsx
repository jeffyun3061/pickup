import { type Href, router } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { Screen } from '@/src/components/Screen';
import { ToggleRow } from '@/src/components/ToggleRow';
import { useCatalog } from '@/src/hooks/useCatalog';
import { useApp } from '@/src/state/AppProvider';
import { theme } from '@/src/theme/tokens';

/** 시안 settings_unified + 제품 알림 3종 계약 */
export default function SettingsScreen() {
  const { preferences, setNotifications, resetLocalData } = useApp();
  const { announcements } = useCatalog();
  const n = preferences.notifications;

  const toggle = async (key: keyof typeof n) => {
    await setNotifications({ ...n, [key]: !n[key] });
  };

  return (
    <Screen>
      <AppHeader title="SETTINGS" />

      <View style={styles.info}>
        <AppText variant="label">시스템 설정</AppText>
        <AppText variant="body" style={{ marginTop: 10 }}>
          알림은 세 가지만 저장합니다. 게임별 토글은 없습니다.
        </AppText>
      </View>

      <ToggleRow
        icon="newspaper-outline"
        title="선택 게임 새 소식"
        description="마이 픽 게임에 발행된 소식"
        value={n.selectedGameNews}
        onValueChange={() => void toggle('selectedGameNews')}
      />
      <ToggleRow
        icon="alarm-outline"
        title="종료 임박"
        description="이벤트·팝업 종료 전 알림"
        value={n.eventEnding}
        onValueChange={() => void toggle('eventEnding')}
      />
      <ToggleRow
        icon="megaphone-outline"
        title="서비스 공지"
        description="GamePickup 운영 안내"
        value={n.serviceNotices}
        onValueChange={() => void toggle('serviceNotices')}
      />

      <AppText variant="label" style={styles.section}>
        공지
      </AppText>
      {announcements.length === 0 ? (
        <AppText variant="caption" style={{ marginBottom: 16 }}>
          등록된 서비스 공지가 없습니다.
        </AppText>
      ) : (
        announcements.map((item) => (
          <Pressable
            key={item.id}
            onPress={() => router.push(`/announcement/${item.id}`)}
            style={styles.link}
          >
            <AppText variant="subtitle">{item.title}</AppText>
            <AppText variant="caption" numberOfLines={1}>
              {item.body}
            </AppText>
          </Pressable>
        ))
      )}

      <AppText variant="label" style={styles.section}>
        지원
      </AppText>
      <Pressable onPress={() => router.push('/inquiry' as Href)} style={styles.link}>
        <AppText variant="subtitle">문의하기</AppText>
        <AppText variant="caption">버그·제안·콘텐츠 문의 (로그인 불필요)</AppText>
      </Pressable>

      <AppText variant="label" style={styles.section}>
        데이터
      </AppText>
      <Pressable
        onPress={async () => {
          await resetLocalData();
          router.replace('/onboarding');
        }}
        style={styles.danger}
      >
        <AppText style={styles.dangerText}>앱 데이터 초기화</AppText>
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  info: {
    backgroundColor: 'rgba(32, 31, 32, 0.85)',
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.lg,
    padding: 18,
    marginBottom: 20,
  },
  section: {
    marginTop: 12,
    marginBottom: 10,
    color: theme.color.cyberOrange,
  },
  link: {
    backgroundColor: theme.color.surfaceContainer,
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.md,
    padding: 14,
    marginBottom: 10,
    gap: 4,
  },
  danger: {
    borderWidth: 1,
    borderColor: theme.color.error,
    borderRadius: theme.radius.md,
    paddingVertical: 14,
    alignItems: 'center',
  },
  dangerText: {
    fontFamily: theme.font.label,
    color: theme.color.error,
    letterSpacing: 1,
  },
});
