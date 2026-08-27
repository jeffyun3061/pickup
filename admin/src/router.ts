import { useEffect, useState } from 'react';

export type Route = 'dashboard' | 'contents' | 'games' | 'ingest' | 'inquiries';

const DEFAULT_ROUTE: Route = 'dashboard';

function parse(hash: string): Route {
  const name = hash.replace(/^#\/?/, '');
  if (
    name === 'contents' ||
    name === 'games' ||
    name === 'ingest' ||
    name === 'inquiries' ||
    name === 'dashboard'
  ) {
    return name;
  }
  return DEFAULT_ROUTE;
}

/** URL 해시 기반 페이지 라우팅 — 새로고침·북마크·뒤로가기 유지 */
export function useHashRoute(): Route {
  const [route, setRoute] = useState<Route>(() => parse(window.location.hash));
  useEffect(() => {
    const onChange = () => setRoute(parse(window.location.hash));
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);
  return route;
}

export function navigate(route: Route) {
  window.location.hash = `/${route}`;
}
