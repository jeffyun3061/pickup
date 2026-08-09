import { FormEvent, useCallback, useEffect, useState } from 'react';
import { api, getToken, setToken, type Content, type Game, type Inquiry } from './api';

type Tab = 'games' | 'contents' | 'inquiries';

export function App() {
  const [token, setTokenState] = useState<string | null>(() => getToken());
  const [tab, setTab] = useState<Tab>('contents');
  const [error, setError] = useState('');
  const [games, setGames] = useState<Game[]>([]);
  const [contents, setContents] = useState<Content[]>([]);
  const [inquiries, setInquiries] = useState<Inquiry[]>([]);

  const authed = Boolean(token);

  const refresh = useCallback(async () => {
    if (!getToken()) return;
    setError('');
    try {
      const [g, c, i] = await Promise.all([api.games(), api.contents(), api.inquiries()]);
      setGames(g);
      setContents(c);
      setInquiries(i);
    } catch (e) {
      setError(e instanceof Error ? e.message : '로드 실패');
    }
  }, []);

  useEffect(() => {
    if (authed) void refresh();
  }, [authed, refresh]);

  const onLogin = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    const fd = new FormData(e.currentTarget);
    try {
      const res = await api.login(String(fd.get('username')), String(fd.get('password')));
      setToken(res.access_token);
      setTokenState(res.access_token);
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
    <div className="app">
      <header className="top">
        <div className="brand">PIKY ADMIN</div>
        <div className="row">
          <button className="btn ghost" type="button" onClick={() => void refresh()}>
            새로고침
          </button>
          <button className="btn ghost" type="button" onClick={logout}>
            로그아웃
          </button>
        </div>
      </header>
      <div className="tabs">
        {(
          [
            ['contents', '소식'],
            ['games', '게임'],
            ['inquiries', '문의'],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={`tab ${tab === id ? 'active' : ''}`}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>
      <main className="main">
        {error ? <p className="error">{error}</p> : null}
        {tab === 'games' ? (
          <GamesPanel
            games={games}
            onChanged={() => void refresh()}
            onError={setError}
          />
        ) : null}
        {tab === 'contents' ? (
          <ContentsPanel
            games={games}
            contents={contents}
            onChanged={() => void refresh()}
            onError={setError}
          />
        ) : null}
        {tab === 'inquiries' ? (
          <InquiriesPanel
            inquiries={inquiries}
            onChanged={() => void refresh()}
            onError={setError}
          />
        ) : null}
      </main>
    </div>
  );
}

function GamesPanel({
  games,
  onChanged,
  onError,
}: {
  games: Game[];
  onChanged: () => void;
  onError: (msg: string) => void;
}) {
  const onCreate = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.createGame({
        name: String(fd.get('name')),
        genre: String(fd.get('genre') || ''),
        interest_count: Number(fd.get('interest_count') || 0),
      });
      e.currentTarget.reset();
      onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : '게임 생성 실패');
    }
  };

  return (
    <div className="stack">
      <form className="card stack" onSubmit={onCreate}>
        <strong>게임 등록</strong>
        <div className="row">
          <label style={{ flex: 2 }}>
            이름
            <input name="name" required placeholder="프로젝트: 섀도우" />
          </label>
          <label style={{ flex: 1 }}>
            장르
            <input name="genre" placeholder="전술 RPG" />
          </label>
          <label style={{ width: 120 }}>
            관심수
            <input name="interest_count" type="number" defaultValue={0} />
          </label>
        </div>
        <button className="btn" type="submit">
          추가
        </button>
      </form>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>이름</th>
              <th>장르</th>
              <th>관심</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {games.map((g) => (
              <tr key={g.id}>
                <td>
                  {g.name}
                  <div className="muted">{g.id}</div>
                </td>
                <td>{g.genre}</td>
                <td>{g.interest_count}</td>
                <td>
                  <button
                    className="btn danger"
                    type="button"
                    onClick={() =>
                      void api
                        .deleteGame(g.id)
                        .then(onChanged)
                        .catch((err) => onError(String(err.message ?? err)))
                    }
                  >
                    삭제
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ContentsPanel({
  games,
  contents,
  onChanged,
  onError,
}: {
  games: Game[];
  contents: Content[];
  onChanged: () => void;
  onError: (msg: string) => void;
}) {
  const onCreate = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const points = String(fd.get('summary') || '')
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);
    try {
      await api.createContent({
        game_id: String(fd.get('game_id')),
        kind: String(fd.get('kind')),
        title: String(fd.get('title')),
        summary_points: points,
        official_url: String(fd.get('official_url') || ''),
        status: 'draft',
      });
      e.currentTarget.reset();
      onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : '소식 생성 실패');
    }
  };

  const setStatus = async (id: string, status: string) => {
    try {
      await api.patchContent(id, { status });
      onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : '상태 변경 실패');
    }
  };

  return (
    <div className="stack">
      <form className="card stack" onSubmit={onCreate}>
        <strong>소식 작성 (초안)</strong>
        <p className="muted">발행은 draft → reviewed → published 순서만 허용됩니다.</p>
        <div className="row">
          <label style={{ flex: 1 }}>
            게임
            <select name="game_id" required defaultValue="">
              <option value="" disabled>
                선택
              </option>
              {games.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
          </label>
          <label style={{ width: 160 }}>
            종류
            <select name="kind" defaultValue="update">
              <option value="update">update</option>
              <option value="event">event</option>
              <option value="popup">popup</option>
              <option value="goods">goods</option>
            </select>
          </label>
        </div>
        <label>
          제목
          <input name="title" required />
        </label>
        <label>
          요약 (줄바꿈 = 포인트)
          <textarea name="summary" rows={3} />
        </label>
        <label>
          공식 URL
          <input name="official_url" placeholder="https://" />
        </label>
        <button className="btn" type="submit">
          초안 저장
        </button>
      </form>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>상태</th>
              <th>소식</th>
              <th>액션</th>
            </tr>
          </thead>
          <tbody>
            {contents.map((item) => (
              <tr key={item.id}>
                <td>
                  <span className={`badge ${item.status ?? 'draft'}`}>{item.status}</span>
                </td>
                <td>
                  <div>{item.title}</div>
                  <div className="muted">
                    {item.game_name} · {item.kind}
                  </div>
                </td>
                <td className="row">
                  {item.status === 'draft' ? (
                    <button className="btn ghost" type="button" onClick={() => void setStatus(item.id, 'reviewed')}>
                      검수
                    </button>
                  ) : null}
                  {item.status === 'reviewed' ? (
                    <>
                      <button className="btn" type="button" onClick={() => void setStatus(item.id, 'published')}>
                        발행
                      </button>
                      <button className="btn ghost" type="button" onClick={() => void setStatus(item.id, 'draft')}>
                        반려
                      </button>
                    </>
                  ) : null}
                  {item.status === 'published' ? (
                    <button className="btn ghost" type="button" onClick={() => void setStatus(item.id, 'reviewed')}>
                      발행 회수
                    </button>
                  ) : null}
                  <button
                    className="btn danger"
                    type="button"
                    onClick={() =>
                      void api
                        .deleteContent(item.id)
                        .then(onChanged)
                        .catch((err) => onError(String(err.message ?? err)))
                    }
                  >
                    삭제
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function InquiriesPanel({
  inquiries,
  onChanged,
  onError,
}: {
  inquiries: Inquiry[];
  onChanged: () => void;
  onError: (msg: string) => void;
}) {
  return (
    <div className="card">
      <strong>문의함</strong>
      <p className="muted">앱 설정의 문의하기에서 들어온 메시지입니다.</p>
      <table>
        <thead>
          <tr>
            <th>상태</th>
            <th>내용</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {inquiries.map((item) => (
            <tr key={item.id}>
              <td>{item.status}</td>
              <td>
                <div>{item.message}</div>
                <div className="muted">
                  {item.category} · {item.email || '이메일 없음'} · {new Date(item.created_at).toLocaleString('ko-KR')}
                </div>
              </td>
              <td>
                {item.status === 'open' ? (
                  <button
                    className="btn ghost"
                    type="button"
                    onClick={() =>
                      void api
                        .closeInquiry(item.id)
                        .then(onChanged)
                        .catch((err) => onError(String(err.message ?? err)))
                    }
                  >
                    처리 완료
                  </button>
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
