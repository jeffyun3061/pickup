const TOKEN_KEY = 'piky.admin.token';
const SESSION_EXPIRED_KEY = 'piky.admin.sessionExpired';
const REQUEST_TIMEOUT_MS = 15_000;

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

/** 로그인 화면이 세션 만료 안내를 1회 표시할 때 사용한다 */
export function consumeSessionExpired(): boolean {
  if (sessionStorage.getItem(SESSION_EXPIRED_KEY)) {
    sessionStorage.removeItem(SESSION_EXPIRED_KEY);
    return true;
  }
  return false;
}

/** 백엔드는 타임존 표기 없는 UTC 시각을 반환하므로 Z를 붙여 로컬 시각으로 변환한다 */
export function parseUtc(value: string): Date {
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value);
  return new Date(hasTimezone ? value : `${value}Z`);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  // FormData는 브라우저가 boundary 포함 Content-Type을 직접 설정한다
  if (!headers.has('Content-Type') && init.body && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  const token = getToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const controller = new AbortController();
  const externalSignal = init.signal;
  const forwardAbort = () => controller.abort();
  if (externalSignal) {
    if (externalSignal.aborted) controller.abort();
    else externalSignal.addEventListener('abort', forwardAbort, { once: true });
  }
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    let res: Response;
    try {
      res = await fetch(path, { ...init, headers, signal: controller.signal });
    } catch (error) {
      if (controller.signal.aborted && !externalSignal?.aborted) {
        throw new Error('서버 응답이 늦어 연결을 종료했습니다. 잠시 후 다시 시도해 주세요.');
      }
      throw error;
    }

    // 토큰 만료·폐기 시 조용한 401 폴링을 멈추고 로그인 화면으로 복귀한다
    if (res.status === 401 && !path.endsWith('/login') && getToken()) {
      setToken(null);
      sessionStorage.setItem(SESSION_EXPIRED_KEY, '1');
      window.location.reload();
      throw new Error('세션이 만료되었습니다. 다시 로그인하세요.');
    }
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail ?? JSON.stringify(body);
      } catch {
        /* ignore */
      }
      throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }
    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timeout);
    externalSignal?.removeEventListener('abort', forwardAbort);
  }
}

export type Game = {
  id: string;
  name: string;
  initial: string;
  genre: string;
  color: string;
  interest_count: number;
  image_url?: string | null;
  image_source_url?: string | null;
  image_rights_status: ImageRightsStatus;
  fallback_image_key: string;
};

export type ImageRightsStatus = 'unverified' | 'official' | 'licensed' | 'original';

export type Content = {
  id: string;
  game_id: string;
  game_name: string;
  kind: string;
  title: string;
  summary_points: string[];
  official_url: string;
  image_url?: string | null;
  image_source_url?: string | null;
  image_rights_status: ImageRightsStatus;
  fallback_image_key: string;
  place?: string | null;
  reservation_url?: string | null;
  starts_at?: string | null;
  ends_at?: string | null;
  status?: string;
  published_at?: string | null;
  idempotency_key?: string | null;
  summary_status?: 'none' | 'pending' | 'done' | 'failed' | null;
  source_id?: string | null;
  created_at?: string | null;
  summarized_at?: string | null;
  origin_published_at?: string | null;
  raw_text_excerpt?: string | null;
  needs_review_reason?: string | null;
  scheduled_publish_at?: string | null;
  link_broken?: boolean | null;
  auto_published?: boolean | null;
};

export type Inquiry = {
  id: string;
  email?: string | null;
  category: string;
  message: string;
  status: string;
  created_at: string;
};

export type SourceType = 'rss' | 'api' | 'html';

export type IngestSource = {
  id: string;
  name: string;
  source_type: SourceType;
  game_id: string;
  game_name: string;
  endpoint_url: string;
  interval_minutes: number;
  enabled: boolean;
  auto_publish: boolean;
  config: Record<string, string>;
  secret_env_name?: string | null;
  next_run_at?: string | null;
  last_run_at?: string | null;
  last_status?: string | null;
  consecutive_failures: number;
  consecutive_empty_runs: number;
  health: 'ok' | 'failing' | 'quiet';
  created_at: string;
  stat_approved: number;
  stat_edited: number;
  stat_retracted: number;
  promote_suggested: boolean;
};

export type PushStats = {
  pending: number;
  sent: number;
  failed: number;
  last_sent_at?: string | null;
};

