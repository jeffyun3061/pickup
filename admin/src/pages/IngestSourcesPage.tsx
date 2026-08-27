import { FormEvent, useCallback, useEffect, useState } from 'react';
import {
  api,
  parseUtc,
  type Game,
  type IngestRun,
  type IngestSource,
  type SourcePreview,
  type SourceType,
} from '../api';

const RUN_LABEL: Record<string, string> = {
  pending: '대기',
  running: '실행 중',
  succeeded: '성공',
  failed: '실패',
};

const HEALTH_LABEL: Record<string, string> = {
  failing: '연속 실패',
  quiet: '0건 지속 — 설정 확인',
};

const API_CONFIG_KEYS = [
  'items_path',
  'id_field',
  'title_field',
  'url_field',
  'summary_field',
  'image_field',
  'published_field',
  'auth_header',
  'auth_prefix',
] as const;

const HTML_CONFIG_KEYS = [
  'list_selector',
  'title_selector',
  'url_selector',
  'date_selector',
  'summary_selector',
  'image_selector',
  'image_attr',
  'detail_selector',
  'wait_selector',
  'render_timeout_seconds',
] as const;

const SCHEDULE_CONFIG_KEYS = [
  'active_start_hour',
  'active_end_hour',
  'utc_offset_hours',
] as const;

function date(value?: string | null) {
  return value ? parseUtc(value).toLocaleString('ko-KR') : '—';
}

function readConfig(fd: FormData, type: SourceType): Record<string, string> {
  const config: Record<string, string> = { kind: String(fd.get('kind') || 'update') };
  const keys = type === 'api' ? API_CONFIG_KEYS : type === 'html' ? HTML_CONFIG_KEYS : [];
  for (const key of keys) {
    const value = String(fd.get(key) || '').trim();
    if (value) config[key] = value;
  }
  for (const key of SCHEDULE_CONFIG_KEYS) {
    const value = String(fd.get(key) || '').trim();
    if (value) config[key] = value;
  }
  if (type === 'html') {
    config.render_js = fd.get('render_js') === 'on' ? 'true' : 'false';
    config.fetch_detail = fd.get('fetch_detail') === 'on' ? 'true' : 'false';
  }
  return config;
}

