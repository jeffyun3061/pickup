import { FormEvent, useCallback, useEffect, useState } from 'react';
import { api, type Game, type ImageRightsStatus } from '../api';
import { ImageUploadInput } from '../components/ImageUploadInput';

const RIGHTS_LABEL: Record<ImageRightsStatus, string> = {
  unverified: '미확인 — 앱에서 원본 숨김',
  official: '공식 사용 허용',
  licensed: '별도 라이선스 확보',
  original: '자체 제작',
};

const FALLBACK_IMAGES = [
  ['coverTactical', '전술 테마'],
  ['coverOps', '작전 테마'],
  ['feedNeon', '네온 테마'],
  ['feedCity', '도시 테마'],
  ['feedGrid', '그리드 테마'],
  ['feedCore', '코어 테마'],
] as const;

/** 게임 관리 — 목록 + 우측(모바일은 상단) 편집 패널 */
export function GamesPage() {
  const [games, setGames] = useState<Game[]>([]);
  const [editing, setEditing] = useState<Game | null>(null);
  const [creating, setCreating] = useState(false);
  const [previewColor, setPreviewColor] = useState('#2A2A2B');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const refresh = useCallback(async () => {
    try {
      setGames(await api.games());
      setError('');
    } catch (e) {
      setError(e instanceof Error ? e.message : '게임 목록 로드 실패');
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const flash = (msg: string) => {
    setNotice(msg);
    setError('');
    window.setTimeout(() => setNotice(''), 2500);
  };

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    const body = {
      name: String(fd.get('name')),
      genre: String(fd.get('genre') || ''),
      initial: String(fd.get('initial') || ''),
      color: String(fd.get('color') || '#2A2A2B'),
      image_url: String(fd.get('image_url') || '') || null,
      image_source_url: String(fd.get('image_source_url') || '') || null,
      image_rights_status: String(
        fd.get('image_rights_status') || 'unverified',
      ) as ImageRightsStatus,
      fallback_image_key: String(fd.get('fallback_image_key') || 'coverTactical'),
    };
    try {
      if (editing) {
        await api.patchGame(editing.id, body);
        flash('게임 정보를 수정했습니다.');
      } else {
        await api.createGame(body);
        flash('게임을 등록했습니다.');
        form.reset();
      }
      setEditing(null);
      setCreating(false);
      void refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : '저장 실패');
    }
  };

  const onDelete = async (g: Game) => {
    if (!window.confirm(`'${g.name}' 게임을 삭제할까요?\n소식이 남아 있으면 삭제되지 않습니다.`)) return;
    try {
      await api.deleteGame(g.id);
      if (editing?.id === g.id) setEditing(null);
      flash('게임을 삭제했습니다.');
      void refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : '삭제 실패');
    }
  };

  const showForm = creating || editing !== null;

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>게임 관리</h1>
          <p className="muted">카탈로그에 노출되는 게임을 추가·수정·삭제합니다.</p>
        </div>
        <button
          className="btn"
          type="button"
          onClick={() => {
            setEditing(null);
            setCreating(true);
            setPreviewColor('#2A2A2B');
          }}
        >
          + 새 게임
        </button>
      </div>

      {error ? <p className="error">{error}</p> : null}
      {notice ? <p className="notice">{notice}</p> : null}

      <div className="split">
        <div className="card list-card">
          <table>
            <thead>
              <tr>
                <th>게임</th>
                <th>장르</th>
                <th>등록 수</th>
                <th className="actions-col" />
              </tr>
            </thead>
            <tbody>
              {games.length === 0 ? (
                <tr>
                  <td colSpan={4} className="muted">
                    등록된 게임이 없습니다. 오른쪽에서 첫 게임을 추가하세요.
                  </td>
                </tr>
              ) : null}
              {games.map((g) => (
                <tr key={g.id} className={editing?.id === g.id ? 'selected' : ''}>
                  <td>
                    <div className="cell-title">
                      <span className="swatch" style={{ background: g.color }}>
                        {g.initial || g.name.charAt(0)}
                      </span>
                      {g.name}
                    </div>
                    <div className="muted mono">{g.id}</div>
                    <div className="muted">
                      이미지: {RIGHTS_LABEL[g.image_rights_status ?? 'unverified']}
                    </div>
                  </td>
                  <td>{g.genre || '—'}</td>
                  <td>{g.interest_count.toLocaleString()}</td>
                  <td className="row-actions">
                    <button
                      className="btn ghost sm"
                      type="button"
                      onClick={() => {
                        setCreating(false);
                        setEditing(g);
                        setPreviewColor(g.color || '#2A2A2B');
                      }}
                    >
                      수정
                    </button>
                    <button className="btn danger sm" type="button" onClick={() => void onDelete(g)}>
                      삭제
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {showForm ? (
          <form key={editing?.id ?? 'new'} className="card editor" onSubmit={onSubmit}>
            <div className="editor-head">
              <strong>{editing ? '게임 수정' : '게임 등록'}</strong>
              <button
                className="btn ghost sm"
                type="button"
                onClick={() => {
                  setEditing(null);
                  setCreating(false);
                }}
              >
                닫기
              </button>
            </div>
            <label>
              이름
              <input name="name" required defaultValue={editing?.name ?? ''} placeholder="프로젝트: 섀도우" />
            </label>
            <div className="row">
              <label style={{ flex: 1 }}>
                장르
                <input name="genre" defaultValue={editing?.genre ?? ''} placeholder="전술 RPG" />
              </label>
              <label style={{ width: 90 }}>
                이니셜
                <input name="initial" maxLength={8} defaultValue={editing?.initial ?? ''} placeholder="섀" />
              </label>
            </div>
            <div className="row">
              <label style={{ width: 130 }}>
                포인트 색
                <input
                  name="color"
                  defaultValue={editing?.color ?? '#2A2A2B'}
                  placeholder="#2A2A2B"
                  onChange={(event) => setPreviewColor(event.target.value || '#2A2A2B')}
                />
              </label>
              <div style={{ flex: 1 }} className="muted">
                등록 수는 앱에서 실제로 선택한 활성 설치를 자동 집계합니다.
              </div>
            </div>
            <div
              aria-label="자동 생성 대체 이미지 미리보기"
              style={{
                height: 116,
                borderRadius: 12,
                border: '1px solid var(--outline, #3d3d40)',
                background: [
                  `radial-gradient(circle at 24% 30%, ${previewColor} 0, transparent 38%)`,
                  `radial-gradient(circle at 78% 68%, ${previewColor} 0, transparent 42%)`,
                  'linear-gradient(135deg, #111216, #272932)',
                ].join(','),
                filter: 'saturate(1.15)',
                boxShadow: `inset 0 0 36px ${previewColor}55`,
              }}
            >
              <span
                style={{
                  display: 'inline-block',
                  margin: 12,
                  padding: '5px 8px',
                  borderRadius: 6,
                  background: 'rgba(10,10,12,.62)',
                  color: '#fff',
                  fontSize: 12,
                }}
              >
                자동 생성 블러 목업
              </span>
            </div>
            <label>
              커버 이미지 (URL 또는 파일 업로드)
              <ImageUploadInput
                name="image_url"
                defaultValue={editing?.image_url}
                onError={setError}
              />
            </label>
            <label>
              이미지 출처·허가 근거 URL
              <input
                name="image_source_url"
                type="url"
                defaultValue={editing?.image_source_url ?? ''}
                placeholder="공식 미디어킷·보도자료·라이선스 페이지"
              />
            </label>
            <div className="row">
              <label style={{ flex: 1 }}>
                사용 권한
                <select name="image_rights_status" defaultValue={editing?.image_rights_status ?? 'unverified'}>
                  {Object.entries(RIGHTS_LABEL).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </label>
              <label style={{ flex: 1 }}>
                권한 미확인·로딩 실패 시 대체 이미지
                <select name="fallback_image_key" defaultValue={editing?.fallback_image_key ?? 'coverTactical'}>
                  {FALLBACK_IMAGES.map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </label>
            </div>
            <p className="muted">
              미확인 이미지는 앱에 표시하지 않고 선택한 자체 제작 테마 이미지로 대체합니다.
            </p>
            <button className="btn" type="submit">
              {editing ? '수정 저장' : '게임 추가'}
            </button>
          </form>
        ) : null}
      </div>
    </div>
  );
}