export type UserStats = {
  installations: number;
  with_device_token: number;
  notify_selected_game_news: number;
  notify_event_ending: number;
  notify_service_notices: number;
  top_games: { game_id: string; game_name: string; pick_count: number }[];
};

export type AuditLog = {
  id: string;
  actor: string;
  action: string;
  entity: string;
  entity_id: string;
  detail: string;
  created_at: string;
};

export type IngestRun = {
  id: string;
  source_id: string;
  source_name: string;
  status: 'pending' | 'running' | 'succeeded' | 'failed';
  attempt: number;
  items_seen: number;
  items_created: number;
  not_modified: boolean;
  error?: string | null;
  queued_at: string;
  started_at?: string | null;
  completed_at?: string | null;
};

export type SourcePreviewItem = {
  external_id: string;
  title: string;
  url: string;
  summary: string;
  image_url?: string | null;
  published_at?: string | null;
};

export type SourcePreview = {
  items: SourcePreviewItem[];
  warning?: string | null;
};

export const api = {
  login: (username: string, password: string) =>
    request<{ access_token: string }>('/api/v1/admin/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  games: () => request<Game[]>('/api/v1/admin/games'),
  createGame: (body: Partial<Game> & { name: string }) =>
    request<Game>('/api/v1/admin/games', { method: 'POST', body: JSON.stringify(body) }),
  patchGame: (id: string, body: Partial<Game>) =>
    request<Game>(`/api/v1/admin/games/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  deleteGame: (id: string) =>
    request<void>(`/api/v1/admin/games/${id}`, { method: 'DELETE' }),
  contents: () => request<Content[]>('/api/v1/admin/contents'),
  createContent: (body: Record<string, unknown>) =>
    request<Content>('/api/v1/admin/contents', { method: 'POST', body: JSON.stringify(body) }),
  patchContent: (id: string, body: Record<string, unknown>) =>
    request<Content>(`/api/v1/admin/contents/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  deleteContent: (id: string) =>
    request<void>(`/api/v1/admin/contents/${id}`, { method: 'DELETE' }),
  createContentFromUrl: (body: { url: string; game_id: string; kind: string }) =>
    request<Content>('/api/v1/admin/contents/from-url', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  resummarizeContent: (id: string) =>
    request<Content>(`/api/v1/admin/contents/${id}/summarize`, { method: 'POST' }),
  inquiries: () => request<Inquiry[]>('/api/v1/admin/inquiries'),
  closeInquiry: (id: string) =>
    request<Inquiry>(`/api/v1/admin/inquiries/${id}/close`, { method: 'POST' }),
  ingestSources: () => request<IngestSource[]>('/api/v1/admin/ingest-sources'),
  createIngestSource: (body: Record<string, unknown>) =>
    request<IngestSource>('/api/v1/admin/ingest-sources', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  patchIngestSource: (id: string, body: Record<string, unknown>) =>
    request<IngestSource>(`/api/v1/admin/ingest-sources/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  deleteIngestSource: (id: string) =>
    request<void>(`/api/v1/admin/ingest-sources/${id}`, { method: 'DELETE' }),
  runIngestSource: (id: string) =>
    request<IngestRun>(`/api/v1/admin/ingest-sources/${id}/runs`, { method: 'POST' }),
  dryRunIngestSource: (body: {
    source_type: string;
    endpoint_url: string;
    config: Record<string, string>;
    secret_env_name?: string | null;
  }) =>
    request<SourcePreview>('/api/v1/admin/ingest-sources/dry-run', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  ingestRuns: (limit = 50) =>
    request<IngestRun[]>(`/api/v1/admin/ingest-runs?limit=${limit}`),
  dispatchPush: (limit = 200) =>
    request<{ processed: number; sent: number; failed: number }>(
      `/api/v1/admin/push/dispatch?limit=${limit}`,
      { method: 'POST' },
    ),
  uploadImage: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request<{ url: string; path: string }>('/api/v1/admin/uploads', {
      method: 'POST',
      body: form,
    });
  },
  pushStats: () => request<PushStats>('/api/v1/admin/push/stats'),
  userStats: () => request<UserStats>('/api/v1/admin/stats/users'),
  auditLogs: (limit = 50) => request<AuditLog[]>(`/api/v1/admin/audit-logs?limit=${limit}`),
};