/** RSS·API·HTML 크롤 소스 설정 + 테스트 수집 + collector 실행 이력 */
export function IngestSourcesPage() {
  const [games, setGames] = useState<Game[]>([]);
  const [sources, setSources] = useState<IngestSource[]>([]);
  const [runs, setRuns] = useState<IngestRun[]>([]);
  const [editing, setEditing] = useState<IngestSource | null>(null);
  const [creating, setCreating] = useState(false);
  const [sourceType, setSourceType] = useState<SourceType>('rss');
  const [preview, setPreview] = useState<SourcePreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const refresh = useCallback(async () => {
    try {
      const [g, s, r] = await Promise.all([
        api.games(),
        api.ingestSources(),
        api.ingestRuns(),
      ]);
      setGames(g);
      setSources(s);
      setRuns(r);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : '수집 설정 로드 실패');
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 10_000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const flash = (message: string) => {
    setNotice(message);
    setError('');
    window.setTimeout(() => setNotice(''), 3000);
  };

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const fd = new FormData(form);
    const type = String(fd.get('source_type')) as SourceType;
    const body = {
      name: String(fd.get('name')),
      source_type: type,
      game_id: String(fd.get('game_id')),
      endpoint_url: String(fd.get('endpoint_url')),
      interval_minutes: Number(fd.get('interval_minutes')),
      enabled: fd.get('enabled') === 'on',
      auto_publish: fd.get('auto_publish') === 'on',
      secret_env_name: String(fd.get('secret_env_name') || '').trim() || null,
      config: readConfig(fd, type),
    };
    try {
      if (editing) {
        await api.patchIngestSource(editing.id, body);
        flash('수집 소스를 수정했습니다.');
      } else {
        await api.createIngestSource(body);
        flash('수집 소스를 추가했습니다.');
        form.reset();
      }
      setEditing(null);
      setCreating(false);
      setPreview(null);
      void refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : '저장 실패');
    }
  };

  const dryRun = async (form: HTMLFormElement | null) => {
    if (!form) return;
    const fd = new FormData(form);
    const type = String(fd.get('source_type')) as SourceType;
    if (type === 'html' && fd.get('render_js') === 'on') {
      setPreview(null);
      setError('자바스크립트 렌더 소스는 저장 후 ‘지금 실행’으로 collector에서 검증하세요.');
      return;
    }
    setPreviewLoading(true);
    setPreview(null);
    try {
      const result = await api.dryRunIngestSource({
        source_type: type,
        endpoint_url: String(fd.get('endpoint_url')),
        config: readConfig(fd, type),
        secret_env_name: String(fd.get('secret_env_name') || '').trim() || null,
      });
      setPreview(result);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : '테스트 수집 실패');
    } finally {
      setPreviewLoading(false);
    }
  };

  const runNow = async (source: IngestSource) => {
    try {
      await api.runIngestSource(source.id);
      flash(`'${source.name}' 작업을 대기열에 넣었습니다.`);
      void refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : '실행 요청 실패');
    }
  };

  const toggle = async (source: IngestSource) => {
    try {
      await api.patchIngestSource(source.id, { enabled: !source.enabled });
      flash(source.enabled ? '자동 실행을 중지했습니다.' : '자동 실행을 시작했습니다.');
      void refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : '상태 변경 실패');
    }
  };

  const toggleAutoPublish = async (source: IngestSource) => {
    const next = !source.auto_publish;
    if (
      next &&
      !window.confirm(
        `'${source.name}'을(를) 자동 발행으로 전환할까요?\n요약 성공 시 검수 없이 앱에 노출되고 푸시가 발송됩니다.`,
      )
    ) {
      return;
    }
    try {
      await api.patchIngestSource(source.id, { auto_publish: next });
      flash(next ? '자동 발행을 켰습니다.' : '자동 발행을 껐습니다. 이후 수집분은 검수 대기로 남습니다.');
      void refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : '상태 변경 실패');
    }
  };

  const remove = async (source: IngestSource) => {
    if (!window.confirm(`'${source.name}'과 실행 이력을 삭제할까요?`)) return;
    try {
      await api.deleteIngestSource(source.id);
      if (editing?.id === source.id) setEditing(null);
      flash('수집 소스를 삭제했습니다.');
      void refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : '삭제 실패');
    }
  };

  const showForm = creating || editing !== null;
  const warningSources = sources.filter((source) => source.health !== 'ok');

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>자동 수집</h1>
          <p className="muted">
            새 소스는 검수 모드로 시작하고, 수집 품질 확인 후 자동 발행으로 승격하세요.
          </p>
        </div>
        <button
          className="btn"
          type="button"
          onClick={() => {
            setEditing(null);
            setSourceType('rss');
            setPreview(null);
            setCreating(true);
          }}
        >
          + 수집 소스
        </button>
      </div>

      {error ? <p className="error">{error}</p> : null}
      {notice ? <p className="notice">{notice}</p> : null}
      {warningSources.length > 0 ? (
        <div className="card health-warning">
          <strong>점검 필요한 소스</strong>
          {warningSources.map((source) => (
            <div key={source.id} className="muted">
              <span className="badge failed">{HEALTH_LABEL[source.health]}</span> {source.name}
              {source.health === 'failing'
                ? ` — ${source.consecutive_failures}회 연속 실패`
                : ` — 페이지는 바뀌는데 ${source.consecutive_empty_runs}회 연속 0건 (셀렉터 깨짐 의심)`}
            </div>
          ))}
        </div>
      ) : null}

      <div className="ingest-summary">
        <div className="card metric">
          <strong>{sources.filter((source) => source.enabled).length}</strong>
          <span className="muted">활성 소스</span>
        </div>
        <div className="card metric">
          <strong>{sources.filter((source) => source.auto_publish).length}</strong>
          <span className="muted">자동 발행 소스</span>
        </div>
        <div className="card metric">
          <strong className={warningSources.length > 0 ? 'error' : ''}>
            {warningSources.length}
          </strong>
          <span className="muted">점검 필요</span>
        </div>
      </div>

      <div className="split">
        <div>
          <div className="card list-card">
            <table>
              <thead>
                <tr>
                  <th>소스</th>
                  <th>주기·상태</th>
                  <th className="actions-col" />
                </tr>
              </thead>
              <tbody>
                {sources.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="muted">등록된 수집 소스가 없습니다.</td>
                  </tr>
                ) : null}
                {sources.map((source) => (
                  <tr key={source.id} className={editing?.id === source.id ? 'selected' : ''}>
                    <td>
                      <div className="cell-title">
                        <span className={`badge ${source.source_type}`}>{source.source_type.toUpperCase()}</span>
                        {source.name}
                        {source.config.render_js === 'true' ? <span className="badge">JS 렌더</span> : null}
                        {source.auto_publish ? <span className="badge published">자동 발행</span> : null}
                        {source.health !== 'ok' ? (
                          <span className="badge failed">{HEALTH_LABEL[source.health]}</span>
                        ) : null}
                      </div>
                      <div className="muted">{source.game_name} · {source.endpoint_url}</div>
                    </td>
                    <td>
                      <div>{source.interval_minutes}분마다 · {source.enabled ? '자동 실행' : '중지'}</div>
                      {source.config.active_start_hour && source.config.active_end_hour ? (
                        <div className="muted">
                          활성 {source.config.active_start_hour}:00–{source.config.active_end_hour}:00
                          {' '}UTC{Number(source.config.utc_offset_hours ?? 0) >= 0 ? '+' : ''}
                          {source.config.utc_offset_hours ?? '0'}
                        </div>
                      ) : null}
                      <div className="muted">
                        최근 {date(source.last_run_at)} · {source.last_status ?? '실행 전'}
                      </div>
                    </td>
                    <td className="row-actions">
                      <button className="btn sm" type="button" onClick={() => void runNow(source)}>
                        지금 실행
                      </button>
                      <button className="btn ghost sm" type="button" onClick={() => void toggleAutoPublish(source)}>
                        {source.auto_publish ? '자동 발행 끄기' : '자동 발행 켜기'}
                      </button>
                      <button className="btn ghost sm" type="button" onClick={() => void toggle(source)}>
                        {source.enabled ? '중지' : '활성화'}
                      </button>
                      <button
                        className="btn ghost sm"
                        type="button"
                        onClick={() => {
                          setCreating(false);
                          setEditing(source);
                          setSourceType(source.source_type);
                          setPreview(null);
                        }}
                      >
                        수정
                      </button>
                      <button className="btn danger sm" type="button" onClick={() => void remove(source)}>
                        삭제
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card list-card run-history">
            <div className="table-title">최근 실행 이력</div>
            <table>
              <thead>
                <tr>
                  <th>상태</th>
                  <th>소스</th>
                  <th>결과</th>
                  <th>실행 시각</th>
                </tr>
              </thead>
              <tbody>
                {runs.length === 0 ? (
                  <tr><td colSpan={4} className="muted">실행 이력이 없습니다.</td></tr>
                ) : null}
                {runs.map((run) => (
                  <tr key={run.id}>
                    <td><span className={`badge ${run.status}`}>{RUN_LABEL[run.status]}</span></td>
                    <td>{run.source_name}</td>
                    <td>
                      {run.not_modified ? (
                        <span className="muted">변화 없음 (스킵)</span>
                      ) : (
                        `${run.items_created}/${run.items_seen}건`
                      )}
                      {run.error ? <div className="error run-error">{run.error}</div> : null}
                    </td>
                    <td className="muted">{date(run.started_at ?? run.queued_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {showForm ? (
          <div>
            <form key={editing?.id ?? 'new'} className="card editor" onSubmit={onSubmit}>
              <div className="editor-head">
                <strong>{editing ? '수집 소스 수정' : '새 수집 소스'}</strong>
                <button className="btn ghost sm" type="button" onClick={() => {
                  setEditing(null);
                  setCreating(false);
                  setPreview(null);
                }}>
                  닫기
                </button>
              </div>
              <label>
                이름
                <input name="name" required defaultValue={editing?.name ?? ''} placeholder="공식 공지 게시판" />
              </label>
              <div className="row">
                <label style={{ flex: 1 }}>
                  방식
                  <select
                    name="source_type"
                    value={sourceType}
                    onChange={(event) => setSourceType(event.target.value as SourceType)}
                  >
                    <option value="rss">RSS</option>
                    <option value="api">JSON API</option>
                    <option value="html">HTML 크롤</option>
                  </select>
                </label>
                <label style={{ flex: 1 }}>
                  게임
                  <select name="game_id" required defaultValue={editing?.game_id ?? ''}>
                    <option value="" disabled>선택</option>
                    {games.map((game) => <option key={game.id} value={game.id}>{game.name}</option>)}
                  </select>
                </label>
              </div>
              <label>
                소스 URL (공지 목록)
                <input name="endpoint_url" type="url" required defaultValue={editing?.endpoint_url ?? ''} placeholder="https://example.com/notice" />
              </label>
              <div className="row">
                <label style={{ flex: 1 }}>
                  실행 주기 (분)
                  <input name="interval_minutes" type="number" min={5} max={10080} defaultValue={editing?.interval_minutes ?? 15} />
                </label>
                <label style={{ flex: 1 }}>
                  기본 종류
                  <select name="kind" defaultValue={editing?.config.kind ?? 'update'}>
                    <option value="update">업데이트</option>
                    <option value="event">이벤트</option>
                    <option value="popup">팝업</option>
                    <option value="goods">굿즈</option>
                  </select>
                </label>
              </div>
              <div className="mapping-fields">
                <strong>자동 실행 시간</strong>
                <div className="row">
                  <label style={{ flex: 1 }}>
                    시작 시
                    <input
                      name="active_start_hour"
                      type="number"
                      min={0}
                      max={23}
                      defaultValue={editing ? (editing.config.active_start_hour ?? '') : 8}
                      placeholder="비우면 제한 없음"
                    />
                  </label>
                  <label style={{ flex: 1 }}>
                    종료 시
                    <input
                      name="active_end_hour"
                      type="number"
                      min={0}
                      max={23}
                      defaultValue={editing ? (editing.config.active_end_hour ?? '') : 22}
                      placeholder="비우면 제한 없음"
                    />
                  </label>
                  <label style={{ flex: 1 }}>
                    UTC 오프셋
                    <input
                      name="utc_offset_hours"
                      type="number"
                      min={-12}
                      max={14}
                      defaultValue={editing ? (editing.config.utc_offset_hours ?? '') : 9}
                      placeholder="+9"
                    />
                  </label>
                </div>
                <p className="muted">시작·종료를 비우거나 같게 두면 24시간 실행합니다. ‘지금 실행’은 제한 없이 동작합니다.</p>
              </div>
              {sourceType === 'api' ? (
                <div className="mapping-fields">
                  <strong>JSON 필드 매핑</strong>
                  <label>목록 경로<input name="items_path" defaultValue={editing?.config.items_path ?? ''} placeholder="data.articles" /></label>
                  <div className="row">
                    <label style={{ flex: 1 }}>ID 필드<input name="id_field" defaultValue={editing?.config.id_field ?? 'id'} /></label>
                    <label style={{ flex: 1 }}>제목 필드<input name="title_field" defaultValue={editing?.config.title_field ?? 'title'} /></label>
                  </div>
                  <div className="row">
                    <label style={{ flex: 1 }}>URL 필드<input name="url_field" defaultValue={editing?.config.url_field ?? 'url'} /></label>
                    <label style={{ flex: 1 }}>요약 필드<input name="summary_field" defaultValue={editing?.config.summary_field ?? 'summary'} /></label>
                  </div>
                  <div className="row">
                    <label style={{ flex: 1 }}>이미지 필드<input name="image_field" defaultValue={editing?.config.image_field ?? ''} /></label>
                    <label style={{ flex: 1 }}>게시일 필드<input name="published_field" defaultValue={editing?.config.published_field ?? ''} /></label>
                  </div>
                  <div className="row">
                    <label style={{ flex: 1 }}>인증 헤더<input name="auth_header" defaultValue={editing?.config.auth_header ?? ''} placeholder="Authorization" /></label>
                    <label style={{ flex: 1 }}>인증 접두어<input name="auth_prefix" defaultValue={editing?.config.auth_prefix ?? ''} placeholder="Bearer" /></label>
                  </div>
                  <label>비밀 환경변수 이름<input name="secret_env_name" defaultValue={editing?.secret_env_name ?? ''} placeholder="GAME_NEWS_API_TOKEN" /></label>
                </div>
              ) : null}
              {sourceType === 'html' ? (
                <div className="mapping-fields">
                  <strong>CSS 셀렉터</strong>
                  <label>목록 아이템 (필수)<input name="list_selector" required defaultValue={editing?.config.list_selector ?? ''} placeholder="ul.board li" /></label>
                  <div className="row">
                    <label style={{ flex: 1 }}>제목<input name="title_selector" defaultValue={editing?.config.title_selector ?? ''} placeholder="비우면 링크 텍스트" /></label>
                    <label style={{ flex: 1 }}>링크<input name="url_selector" defaultValue={editing?.config.url_selector ?? ''} placeholder="a (기본)" /></label>
                  </div>
                  <div className="row">
                    <label style={{ flex: 1 }}>날짜<input name="date_selector" defaultValue={editing?.config.date_selector ?? ''} placeholder="span.date" /></label>
                    <label style={{ flex: 1 }}>요약<input name="summary_selector" defaultValue={editing?.config.summary_selector ?? ''} /></label>
                  </div>
                  <div className="row">
                    <label style={{ flex: 1 }}>이미지 셀렉터<input name="image_selector" defaultValue={editing?.config.image_selector ?? ''} placeholder="img.thumbnail" /></label>
                    <label style={{ flex: 1 }}>이미지 속성<input name="image_attr" defaultValue={editing?.config.image_attr ?? 'src'} placeholder="src" /></label>
                  </div>
                  <label>상세 본문 셀렉터<input name="detail_selector" defaultValue={editing?.config.detail_selector ?? ''} placeholder="비우면 article/main 자동" /></label>
                  <label className="check-label">
                    <input
                      name="render_js"
                      type="checkbox"
                      defaultChecked={editing?.config.render_js === 'true'}
                    />
                    자바스크립트로 목록 렌더링
                  </label>
                  <div className="row">
                    <label style={{ flex: 1 }}>
                      렌더 완료 대기 셀렉터
                      <input
                        name="wait_selector"
                        defaultValue={editing?.config.wait_selector ?? ''}
                        placeholder=".news-list li"
                      />
                    </label>
                    <label style={{ flex: 1 }}>
                      렌더 제한 시간(초)
                      <input
                        name="render_timeout_seconds"
                        type="number"
                        min={1}
                        max={60}
                        defaultValue={editing?.config.render_timeout_seconds ?? 20}
                      />
                    </label>
                  </div>
                  <label className="check-label">
                    <input
                      name="fetch_detail"
                      type="checkbox"
                      defaultChecked={editing?.config.fetch_detail !== 'false'}
                    />
                    새 글 상세 본문 수집
                  </label>
                  <p className="muted">robots.txt가 차단하면 실행이 실패로 표시됩니다. 저장 전 테스트 수집으로 확인하세요.</p>
                  <p className="muted">JS 렌더 소스는 API 서버 dry-run 대신 저장 후 ‘지금 실행’으로 collector에서 확인합니다.</p>
                </div>
              ) : null}
              <label className="check-label">
                <input name="enabled" type="checkbox" defaultChecked={editing?.enabled ?? true} />
                저장 후 자동 실행
              </label>
              <label className="check-label">
                <input name="auto_publish" type="checkbox" defaultChecked={editing?.auto_publish ?? false} />
                자동 발행 (요약 성공 시 검수 없이 발행+푸시)
              </label>
              <div className="row">
                <button
                  className="btn ghost"
                  type="button"
                  style={{ flex: 1 }}
                  disabled={previewLoading}
                  onClick={(event) => void dryRun(event.currentTarget.form)}
                >
                  {previewLoading ? '수집 중…' : '테스트 수집'}
                </button>
                <button className="btn" type="submit" style={{ flex: 1 }}>
                  {editing ? '수정 저장' : '소스 추가'}
                </button>
              </div>
              <p className="muted">비밀값 자체는 저장하지 않습니다. collector 환경변수에 별도로 설정하세요.</p>
            </form>

            {preview ? (
              <div className="card preview-card">
                <strong>테스트 수집 결과 ({preview.items.length}건)</strong>
                {preview.warning ? <p className="error">{preview.warning}</p> : null}
                {preview.items.map((item) => (
                  <div key={item.external_id} className="preview-item">
                    <div className="cell-title">{item.title}</div>
                    <div className="muted">
                      {item.published_at ? `${item.published_at} · ` : ''}
                      {item.url || 'URL 없음'}
                    </div>
                    {item.summary ? <div className="muted">{item.summary.slice(0, 120)}</div> : null}
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
