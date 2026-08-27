import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

let apiFetch: typeof import('@/src/data/apiClient').apiFetch;

beforeAll(async () => {
  // 테스트는 실제 API 호출 없이 URL 조립과 204 계약만 검증한다.
  vi.stubEnv('EXPO_PUBLIC_API_URL', 'http://127.0.0.1:8000');
  ({ apiFetch } = await import('@/src/data/apiClient'));
});

afterAll(() => vi.unstubAllEnvs());

describe('apiFetch', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('204 응답은 JSON 파싱 없이 성공으로 반환한다', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );

    await expect(apiFetch<void>('/api/v1/installations/me')).resolves.toBeUndefined();
  });

  it.each([
    [401, '인증이 필요합니다.'],
    [429, '잠시 후 다시 시도해 주세요.'],
    [500, '서버 오류가 발생했습니다.'],
  ])('%i 응답은 상태 코드와 서버 설명을 보존한다', async (status, detail) => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail }), {
          status,
          headers: { 'content-type': 'application/json' },
        }),
      ),
    );

    await expect(apiFetch('/api/v1/games')).rejects.toMatchObject({ status, message: detail });
  });

  it('네트워크 예외는 오프라인 화면이 처리할 수 있는 상태 0으로 표준화한다', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network down')));

    await expect(apiFetch('/api/v1/games')).rejects.toMatchObject({
      status: 0,
      message: '네트워크 연결을 확인해 주세요.',
    });
  });

  it('운영 API 주소가 없으면 localhost로 요청하지 않는다', async () => {
    vi.resetModules();
    vi.stubEnv('EXPO_PUBLIC_API_URL', '');
    const missingApi = await import('@/src/data/apiClient');

    await expect(missingApi.apiFetch('/api/v1/games')).rejects.toMatchObject({ status: 0 });
  });
});
