import { router } from 'expo-router';
import { useState } from 'react';
import { Alert, Pressable, StyleSheet, TextInput, View } from 'react-native';

import { AppHeader } from '@/src/components/AppHeader';
import { AppText } from '@/src/components/AppText';
import { Screen } from '@/src/components/Screen';
import { submitInquiry } from '@/src/data/inquiryApi';
import { theme } from '@/src/theme/tokens';

const CATEGORIES = [
  { id: 'general', label: '일반' },
  { id: 'bug', label: '오류/버그' },
  { id: 'content', label: '콘텐츠' },
  { id: 'other', label: '기타' },
] as const;

/** 설정 → 문의하기 (로그인 없이 서버로 전송) */
export default function InquiryScreen() {
  const [category, setCategory] = useState<(typeof CATEGORIES)[number]['id']>('general');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);

  const canSend = message.trim().length >= 5 && !sending;

  const onSubmit = async () => {
    if (!canSend) return;
    setSending(true);
    try {
      await submitInquiry({
        category,
        email: email.trim() || undefined,
        message: message.trim(),
      });
      Alert.alert('접수 완료', '문의가 전달되었습니다. 확인 후 반영할게요.', [
        { text: '확인', onPress: () => router.back() },
      ]);
    } catch (e) {
      Alert.alert('전송 실패', e instanceof Error ? e.message : '다시 시도해 주세요.');
    } finally {
      setSending(false);
    }
  };

  return (
    <Screen>
      <AppHeader showBack brand title="INQUIRY" rightSlot={null} />
      <AppText variant="display" style={styles.hero}>
        문의하기
      </AppText>
      <AppText variant="caption" style={styles.desc}>
        로그인 없이 보낼 수 있어요. 운영자가 관리자 화면에서 확인합니다.
      </AppText>

      <AppText variant="label" style={styles.label}>
        분류
      </AppText>
      <View style={styles.chips}>
        {CATEGORIES.map((c) => (
          <Pressable
            key={c.id}
            onPress={() => setCategory(c.id)}
            style={[styles.chip, category === c.id && styles.chipOn]}
          >
            <AppText style={[styles.chipText, category === c.id && styles.chipTextOn]}>
              {c.label}
            </AppText>
          </Pressable>
        ))}
      </View>

      <AppText variant="label" style={styles.label}>
        이메일 (선택)
      </AppText>
      <TextInput
        value={email}
        onChangeText={setEmail}
        placeholder="회신이 필요하면 남겨주세요"
        placeholderTextColor={theme.color.textMuted}
        keyboardType="email-address"
        autoCapitalize="none"
        style={styles.input}
      />

      <AppText variant="label" style={styles.label}>
        내용
      </AppText>
      <TextInput
        value={message}
        onChangeText={setMessage}
        placeholder="최소 5자"
        placeholderTextColor={theme.color.textMuted}
        multiline
        style={[styles.input, styles.textarea]}
      />

      <Pressable
        disabled={!canSend}
        onPress={() => void onSubmit()}
        style={[styles.cta, !canSend && styles.ctaDisabled]}
      >
        <AppText style={styles.ctaText}>{sending ? '전송 중…' : '보내기'}</AppText>
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: { marginBottom: 8, color: theme.color.onSurface },
  desc: { marginBottom: 20 },
  label: { marginBottom: 8, color: theme.color.cyberOrange },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 },
  chip: {
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    borderRadius: theme.radius.sm,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: theme.color.surfaceContainer,
  },
  chipOn: { borderColor: theme.color.neonYellow },
  chipText: {
    fontFamily: theme.font.label,
    fontSize: 11,
    color: theme.color.onSurfaceVariant,
  },
  chipTextOn: { color: theme.color.neonYellow },
  input: {
    borderWidth: 1,
    borderColor: theme.color.outlineVariant,
    backgroundColor: theme.color.surfaceContainer,
    borderRadius: theme.radius.md,
    color: theme.color.onSurface,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginBottom: 16,
    fontFamily: theme.font.body,
    fontSize: 15,
  },
  textarea: { minHeight: 140, textAlignVertical: 'top' },
  cta: {
    backgroundColor: theme.color.primaryContainer,
    borderRadius: theme.radius.sm,
    alignItems: 'center',
    paddingVertical: 16,
    marginTop: 8,
  },
  ctaDisabled: { backgroundColor: theme.color.surfaceContainerHighest },
  ctaText: {
    fontFamily: theme.font.label,
    color: theme.color.onPrimary,
    letterSpacing: 1.2,
  },
});
