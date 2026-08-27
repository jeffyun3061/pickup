export type ContentKind = 'update' | 'event' | 'popup' | 'goods';

export type AnalysisImportance = 1 | 2 | 3;
export type AnalysisImpactLevel = 'low' | 'medium' | 'high';
export type AnalysisConfidence = 'low' | 'medium' | 'high';
export type CommunitySentiment = 'positive' | 'mixed' | 'negative' | 'unknown';

/**
 * 공지 원문을 바탕으로 서버 LLM이 만든 참고용 분석.
 * 커뮤니티 값은 근거 수집 전까지 unknown만 허용한다.
 */
export type ContentAnalysis = {
  importance: AnalysisImportance;
  impactLevel: AnalysisImpactLevel;
  impactSummary: string;
  confidence: AnalysisConfidence;
  communitySentiment: CommunitySentiment;
  communitySummary?: string;
  communitySampleCount?: number;
  generatedAt?: string;
};

export const MAX_SELECTED_GAMES = 8;

/**
 * 시안에서 사용하던 게임 ID를 새 카탈로그 ID로 한 번만 옮긴다.
 * 삭제 대신 매핑하므로 기존 설치에서 선택 게임이 갑자기 빈 목록이 되지 않는다.
 */
const LEGACY_GAME_ID_MIGRATION: Record<string, string> = {
  g_shadow: 'g_blue_archive',
  g_neon: 'g_nikke',
  g_grid: 'g_seven_knights',
  g_zero: 'g_pokemon_go',
  g_void: 'g_zenless_zone_zero',
  g_drift: 'g_girls_frontline_2',
  g_cyber: 'g_wuthering_waves',
  g_clash: 'g_ihwan',
};

// 권리 검토 전 공개 목록에서 보류한 게임은 이전 설치 데이터에서도
// 다시 선택 상태로 복원하지 않는다. 서버도 활성 카탈로그만 관계에 저장한다.
// 권리 검토 전 보류: 젠레스 존 제로·명조. `g_wuthering_waves`는
// 이전 시안에서 명조를 가리키던 ID라 기존 설치 복원도 함께 막는다.
const RETIRED_GAME_IDS = new Set([
  'g_zenless_zone_zero',
  'g_mingchao',
  'g_wuthering_waves',
]);

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
  /** 공식 원문 기반 자동 분석(없으면 분석 준비 중) */
  analysis?: ContentAnalysis;
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
      return '새 소식';
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
  const normalized = ids
    .filter((id): id is string => typeof id === 'string')
    .map((id) => LEGACY_GAME_ID_MIGRATION[id] ?? id);
  return [...new Set(normalized)]
    .filter((id) => !RETIRED_GAME_IDS.has(id))
    .slice(0, MAX_SELECTED_GAMES);
}

/**
 * 서버가 반환한 현재 활성 카탈로그와 설치에 남은 선택값을 동기화한다.
 * 네트워크 실패 시 호출하지 않아 오프라인 캐시에서 선택이 사라지지 않게 한다.
 */
export function reconcileGameIds(
  ids: unknown,
  availableGameIds: readonly string[],
): string[] {
  const available = new Set(availableGameIds);
  return normalizeGameIds(ids).filter((id) => available.has(id));
}

/** 마이픽 카드의 N 배지용 읽지 않은 소식 수를 게임별로 계산한다. */
export function countUnreadByGame(
  items: readonly Pick<ContentItem, 'id' | 'gameId'>[],
  readIds: readonly string[],
): Map<string, number> {
  const read = new Set(readIds);
  const counts = new Map<string, number>();
  for (const item of items) {
    if (read.has(item.id)) continue;
    counts.set(item.gameId, (counts.get(item.gameId) ?? 0) + 1);
  }
  return counts;
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
