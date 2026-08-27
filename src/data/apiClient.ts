const configuredApiBase = (process.env.EXPO_PUBLIC_API_URL ?? '').trim();
const isDevelopment = typeof __DEV__ !== 'undefined' && __DEV__;
const REQUEST_TIMEOUT_MS = 15_000;
// 로컬 개발에서만 localhost를 허용한다. API 모드 릴리스가 잘못된
// localhost 주소로 배포되어 영구적으로 연결 실패하는 상황을 막는다.
const API_BASE = (configuredApiBase || (isDevelopment ? 'http://127.0.0.1:8000' : '')).replace(/\/$/, '');

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  if (!API_BASE) {
    throw new ApiError(
      '운영 API 주소가 설정되지 않았습니다. 앱을 최신 버전으로 업데이트해 주세요.',
      0,
    );
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const externalSignal = init?.signal;
  const forwardAbort = () => controller.abort();
  if (externalSignal) {
    if (externalSignal.aborted) controller.abort();
    else externalSignal.addEventListener('abort', forwardAbort, { once: true });
  }

  try {
    let res: Response;
    try {
      res = await fetch(`${API_BASE}${path}`, {
        ...init,
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
          ...(init?.headers ?? {}),
        },
      });
    } catch {
      const timedOut = controller.signal.aborted && !externalSignal?.aborted;
      throw new ApiError(
        timedOut
          ? '서버 응답이 늦어 연결을 종료했습니다. 잠시 후 다시 시도해 주세요.'
          : '네트워크 연결을 확인해 주세요.',
        0,
      );
    }

    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = (await res.json()) as { detail?: string };
        if (body.detail) detail = body.detail;
      } catch {
        /* ignore */
      }
      throw new ApiError(detail, res.status);
    }
    // DELETE/204 응답은 JSON 본문이 없다. 빈 본문을 JSON으로 파싱하려다
    // 성공 요청을 실패로 오인하지 않도록 호출자 계약만 만족시킨다.
    if (res.status === 204 || res.headers.get('content-length') === '0') {
      return undefined as T;
    }
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timeout);
    externalSignal?.removeEventListener('abort', forwardAbort);
  }
}

export function getApiBaseUrl(): string {
  return API_BASE;
}
