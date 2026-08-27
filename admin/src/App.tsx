import { FormEvent, useState } from 'react';
import { api, consumeSessionExpired, getToken, setToken } from './api';
import { navigate, useHashRoute, type Route } from './router';
import { ContentsPage } from './pages/ContentsPage';
import { DashboardPage } from './pages/DashboardPage';
import { GamesPage } from './pages/GamesPage';
import { InquiriesPage } from './pages/InquiriesPage';
import { IngestSourcesPage } from './pages/IngestSourcesPage';

const NAV: { route: Route; label: string; icon: string }[] = [
  { route: 'dashboard', label: '대시보드', icon: '◆' },
  { route: 'contents', label: '소식 관리', icon: '▤' },
  { route: 'games', label: '게임 관리', icon: '▣' },
  { route: 'ingest', label: '자동 수집', icon: '↻' },
  { route: 'inquiries', label: '문의 관리', icon: '✉' },
];

export function App() {
  const [token, setTokenState] = useState<string | null>(() => getToken());
  const [error, setError] = useState(() =>
    consumeSessionExpired() ? '세션이 만료되었습니다. 다시 로그인하세요.' : '',
  );
  const route = useHashRoute();

  const authed = Boolean(token);

  const onLogin = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    const fd = new FormData(e.currentTarget);
    try {
      const res = await api.login(String(fd.get('username')), String(fd.get('password')));
      setToken(res.access_token);
      setTokenState(res.access_token);
      navigate('dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : '로그인 실패');
    }
  };

  const logout = () => {
    setToken(null);
    setTokenState(null);
  };

  if (!authed) {
    return (
      <div className="login">
        <form className="card stack" onSubmit={onLogin}>
          <div className="brand">PIKY ADMIN</div>
          <p className="muted">운영자 전용. 앱 유저 로그인과 분리되어 있습니다.</p>
          <label>
            Username
            <input name="username" defaultValue="admin" required />
          </label>
          <label>
            Password
            <input name="password" type="password" required />
          </label>
          {error ? <div className="error">{error}</div> : null}
          <button className="btn" type="submit">
            로그인
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">PIKY ADMIN</div>
        <nav className="nav">
          {NAV.map((item) => (
            <button
              key={item.route}
              type="button"
              className={`nav-item ${route === item.route ? 'active' : ''}`}
              onClick={() => navigate(item.route)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
        <button className="btn ghost logout" type="button" onClick={logout}>
          로그아웃
        </button>
      </aside>
      <main className="content">
        {route === 'dashboard' ? <DashboardPage /> : null}
        {route === 'contents' ? <ContentsPage /> : null}
        {route === 'games' ? <GamesPage /> : null}
        {route === 'ingest' ? <IngestSourcesPage /> : null}
        {route === 'inquiries' ? <InquiriesPage /> : null}
      </main>
    </div>
  );
}
