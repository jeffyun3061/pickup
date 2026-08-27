import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  api,
  parseUtc,
  type AuditLog,
  type Content,
  type IngestSource,
  type PushStats,
  type UserStats,
} from '../api';
import { navigate } from '../router';

type Stats = {
  games: number;
  draft: number;
  reviewed: number;
  published: number;
  openInquiries: number;
  activeSources: number;
  autoPublishSources: number;
  failedRuns: number;
  summaryFailed: number;
};

const KIND_LABEL: Record<string, string> = {
  update: '업데이트',
  event: '이벤트',
  popup: '팝업',
  goods: '굿즈',
};

function date(value?: string | null) {
  return value ? parseUtc(value).toLocaleString('ko-KR', { dateStyle: 'short', timeStyle: 'short' }) : '';
}

function timeAgo(value?: string | null) {
  if (!value) return '';
  const diff = Date.now() - parseUtc(value).getTime();
  const min = Math.floor(diff / 60_000);
  if (min < 1) return '방금 전';
  if (min < 60) return `${min}분 전`;
  const hours = Math.floor(min / 60);
  if (hours < 24) return `${hours}시간 전`;
  return `${Math.floor(hours / 24)}일 전`;
}

/** 대시보드 — 검수 큐·최근 발행·수집 제어까지 한 화면에서 처리하는 운영 센터 */
export function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [contents, setContents] = useState<Content[]>([]);
  const [sources, setSources] = useState<IngestSource[]>([]);
  const [pushStats, setPushStats] = useState<PushStats | null>(null);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [intervalDraft, setIntervalDraft] = useState<Record<string, string>>({});

  const refresh = useCallback(async () => {
    try {
      const [games, contentList, inquiries, sourceList, runs, push, users, logs] =
        await Promise.all([
          api.games(),
          api.contents(),
          api.inquiries(),
          api.ingestSources(),
          api.ingestRuns(20),
          api.pushStats(),
          api.userStats(),
          api.auditLogs(20),
        ]);
      setStats({
        games: games.length,
        draft: contentList.filter((c) => c.status === 'draft').length,
        reviewed: contentList.filter((c) => c.status === 'reviewed').length,
        published: contentList.filter((c) => c.status === 'published').length,
        openInquiries: inquiries.filter((i) => i.status === 'open').length,
        activeSources: sourceList.filter((source) => source.enabled).length,
        autoPublishSources: sourceList.filter((source) => source.auto_publish).length,
        failedRuns: runs.filter((run) => run.status === 'failed').length,
        summaryFailed: contentList.filter((c) => c.summary_status === 'failed').length,
      });
      setContents(contentList);
      setSources(sourceList);
      setPushStats(push);
      setUserStats(users);
      setAuditLogs(logs);
      setUpdatedAt(new Date());
      setError('');
    } catch (e) {
      setError(e instanceof Error ? e.message : '요약 로드 실패');
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 20_000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const flash = (msg: string) => {
    setNotice(msg);
    setError('');
    window.setTimeout(() => setNotice(''), 2500);
  };

  const warnSources = useMemo(() => sources.filter((s) => s.health !== 'ok'), [sources]);
  const promoteSources = useMemo(() => sources.filter((s) => s.promote_suggested), [sources]);
  const brokenLinks = useMemo(
    () => contents.filter((c) => c.link_broken && c.status === 'published'),
    [contents],
  );

  const dispatchNow = () =>
    act('push-dispatch', async () => {
      const result = await api.dispatchPush(200);
      flash(`푸시 발송 완료 — 성공 ${result.sent}건 · 실패 ${result.failed}건`);
    }, '');

  const queue = useMemo(
    () =>
      contents
        .filter((c) => c.status === 'draft' || c.status === 'reviewed')
        .sort((a, b) => (b.created_at ?? '').localeCompare(a.created_at ?? ''))
        .slice(0, 8),
    [contents],
  );

  const recentPublished = useMemo(
    () =>
      contents
        .filter((c) => c.status === 'published')
        .sort((a, b) => (b.published_at ?? '').localeCompare(a.published_at ?? ''))
        .slice(0, 6),
    [contents],
  );

  const act = async (id: string, fn: () => Promise<unknown>, done: string) => {
    setBusyId(id);
    try {
      await fn();
      flash(done);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : '작업 실패');
    } finally {
      setBusyId(null);
    }
  };

  const approve = (item: Content) =>
    act(
      item.id,
      () => api.patchContent(item.id, { status: item.status === 'draft' ? 'reviewed' : 'published' }),
      item.status === 'draft' ? '검수 완료로 넘겼습니다.' : '발행했습니다. 앱과 푸시에 반영됩니다.',
    );

  const unpublish = (item: Content) =>
    act(item.id, () => api.patchContent(item.id, { status: 'reviewed' }), '발행을 회수했습니다.');

  const resummarize = (item: Content) =>
    act(item.id, () => api.resummarizeContent(item.id), 'AI 요약을 다시 실행했습니다.');

  const openEditor = (item: Content) => {
    sessionStorage.setItem('piky.admin.editContentId', item.id);
    navigate('contents');
  };

  const saveInterval = (source: IngestSource) => {
    const raw = intervalDraft[source.id];
    const minutes = Number(raw);
    if (!raw || !Number.isFinite(minutes) || minutes < 1) {
      setError('수집 주기는 1분 이상이어야 합니다.');
      return;
    }
    void act(
      source.id,
      () => api.patchIngestSource(source.id, { interval_minutes: Math.round(minutes) }),
      `수집 주기를 ${Math.round(minutes)}분으로 변경했습니다.`,
    );
  };

  const runNow = (source: IngestSource) =>
    act(source.id, () => api.runIngestSource(source.id), '수집을 대기열에 넣었습니다. 잠시 후 결과가 반영됩니다.');

  const toggleEnabled = (source: IngestSource) =>
    act(
      source.id,
      () => api.patchIngestSource(source.id, { enabled: !source.enabled }),
      source.enabled ? '소스를 일시중지했습니다.' : '소스를 다시 켰습니다.',
    );

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>대시보드</h1>
          <p className="muted">수집 → AI 요약 → 검수 → 발행까지 이 화면에서 처리하세요.</p>
        </div>
        <div className="head-tools">
          {updatedAt ? (
            <span className="muted">{updatedAt.toLocaleTimeString('ko-KR')} 기준 · 20초마다 자동 갱신</span>
          ) : null}
          <button className="btn ghost sm" type="button" onClick={() => void refresh()}>
            새로고침
          </button>
        </div>
      </div>

      {error ? <p className="error">{error}</p> : null}
      {notice ? <p className="notice">{notice}</p> : null}

      {warnSources.length > 0 || brokenLinks.length > 0 || promoteSources.length > 0 ? (
        <div className="card health-warning">
          <strong>운영 알림</strong>
          {warnSources.map((source) => (
            <div key={source.id} className="muted">
              <span className="badge failed">
                {source.health === 'failing' ? '연속 실패' : '0건 지속'}
              </span>{' '}
              {source.name} —{' '}
              {source.health === 'failing'
                ? `${source.consecutive_failures}회 연속 실패`
                : `페이지는 바뀌는데 ${source.consecutive_empty_runs}회 연속 0건 (셀렉터 깨짐 의심)`}
              <button className="btn ghost sm" type="button" onClick={() => navigate('ingest')} style={{ marginLeft: 8 }}>
                확인
              </button>
            </div>
          ))}
          {brokenLinks.map((item) => (
            <div key={item.id} className="muted">
              <span className="badge failed">데드링크</span> {item.title} — 원문 링크가 404/410으로
              확인됐습니다. 링크를 고치거나 발행을 회수하세요.
              <button className="btn ghost sm" type="button" onClick={() => openEditor(item)} style={{ marginLeft: 8 }}>
                수정
              </button>
            </div>
          ))}
          {promoteSources.map((source) => (
            <div key={source.id} className="muted">
              <span className="badge published">승격 제안</span> {source.name} — 무수정 발행{' '}
              {source.stat_approved}건 연속. 자동 발행으로 승격을 검토하세요.
              <button
                className="btn ghost sm"
                type="button"
                disabled={busyId === source.id}
                style={{ marginLeft: 8 }}
                onClick={() =>
                  void act(
                    source.id,
                    () => api.patchIngestSource(source.id, { auto_publish: true }),
                    `${source.name}을(를) 자동 발행으로 승격했습니다.`,
                  )
                }
              >
                자동 발행 켜기
              </button>
            </div>
          ))}
        </div>
      ) : null}

      <div className="stat-grid">
        <button className="stat" type="button" onClick={() => navigate('contents')}>
          <span className="stat-value warn">{stats?.draft ?? '—'}</span>
          <span className="stat-label">검수 대기 초안</span>
        </button>
        <button className="stat" type="button" onClick={() => navigate('contents')}>
          <span className="stat-value accent">{stats?.reviewed ?? '—'}</span>
          <span className="stat-label">발행 대기</span>
        </button>
        <button className="stat" type="button" onClick={() => navigate('inquiries')}>
          <span className="stat-value warn">{stats?.openInquiries ?? '—'}</span>
          <span className="stat-label">미처리 문의</span>
        </button>
        <button className="stat" type="button" onClick={() => navigate('ingest')}>
          <span className="stat-value warn">{stats?.failedRuns ?? '—'}</span>
          <span className="stat-label">최근 수집 실패</span>
        </button>
        <button className="stat" type="button" onClick={() => navigate('contents')}>
          <span className="stat-value warn">{stats?.summaryFailed ?? '—'}</span>
          <span className="stat-label">AI 요약 실패</span>
        </button>
        <button className="stat" type="button" onClick={() => navigate('contents')}>
          <span className="stat-value">{stats?.published ?? '—'}</span>
          <span className="stat-label">발행 중 소식</span>
        </button>
        <button className="stat" type="button" onClick={() => navigate('games')}>
          <span className="stat-value">{stats?.games ?? '—'}</span>
          <span className="stat-label">등록 게임</span>
        </button>
        <button className="stat" type="button" onClick={() => navigate('ingest')}>
          <span className="stat-value accent">{stats?.activeSources ?? '—'}</span>
          <span className="stat-label">활성 수집 소스</span>
        </button>
      </div>

      <div className="widget-grid">
        <div className="card widget">
          <div className="widget-head">
            <strong>푸시 발송 현황</strong>
            <button
              className="btn sm"
              type="button"
              disabled={busyId === 'push-dispatch' || (pushStats?.pending ?? 0) === 0}
              onClick={() => void dispatchNow()}
            >
              대기분 지금 발송
            </button>
          </div>
          <div className="widget-metrics">
            <div>
              <span className="stat-value warn">{pushStats?.pending ?? '—'}</span>
              <span className="stat-label">대기</span>
            </div>
            <div>
              <span className="stat-value accent">{pushStats?.sent ?? '—'}</span>
              <span className="stat-label">발송됨</span>
            </div>
            <div>
              <span className="stat-value warn">{pushStats?.failed ?? '—'}</span>
              <span className="stat-label">실패</span>
            </div>
          </div>
          <p className="muted">
            {pushStats?.last_sent_at
              ? `마지막 발송 ${timeAgo(pushStats.last_sent_at)}`
              : '아직 발송 이력이 없습니다.'}
            {' · '}발행 시 자동 enqueue, 심야(23~08시)분은 아침 8시에 발송됩니다.
          </p>
        </div>

        <div className="card widget">
          <div className="widget-head">
            <strong>유저 현황</strong>
          </div>
          <div className="widget-metrics">
            <div>
              <span className="stat-value">{userStats?.installations ?? '—'}</span>
              <span className="stat-label">설치</span>
            </div>
            <div>
              <span className="stat-value accent">{userStats?.with_device_token ?? '—'}</span>
              <span className="stat-label">푸시 가능</span>
            </div>
            <div>
              <span className="stat-value">{userStats?.notify_selected_game_news ?? '—'}</span>
              <span className="stat-label">새소식 알림 ON</span>
            </div>
          </div>
          {userStats && userStats.top_games.length > 0 ? (
            <p className="muted">
              인기 마이픽:{' '}
              {userStats.top_games
                .map((g) => `${g.game_name} ${g.pick_count}명`)
                .join(' · ')}
            </p>
          ) : (
            <p className="muted">아직 마이픽 데이터가 없습니다.</p>
          )}
        </div>
      </div>

      <div className="section-head">
        <div className="section-title">검수 대기 큐</div>
        <button className="btn ghost sm" type="button" onClick={() => navigate('contents')}>
          전체 보기
        </button>
      </div>
      <div className="card list-card">
        {queue.length === 0 ? (
          <p className="muted empty-line">검수할 소식이 없습니다. 수집되거나 작성된 초안이 여기에 표시됩니다.</p>
        ) : (
          queue.map((item) => (
            <div key={item.id} className="queue-item">
              <div className="queue-main">
                <div className="cell-title">
                  <span className={`badge ${item.status ?? 'draft'}`}>
                    {item.status === 'reviewed' ? '발행 대기' : '초안'}
                  </span>
                  {item.source_id ? <span className="badge api">자동 수집</span> : null}
                  {item.scheduled_publish_at ? (
                    <span className="badge reviewed">예약 {date(item.scheduled_publish_at)}</span>
                  ) : null}
                  <span>{item.title}</span>
                </div>
                {item.needs_review_reason ? (
                  <p className="error summary-note">
                    자동 발행 보류 — {item.needs_review_reason}. 확인 후 직접 발행하세요.
                  </p>
                ) : null}
                <div className="muted">
                  {item.game_name} · {KIND_LABEL[item.kind] ?? item.kind} · {timeAgo(item.created_at)}
                  {item.official_url ? (
                    <>
                      {' · '}
                      <a href={item.official_url} target="_blank" rel="noreferrer">
                        원문 링크
                      </a>
                    </>
                  ) : null}
                </div>
                {item.summary_points.length > 0 ? (
                  <ul className="summary-points">
                    {item.summary_points.map((point, i) => (
                      <li key={i}>{point}</li>
                    ))}
                  </ul>
                ) : item.summary_status === 'pending' ? (
                  <p className="muted summary-note">AI 요약 생성 중…</p>
                ) : item.summary_status === 'failed' ? (
                  <p className="error summary-note">AI 요약 실패 — 다시 실행하거나 직접 수정하세요.</p>
                ) : (
                  <p className="muted summary-note">요약 없음 — 수정에서 직접 입력할 수 있습니다.</p>
                )}
              </div>
              <div className="queue-actions">
                <button
                  className="btn sm"
                  type="button"
                  disabled={busyId === item.id}
                  onClick={() => void approve(item)}
                >
                  {item.status === 'draft' ? '승인 (검수 완료)' : '발행'}
                </button>
                <button className="btn ghost sm" type="button" onClick={() => openEditor(item)}>
                  수정 후 업로드
                </button>
                {item.summary_status === 'failed' ? (
                  <button
                    className="btn ghost sm"
                    type="button"
                    disabled={busyId === item.id}
                    onClick={() => void resummarize(item)}
                  >
                    요약 재실행
                  </button>
                ) : null}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="section-head">
        <div className="section-title">최근 업로드 (발행됨)</div>
        <button className="btn ghost sm" type="button" onClick={() => navigate('contents')}>
          전체 보기
        </button>
      </div>
      <div className="card list-card">
        {recentPublished.length === 0 ? (
          <p className="muted empty-line">아직 발행된 소식이 없습니다.</p>
        ) : (
          recentPublished.map((item) => (
            <div key={item.id} className="list-row">
              <div className="list-row-main">
                <div className="cell-title">
                  <span className="badge published">발행됨</span>
                  {item.auto_published ? <span className="badge api">자동 발행</span> : null}
                  {item.link_broken ? <span className="badge failed">데드링크</span> : null}
                  <span>{item.title}</span>
                </div>
                <div className="muted">
                  {item.game_name} · {KIND_LABEL[item.kind] ?? item.kind} · 발행 {date(item.published_at)}
                  {item.official_url ? (
                    <>
                      {' · '}
                      <a href={item.official_url} target="_blank" rel="noreferrer">
                        원문 링크
                      </a>
                    </>
                  ) : null}
                </div>
              </div>
              <div className="queue-actions">
                <button className="btn ghost sm" type="button" onClick={() => openEditor(item)}>
                  수정
                </button>
                <button
                  className="btn danger sm"
                  type="button"
                  disabled={busyId === item.id}
                  onClick={() => void unpublish(item)}
                >
                  발행 회수
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="section-head">
        <div className="section-title">수집 소스 제어</div>
        <button className="btn ghost sm" type="button" onClick={() => navigate('ingest')}>
          소스 관리
        </button>
      </div>
      <div className="card list-card">
        {sources.length === 0 ? (
          <p className="muted empty-line">
            수집 소스가 없습니다. 자동 수집 메뉴에서 RSS·API·HTML 소스를 등록하세요.
          </p>
        ) : (
          sources.map((source) => (
            <div key={source.id} className="list-row">
              <div className="list-row-main">
                <div className="cell-title">
                  <span className={`badge ${source.source_type}`}>{source.source_type.toUpperCase()}</span>
                  {!source.enabled ? <span className="badge draft">중지됨</span> : null}
                  {source.auto_publish ? <span className="badge published">자동 발행</span> : null}
                  <span>{source.name}</span>
                </div>
                <div className="muted">
                  {source.game_name} · 최근 실행 {source.last_run_at ? timeAgo(source.last_run_at) : '없음'}
                  {source.last_status ? ` (${source.last_status === 'succeeded' ? '성공' : '실패'})` : ''}
                  {source.next_run_at && source.enabled ? ` · 다음 실행 ${date(source.next_run_at)}` : ''}
                </div>
              </div>
              <div className="queue-actions">
                <label className="interval-control">
                  주기
                  <input
                    type="number"
                    min={1}
                    value={intervalDraft[source.id] ?? String(source.interval_minutes)}
                    onChange={(e) =>
                      setIntervalDraft((prev) => ({ ...prev, [source.id]: e.target.value }))
                    }
                  />
                  분
                </label>
                {intervalDraft[source.id] !== undefined &&
                intervalDraft[source.id] !== String(source.interval_minutes) ? (
                  <button
                    className="btn sm"
                    type="button"
                    disabled={busyId === source.id}
                    onClick={() => saveInterval(source)}
                  >
                    주기 저장
                  </button>
                ) : null}
                <button
                  className="btn ghost sm"
                  type="button"
                  disabled={busyId === source.id || !source.enabled}
                  onClick={() => void runNow(source)}
                >
                  지금 실행
                </button>
                <button
                  className="btn ghost sm"
                  type="button"
                  disabled={busyId === source.id}
                  onClick={() => void toggleEnabled(source)}
                >
                  {source.enabled ? '일시중지' : '재개'}
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="section-head">
        <div className="section-title">최근 작업 이력</div>
      </div>
      <div className="card list-card">
        {auditLogs.length === 0 ? (
          <p className="muted empty-line">아직 기록된 작업이 없습니다.</p>
        ) : (
          auditLogs.map((log) => (
            <div key={log.id} className="list-row">
              <div className="list-row-main">
                <div className="cell-title">
                  <span className={`badge ${log.actor === 'admin' ? 'reviewed' : 'api'}`}>
                    {log.actor === 'admin'
                      ? '관리자'
                      : log.actor === 'auto'
                        ? '자동'
                        : log.actor === 'scheduler'
                          ? '예약'
                          : '시스템'}
                  </span>
                  <span>{log.action}</span>
                </div>
                <div className="muted">
                  {log.detail || log.entity_id} · {timeAgo(log.created_at)}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="card">
        <strong>발행 규칙</strong>
        <p className="muted">
          기본 흐름은 초안 → 검수 완료 → 발행입니다. 자동 발행으로 설정한 신뢰 소스는 AI 요약이
          품질 게이트를 통과할 때만 서버가 이 전이를 대행하며, 자동 발행 소식을 회수하면 해당
          소스는 검수 모드로 강등됩니다. 잘못 나간 소식은 발행 회수로 즉시 내릴 수 있습니다.
        </p>
      </div>
    </div>
  );
}
