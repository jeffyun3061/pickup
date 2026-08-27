import { useCallback, useEffect, useMemo, useState } from 'react';
import { api, parseUtc, type Inquiry } from '../api';

type Filter = 'all' | 'open' | 'closed';

/** 문의 관리 — 대기/완료 필터 + 처리 */
export function InquiriesPage() {
  const [inquiries, setInquiries] = useState<Inquiry[]>([]);
  const [filter, setFilter] = useState<Filter>('open');
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    try {
      setInquiries(await api.inquiries());
      setError('');
    } catch (e) {
      setError(e instanceof Error ? e.message : '문의 목록 로드 실패');
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const visible = useMemo(
    () => (filter === 'all' ? inquiries : inquiries.filter((i) => i.status === filter)),
    [inquiries, filter],
  );
  const openCount = inquiries.filter((i) => i.status === 'open').length;

  const close = async (id: string) => {
    try {
      await api.closeInquiry(id);
      void refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : '처리 실패');
    }
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>문의 관리</h1>
          <p className="muted">앱 설정 → 문의하기로 들어온 메시지입니다.</p>
        </div>
      </div>

      {error ? <p className="error">{error}</p> : null}

      <div className="chips">
        {(
          [
            ['open', `대기 ${openCount}`],
            ['closed', `처리 완료 ${inquiries.length - openCount}`],
            ['all', `전체 ${inquiries.length}`],
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
      </div>

      <div className="card list-card">
        <table>
          <thead>
            <tr>
              <th style={{ width: 90 }}>상태</th>
              <th>내용</th>
              <th className="actions-col" />
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 ? (
              <tr>
                <td colSpan={3} className="muted">
                  {filter === 'open' ? '대기 중인 문의가 없습니다.' : '문의가 없습니다.'}
                </td>
              </tr>
            ) : null}
            {visible.map((item) => (
              <tr key={item.id}>
                <td>
                  <span className={`badge ${item.status === 'open' ? 'draft' : 'published'}`}>
                    {item.status === 'open' ? '대기' : '완료'}
                  </span>
                </td>
                <td>
                  <div className="cell-title">{item.message}</div>
                  <div className="muted">
                    {item.category} · {item.email || '이메일 없음'} ·{' '}
                    {parseUtc(item.created_at).toLocaleString('ko-KR')}
                  </div>
                </td>
                <td className="row-actions">
                  {item.status === 'open' ? (
                    <button className="btn ghost sm" type="button" onClick={() => void close(item.id)}>
                      처리 완료
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
