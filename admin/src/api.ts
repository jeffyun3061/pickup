const TOKEN_KEY = 'piky.admin.token';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json');
  }
  const token = getToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const res = await fetch(path, { ...init, headers });
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
}

export type Game = {
  id: string;
  name: string;
  initial: string;
  genre: string;
  color: string;
  interest_count: number;
  image_url?: string | null;
};

export type Content = {
  id: string;
  game_id: string;
  game_name: string;
  kind: string;
  title: string;
  summary_points: string[];
  official_url: string;
  status?: string;
  published_at?: string | null;
};

export type Inquiry = {
  id: string;
  email?: string | null;
  category: string;
  message: string;
  status: string;
  created_at: string;
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
  inquiries: () => request<Inquiry[]>('/api/v1/admin/inquiries'),
  closeInquiry: (id: string) =>
    request<Inquiry>(`/api/v1/admin/inquiries/${id}/close`, { method: 'POST' }),
};
