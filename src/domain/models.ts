export type ContentKind = 'update' | 'event' | 'popup' | 'goods';

export const MAX_SELECTED_GAMES = 8;

/** 기간 콘텐츠를 화면에서 구분하기 위한 운영 분류. kind는 기존 API 호환용으로 유지한다. */
export type TimeBoundType =
  | 'event'
  | 'pickup'
  | 'collab'
  | 'season'
  | 'attendance'
  | 'exchange'
  | 'popup'
  | 'goods';

/** 이미지 키는 `src/assets/images.ts` 의 AppImageName과 맞춘다 */
export type ContentItem = {
  id: string;
  gameId: string;
  gameName: string;
  kind: ContentKind;
  title: string;
  summaryPoints: string[];
  officialUrl: string;
  startsAt?: string;
  endsAt?: string;
  place?: string;
  reservationUrl?: string;
  publishedAt: string;
  /** optional: images.ts 키 (미리보기) */
  imageKey?: string;
  /** optional: API 원격 이미지 */
  imageUrl?: string;
  /** 원격 이미지가 없거나 깨졌을 때 게임 포인트 색 */
  fallbackColor?: string;
  /** API 카탈로그의 자체 제작 색상 목업 사용 여부 */
  themedFallback?: boolean;
  /** 이벤트 기간 카드에 표시할 세부 분류(없으면 kind에서 추론) */
  timeBoundType?: TimeBoundType;
  /** 운영자가 지정한 중요도. 클수록 홈 대표 소식으로 우선 노출 */
  importance?: number;
};

export type Game = {
  id: string;
  name: string;
  initial: string;
  genre: string;
  color: string;
  interestCount: number;
  /** optional: images.ts 키 (커버/타일) */
  imageKey?: string;
  imageUrl?: string;
  themedFallback?: boolean;
};

export type RankingRow = {
  gameId: string;
  gameName: string;
  interestCount: number;
  rank: number;
  initial: string;
  color: string;
  imageKey?: string;
  imageUrl?: string;
  themedFallback?: boolean;
};

export type ServiceAnnouncement = {
  id: string;
  title: string;
  body: string;
  publishedAt: string;
};

export type NotificationPreferences = {
  selectedGameNews: boolean;
  eventEnding: boolean;
  serviceNotices: boolean;
};

export type Preferences = {
  onboardingCompleted: boolean;
  gameIds: string[];
  notifications: NotificationPreferences;
};

export function kindLabel(kind: ContentKind): string {
  switch (kind) {
    case 'update':
      return '업데이트';
    case 'event':
      return '인게임 이벤트';
    case 'popup':
      return '팝업';
    case 'goods':
      return '굿즈';
  }
}

export function timeBoundTypeLabel(type: TimeBoundType): string {
  switch (type) {
    case 'pickup':
      return '픽업';
    case 'collab':
      return '콜라보';
    case 'season':
      return '시즌';
    case 'attendance':
      return '출석';
    case 'exchange':
      return '교환소';
    case 'popup':
      return '팝업';
    case 'goods':
      return '굿즈';
    default:
      return '이벤트';
  }
}

export function normalizeGameIds(ids: unknown): string[] {
  if (!Array.isArray(ids)) return [];
  return [...new Set(ids.filter((id): id is string => typeof id === 'string'))].slice(
    0,
    MAX_SELECTED_GAMES,
  );
}

/** 기간 카드에 넣을 수 있는 콘텐츠인지 판정한다. 시작·종료일이 모두 명시되어야 한다. */
export function isActiveTimeBound(
  item: Pick<ContentItem, 'kind' | 'startsAt' | 'endsAt'>,
  now: Date = new Date(),
): boolean {
  if (!item.startsAt || !item.endsAt) return false;
  const start = new Date(item.startsAt).getTime();
  const end = new Date(item.endsAt).getTime();
  const current = now.getTime();
  return Number.isFinite(start) && Number.isFinite(end) && start <= current && current <= end;
}

export function eventCountdownLabel(endsAt?: string, now: Date = new Date()): string | null {
  if (!endsAt) return null;
  const end = new Date(endsAt);
  if (Number.isNaN(end.getTime())) return null;
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const endDay = new Date(end.getFullYear(), end.getMonth(), end.getDate()).getTime();
  const days = Math.round((endDay - today) / 86_400_000);
  if (days < 0) return null;
  if (days === 0) return '오늘 종료';
  if (days === 1) return '내일 종료';
  if (days === 3) return '종료 D-3';
  return `${days}일 남음`;
}

export function isOfflineKind(kind: ContentKind): boolean {
  return kind === 'popup' || kind === 'goods';
}

export function formatKstDate(iso?: string): string {
  if (!iso) return '';
  return new Intl.DateTimeFormat('ko-KR', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Seoul',
  }).format(new Date(iso));
}

/** 이벤트 마감 D-day 라벨. 마감 14일 이내만 표시, 지났으면 '종료' */
export function dDayLabel(endsAt?: string, now: Date = new Date()): string | null {
  if (!endsAt) return null;
  const end = new Date(endsAt);
  if (Number.isNaN(end.getTime())) return null;
  const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const days = Math.round(
    (startOfDay(end).getTime() - startOfDay(now).getTime()) / 86_400_000,
  );
  if (days < 0) return '종료';
  if (days === 0) return 'D-DAY';
  if (days <= 14) return `D-${days}`;
  return null;
}

/** 토스식 상대 시간: 방금 전 / N분 전 / N시간 전 / N일 전 / 그 외 날짜 */
export function formatRelativeTime(iso?: string, now: Date = new Date()): string {
  if (!iso) return '';
  const then = new Date(iso);
  const diffMs = now.getTime() - then.getTime();
  if (Number.isNaN(diffMs)) return '';
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return '방금 전';
  if (minutes < 60) return `${minutes}분 전`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}일 전`;
  return new Intl.DateTimeFormat('ko-KR', {
    month: 'numeric',
    day: 'numeric',
    timeZone: 'Asia/Seoul',
  }).format(then);
}
