import * as SecureStore from 'expo-secure-store';

/**
 * 민감 설치 자격증명 전용 저장소.
 * - 예: 서버가 발급한 installation_id + secret
 * - 환경설정(알림 토글 등)은 여기 넣지 않는다 (ADR-007).
 * - 아직 설치 API 연동 전이므로 인터페이스와 키만 고정한다.
 */
export const INSTALLATION_SECRET_KEY = 'gamepickup.installation.secret.v1';

export type InstallationCredential = {
  installationId: string;
  secret: string;
};

export type CredentialStore = {
  load(): Promise<InstallationCredential | null>;
  save(credential: InstallationCredential): Promise<void>;
  clear(): Promise<void>;
};

function serialize(credential: InstallationCredential): string {
  return JSON.stringify(credential);
}

function parse(raw: string | null): InstallationCredential | null {
  if (!raw) return null;
  try {
    const value = JSON.parse(raw) as Partial<InstallationCredential>;
    if (
      typeof value.installationId === 'string' &&
      typeof value.secret === 'string' &&
      value.installationId.length > 0 &&
      value.secret.length > 0
    ) {
      return {
        installationId: value.installationId,
        secret: value.secret,
      };
    }
    return null;
  } catch {
    return null;
  }
}

export const credentialStore: CredentialStore = {
  async load() {
    const raw = await SecureStore.getItemAsync(INSTALLATION_SECRET_KEY);
    return parse(raw);
  },
  async save(credential) {
    await SecureStore.setItemAsync(INSTALLATION_SECRET_KEY, serialize(credential));
  },
  async clear() {
    await SecureStore.deleteItemAsync(INSTALLATION_SECRET_KEY);
  },
};
