import { type Href, router } from 'expo-router';
import * as WebBrowser from 'expo-web-browser';
import { Alert, Pressable, StyleSheet } from 'react-native';

import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { Screen } from '@/src/components/Screen';
import { ToggleRow } from '@/src/components/ToggleRow';
import { useCatalog } from '@/src/hooks/useCatalog';
import { useApp } from '@/src/state/AppProvider';
import { theme } from '@/src/theme/tokens';

const PUBLIC_API_URL = (process.env.EXPO_PUBLIC_API_URL ?? '').replace(/\/+$/, '');

/** 사용자가 실제로 조절하는 알림 3종만 노출한다. 게임별 토글은 두지 않는다. */
export default function SettingsScreen() {
  const { preferences, setNotifications, resetLocalData } = useApp();
  const { announcements } = useCatalog();
  const n = preferences.notifications;

  const toggle = async (key: keyof typeof n) => {
    await setNotifications({ ...n, [key]: !n[key] });
  };

  return (
    <Screen>
      <AppHeader title="설정" />

      <AppText variant="label" style={styles.sectionTop}>
        알림
      </AppText>

      <ToggleRow
        icon="newspaper-outline"
        title="내 게임 새 소식"
        description="선택 게임의 새 소식 알림"
        value={n.selectedGameNews}
        onValueChange={() => void toggle('selectedGameNews')}
      />
      <ToggleRow
        icon="alarm-outline"
        title="이벤트 마감 알림"
        description="진행 중인 기간 콘텐츠가 곧 끝날 때"
        value={n.eventEnding}
        onValueChange={() => void toggle('eventEnding')}
      />
      <ToggleRow
        icon="megaphone-outline"
        title="피키 공지"
        description="서비스 점검과 운영 소식을 알려드려요"
        value={n.serviceNotices}
        onValueChange={() => void toggle('serviceNotices')}
      />

      {announcements.length > 0 ? (
        <>
          <AppText variant="label" style={styles.section}>
            공지
          </AppText>
          {announcements.map((item) => (
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
          ))}
        </>
      ) : null}

      <AppText variant="label" style={styles.section}>
        지원
      </AppText>
      <Pressable onPress={() => router.push('/inquiry' as Href)} style={styles.link}>
        <AppText variant="subtitle">문의하기</AppText>
        <AppText variant="caption">버그·제안·콘텐츠 문의 (로그인 불필요)</AppText>
      </Pressable>

      {PUBLIC_API_URL ? (
        <>
          <AppText variant="label" style={styles.section}>
            정책
          </AppText>
          <Pressable
            onPress={() => void WebBrowser.openBrowserAsync(`${PUBLIC_API_URL}/privacy`)}
            style={styles.link}
          >
            <AppText variant="subtitle">개인정보처리방침</AppText>
            <AppText variant="caption">수집 정보와 삭제·문의 방법</AppText>
          </Pressable>
          <Pressable
            onPress={() => void WebBrowser.openBrowserAsync(`${PUBLIC_API_URL}/terms`)}
            style={styles.link}
          >
            <AppText variant="subtitle">이용약관</AppText>
            <AppText variant="caption">원문 링크와 타키의 참고 정리 안내</AppText>
          </Pressable>
        </>
      ) : null}

      <AppText variant="label" style={styles.section}>
        데이터
      </AppText>
      <Pressable
        onPress={() =>
          Alert.alert(
            '앱 데이터 초기화',
            '관심 게임, 읽음 기록, 북마크와 알림 설정이 모두 지워집니다. 계속할까요?',
            [
              { text: '취소', style: 'cancel' },
              {
                text: '초기화',
                style: 'destructive',
                onPress: () => {
                  void resetLocalData().then(() => router.replace('/'));
                },
              },
            ],
          )
        }
        style={styles.danger}
      >
        <AppText style={styles.dangerText}>앱 데이터 초기화</AppText>
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  sectionTop: { marginTop: 10, marginBottom: 10, color: theme.color.cyberOrange },
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
