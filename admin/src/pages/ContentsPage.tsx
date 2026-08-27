import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import {
  api,
  parseUtc,
  type Content,
  type Game,
  type ImageRightsStatus,
} from '../api';
import { ImageUploadInput } from '../components/ImageUploadInput';

type StatusFilter = 'all' | 'draft' | 'reviewed' | 'published';

const STATUS_LABEL: Record<string, string> = {
  draft: '초안',
  reviewed: '검수 완료',
  published: '발행됨',
};

const KIND_LABEL: Record<string, string> = {
  update: '업데이트',
  event: '이벤트',
  popup: '팝업',
  goods: '굿즈',
};

const SUMMARY_LABEL: Record<string, string> = {
  pending: 'AI 요약 대기',
  done: 'AI 요약 완료',
  failed: 'AI 요약 실패',
};

const IMAGE_RIGHTS_LABEL: Record<ImageRightsStatus, string> = {
  unverified: '미확인 — 게임 대체 이미지 사용',
  official: '공식 사용 허용',
  licensed: '별도 라이선스 확보',
  original: '자체 제작',
};

function date(value?: string | null) {
  return value ? parseUtc(value).toLocaleString('ko-KR') : null;
}

function toLocalInput(value?: string | null) {
  if (!value) return '';
  const d = parseUtc(value);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** 소식 관리 — URL 빠른 등록 + 필터 + 단계 타임라인 + AI 요약 */
export function ContentsPage() {
  const [games, setGames] = useState<Game[]>([]);
  const [contents, setContents] = useState<Content[]>([]);
  const [filter, setFilter] = useState<StatusFilter>('all');
  const [gameFilter, setGameFilter] = useState('all');
  const [kindFilter, setKindFilter] = useState('all');
  const [editing, setEditing] = useState<Content | null>(null);
  const [creating, setCreating] = useState(false);
  const [quickAdd, setQuickAdd] = useState(false);
  const [quickLoading, setQuickLoading] = useState(false);
  const [resummarizing, setResummarizing] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const refresh = useCallback(async () => {
    try {
      const [g, c] = await Promise.all([api.games(), api.contents()]);
      setGames(g);
      setContents(c);
      setError('');
    } catch (e) {
      setError(e instanceof Error ? e.message : '소식 목록 로드 실패');
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 15_000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  // 대시보드 "수정 후 업로드" 딥링크 — 목록 로드 후 해당 소식의 에디터를 바로 연다
  useEffect(() => {
    const targetId = sessionStorage.getItem('piky.admin.editContentId');
    if (!targetId || contents.length === 0) return;
    const target = contents.find((c) => c.id === targetId);
    if (target) {
      setEditing(target);
      setCreating(false);
    }
    sessionStorage.removeItem('piky.admin.editContentId');
  }, [contents]);

  const flash = (msg: string) => {
    setNotice(msg);
    setError('');
    window.setTimeout(() => setNotice(''), 2500);
  };

  const visible = useMemo(
    () =>
      contents
        .filter((c) => (filter === 'all' ? true : c.status === filter))
        .filter((c) => (gameFilter === 'all' ? true : c.game_id === gameFilter))
        .filter((c) => (kindFilter === 'all' ? true : c.kind === kindFilter)),
    [contents, filter, gameFilter, kindFilter],
  );

  const counts = useMemo(() => {
    const acc: Record<string, number> = { draft: 0, reviewed: 0, published: 0 };
    for (const c of contents) acc[c.status ?? 'draft'] = (acc[c.status ?? 'draft'] ?? 0) + 1;
    return acc;
  }, [contents]);

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    const points = String(fd.get('summary') || '')
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);
    const optional = (name: string) => String(fd.get(name) || '').trim() || null;
    const optionalDate = (name: string) => {
      const value = String(fd.get(name) || '').trim();
      return value ? new Date(value).toISOString() : null;
    };
    const body = {
      game_id: String(fd.get('game_id')),
      kind: String(fd.get('kind')),
      title: String(fd.get('title')),
      summary_points: points,
      official_url: String(fd.get('official_url') || ''),
      image_url: optional('image_url'),
      image_source_url: optional('image_source_url'),
      image_rights_status: String(
        fd.get('image_rights_status') || 'unverified',
      ) as ImageRightsStatus,
      place: optional('place'),
      reservation_url: optional('reservation_url'),
      starts_at: optionalDate('starts_at'),
      ends_at: optionalDate('ends_at'),
    };
    try {
      if (editing) {
        await api.patchContent(editing.id, {
          ...body,
          scheduled_publish_at: optionalDate('scheduled_publish_at'),
        });
        flash('소식을 수정했습니다.');
      } else {
        await api.createContent({ ...body, status: 'draft' });
        flash('초안을 저장했습니다. 검수 후 발행하세요.');
        form.reset();
      }
      setEditing(null);
      setCreating(false);
      void refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : '저장 실패');
    }
  };

  const onQuickAdd = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    setQuickLoading(true);
    try {
      const created = await api.createContentFromUrl({
        url: String(fd.get('url')),
        game_id: String(fd.get('game_id')),
        kind: String(fd.get('kind') || 'update'),
      });
      flash('URL에서 초안을 만들었습니다. 요약을 확인하고 발행하세요.');
      setQuickAdd(false);
      setCreating(false);
      setEditing(created);
      void refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'URL 등록 실패');
    } finally {
      setQuickLoading(false);
    }
  };

  const setStatus = async (id: string, status: string) => {
    try {
      await api.patchContent(id, { status });
      flash(
        status === 'published'
          ? '발행했습니다. 앱에 바로 노출됩니다.'
          : status === 'reviewed'
            ? '검수 완료로 표시했습니다.'
            : '상태를 변경했습니다.',
      );
      void refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : '상태 변경 실패');
    }
  };

  const resummarize = async (item: Content) => {
    setResummarizing(true);
    try {
      const updated = await api.resummarizeContent(item.id);
      if (updated.summary_status === 'done') flash('AI 요약을 다시 만들었습니다.');
      else setError('AI 요약에 실패했습니다. OPENAI_API_KEY 설정과 원문을 확인하세요.');
      if (editing?.id === item.id) setEditing(updated);
      void refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI 요약 실패');
    } finally {
      setResummarizing(false);
    }
  };

  const onDelete = async (item: Content) => {
    if (!window.confirm(`'${item.title}' 소식을 삭제할까요?`)) return;
    try {
      await api.deleteContent(item.id);
      if (editing?.id === item.id) setEditing(null);
      flash('소식을 삭제했습니다.');
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
          <h1>소식 관리</h1>
          <p className="muted">자동 수집·URL 등록·직접 작성 모두 같은 검수 흐름을 거칩니다.</p>
        </div>
        <div className="row">
          <button
            className="btn ghost"
            type="button"
            onClick={() => {
              setEditing(null);
              setCreating(false);
              setQuickAdd(true);
            }}
          >
            URL로 등록
          </button>
          <button
            className="btn"
            type="button"
            onClick={() => {
              setEditing(null);
              setQuickAdd(false);
              setCreating(true);
            }}
          >
            + 새 소식
          </button>
        </div>
      </div>

      {error ? <p className="error">{error}</p> : null}
      {notice ? <p className="notice">{notice}</p> : null}

      {quickAdd ? (
        <form className="card editor quick-add" onSubmit={onQuickAdd}>
          <div className="editor-head">
            <strong>URL로 빠른 등록</strong>
            <button className="btn ghost sm" type="button" onClick={() => setQuickAdd(false)}>닫기</button>
          </div>
          <p className="muted">공지 URL을 붙여넣으면 제목·본문을 가져와 AI 요약까지 채운 초안을 만듭니다.</p>
          <label>
            공지 URL
            <input name="url" type="url" required placeholder="https://example.com/news/123" />
          </label>
          <div className="row">
            <label style={{ flex: 1 }}>
              게임
              <select name="game_id" required defaultValue="">
                <option value="" disabled>선택</option>
                {games.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
              </select>
            </label>
            <label style={{ width: 140 }}>
              종류
              <select name="kind" defaultValue="update">
                <option value="update">업데이트</option>
                <option value="event">이벤트</option>
                <option value="popup">팝업</option>
                <option value="goods">굿즈</option>
              </select>
            </label>
          </div>
          <button className="btn" type="submit" disabled={quickLoading}>
            {quickLoading ? '가져오는 중…' : '초안 만들기'}
          </button>
        </form>
      ) : null}

      <div className="chips">
        {(
          [
            ['all', `전체 ${contents.length}`],
            ['draft', `초안 ${counts.draft ?? 0}`],
            ['reviewed', `검수 ${counts.reviewed ?? 0}`],
            ['published', `발행 ${counts.published ?? 0}`],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={`chip ${filter === id ? 'active' : ''}`}
            onClick={() => setFilter(id)}
          >
            {label}
          </button>
        ))}
        <select className="chip-select" value={gameFilter} onChange={(e) => setGameFilter(e.target.value)}>
          <option value="all">모든 게임</option>
          {games.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
        </select>
        <select className="chip-select" value={kindFilter} onChange={(e) => setKindFilter(e.target.value)}>
          <option value="all">모든 종류</option>
          {Object.entries(KIND_LABEL).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
        </select>
      </div>

      <div className="split">
        <div className="card list-card">
          <table>
            <thead>
              <tr>
                <th style={{ width: 90 }}>상태</th>
                <th>소식</th>
                <th className="actions-col" />
              </tr>
            </thead>
            <tbody>
              {visible.length === 0 ? (
                <tr>
                  <td colSpan={3} className="muted">
                    {filter === 'all' ? '소식이 없습니다. 첫 소식을 작성하세요.' : '해당 조건의 소식이 없습니다.'}
                  </td>
                </tr>
              ) : null}
              {visible.map((item) => (
                <tr key={item.id} className={editing?.id === item.id ? 'selected' : ''}>
                  <td>
                    <span className={`badge ${item.status ?? 'draft'}`}>
                      {STATUS_LABEL[item.status ?? 'draft'] ?? item.status}
                    </span>
                    {item.summary_status && item.summary_status !== 'none' ? (
                      <div style={{ marginTop: 4 }}>
                        <span className={`badge summary-${item.summary_status}`}>
                          {SUMMARY_LABEL[item.summary_status]}
                        </span>
                      </div>
                    ) : null}
                  </td>
                  <td>
                    <div className="cell-title">
                      {item.title}
                      {item.source_id || item.idempotency_key ? (
                        <span className="badge api">자동 수집</span>
                      ) : null}
                      {item.scheduled_publish_at && item.status !== 'published' ? (
                        <span className="badge reviewed">예약 {date(item.scheduled_publish_at)}</span>
                      ) : null}
                      {item.link_broken ? <span className="badge failed">데드링크</span> : null}
                    </div>
                    <div className="muted">
                      {item.game_name} · {KIND_LABEL[item.kind] ?? item.kind}
                      {item.origin_published_at ? ` · 원문 ${date(item.origin_published_at)}` : ''}
                      {item.published_at ? ` · 발행 ${date(item.published_at)}` : ''}
                    </div>
                    {item.summary_points.length > 0 ? (
                      <div className="muted summary-preview">{item.summary_points[0]}</div>
                    ) : null}
                    {item.official_url ? (
                      <a href={item.official_url} target="_blank" rel="noreferrer" className="source-link">
                        원문 확인
                      </a>
                    ) : null}
                  </td>
                  <td className="row-actions">
                    {item.status === 'draft' ? (
                      <button className="btn ghost sm" type="button" onClick={() => void setStatus(item.id, 'reviewed')}>
                        검수 완료
                      </button>
                    ) : null}
                    {item.status === 'reviewed' ? (
                      <>
                        <button className="btn sm" type="button" onClick={() => void setStatus(item.id, 'published')}>
                          발행
                        </button>
                        <button className="btn ghost sm" type="button" onClick={() => void setStatus(item.id, 'draft')}>
                          반려
                        </button>
                      </>
                    ) : null}
                    {item.status === 'published' ? (
                      <button className="btn ghost sm" type="button" onClick={() => void setStatus(item.id, 'reviewed')}>
                        발행 회수
                      </button>
                    ) : null}
                    <button
                      className="btn ghost sm"
                      type="button"
                      onClick={() => {
                        setCreating(false);
                        setQuickAdd(false);
                        setEditing(item);
                      }}
                    >
                      수정
                    </button>
                    <button className="btn danger sm" type="button" onClick={() => void onDelete(item)}>
                      삭제
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {showForm ? (
          <div>
            <form key={editing?.id ?? 'new'} className="card editor" onSubmit={onSubmit}>
              <div className="editor-head">
                <strong>{editing ? '소식 수정' : '새 소식 (초안)'}</strong>
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
              <div className="row">
                <label style={{ flex: 1 }}>
                  게임
                  <select name="game_id" required defaultValue={editing?.game_id ?? ''}>
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
                <label style={{ width: 140 }}>
                  종류
                  <select name="kind" defaultValue={editing?.kind ?? 'update'}>
                    <option value="update">업데이트</option>
                    <option value="event">이벤트</option>
                    <option value="popup">팝업</option>
                    <option value="goods">굿즈</option>
                  </select>
                </label>
              </div>
              <label>
                제목
                <input name="title" required defaultValue={editing?.title ?? ''} />
              </label>
              <label>
                요약 (줄바꿈 = 포인트)
                <textarea name="summary" rows={4} defaultValue={editing?.summary_points.join('\n') ?? ''} />
              </label>
              {editing ? (
                <button
                  className="btn ghost sm"
                  type="button"
                  disabled={resummarizing}
                  onClick={() => void resummarize(editing)}
                >
                  {resummarizing ? '요약 중…' : 'AI 요약 다시 만들기'}
                </button>
              ) : null}
              <label>
                공식 URL
                <input name="official_url" defaultValue={editing?.official_url ?? ''} placeholder="https://" />
              </label>
              <label>
                이미지 (URL 또는 파일 업로드)
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
                  placeholder="공식 뉴스·미디어킷·라이선스 페이지"
                />
              </label>
              <label>
                이미지 사용 권한
                <select name="image_rights_status" defaultValue={editing?.image_rights_status ?? 'unverified'}>
                  {Object.entries(IMAGE_RIGHTS_LABEL).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </label>
              <p className="muted">
                미확인 이미지는 발행해도 앱에서 숨기고, 게임 관리에서 지정한 자체 제작 테마 이미지로 대체합니다.
              </p>
              <div className="row">
                <label style={{ flex: 1 }}>
                  시작
                  <input name="starts_at" type="datetime-local" defaultValue={toLocalInput(editing?.starts_at)} />
                </label>
                <label style={{ flex: 1 }}>
                  종료
                  <input name="ends_at" type="datetime-local" defaultValue={toLocalInput(editing?.ends_at)} />
                </label>
              </div>
              <label>
                장소 (팝업·오프라인)
                <input name="place" defaultValue={editing?.place ?? ''} />
              </label>
              <label>
                예약 URL
                <input name="reservation_url" defaultValue={editing?.reservation_url ?? ''} placeholder="https://" />
              </label>
              {editing ? (
                <label>
                  예약 발행 시각 (검수 완료 상태에서 시각 도달 시 자동 발행)
                  <input
                    name="scheduled_publish_at"
                    type="datetime-local"
                    defaultValue={toLocalInput(editing?.scheduled_publish_at)}
                  />
                </label>
              ) : null}
              {editing?.needs_review_reason ? (
                <p className="error">
                  자동 발행 보류 사유: {editing.needs_review_reason}
                </p>
              ) : null}
              <button className="btn" type="submit">
                {editing ? '수정 저장' : '초안 저장'}
              </button>
              {editing ? (
                <p className="muted">상태 변경(검수·발행)은 목록의 버튼으로만 가능합니다.</p>
              ) : null}
            </form>

            {editing ? (
              <div className="card timeline-card">
                <strong>진행 단계</strong>
                <ol className="timeline">
                  <li className="done">
                    <span>감지·수집</span>
                    <span className="muted">
                      {date(editing.created_at) ?? '—'}
                      {editing.origin_published_at ? ` (원문 게시 ${date(editing.origin_published_at)})` : ''}
                    </span>
                  </li>
                  <li className={editing.summary_status === 'done' ? 'done' : editing.summary_status === 'failed' ? 'failed' : ''}>
                    <span>AI 요약 카드</span>
                    <span className="muted">
                      {editing.summary_status === 'done'
                        ? date(editing.summarized_at)
                        : editing.summary_status === 'failed'
                          ? '실패 — 수동 요약 또는 재실행'
                          : editing.summary_status === 'pending'
                            ? '대기 중'
                            : '규칙 기반 요약 사용'}
                    </span>
                  </li>
                  <li className={editing.status === 'published' ? 'done' : ''}>
                    <span>발행·푸시</span>
                    <span className="muted">
                      {editing.status === 'published' ? date(editing.published_at) : '대기'}
                    </span>
                  </li>
                </ol>
                {editing.raw_text_excerpt ? (
                  <details>
                    <summary className="muted">수집된 원문 미리보기</summary>
                    <p className="raw-text muted">{editing.raw_text_excerpt}</p>
                  </details>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
