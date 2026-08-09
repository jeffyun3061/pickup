export type ContentKind = 'update' | 'event' | 'popup' | 'goods';

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
