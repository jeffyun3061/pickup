import type {
  ContentItem,
  Game,
  RankingRow,
  ServiceAnnouncement,
} from '@/src/domain/models';

/**
 * 화면 검증용 미리보기 카탈로그.
 *
 * 게임 이름은 사용자가 선택할 실제 서비스 후보를 반영하되, 아래 소식·이미지는
 * 공식 발행물이 아닌 UI 검증용 샘플이다. 실제 출시 전에는 각 게임의 공식 RSS/API와
 * 사용 허가를 확인한 이미지로 API 카탈로그를 교체한다.
 */
export const PREVIEW_GAMES: Game[] = [
  {
    id: 'g_honkai_star_rail',
    name: '붕괴: 스타레일',
    initial: '붕',
    genre: '턴제 RPG',
    color: '#4B4A80',
    interestCount: 11800,
    imageKey: 'rankCyber',
  },
  {
    id: 'g_genshin_impact',
    name: '원신',
    initial: '원',
    genre: '오픈월드 액션',
    color: '#3E6B86',
    interestCount: 10900,
    imageKey: 'feedNeon',
  },
  {
    id: 'g_blue_archive',
    name: '블루 아카이브',
    initial: '블',
    genre: '학원 RPG',
    color: '#2563A6',
    interestCount: 12850,
    imageKey: 'rankVoid',
  },
  {
    id: 'g_nikke',
    name: '니케',
    initial: '니',
    genre: '건슈팅 RPG',
    color: '#6B294D',
    interestCount: 9420,
    imageKey: 'coverTactical',
  },
  {
    id: 'g_seven_knights',
    name: '세븐나이츠',
    initial: '세',
    genre: '수집형 RPG',
    color: '#6A3D28',
    interestCount: 8100,
    imageKey: 'rankDrift',
  },
  {
    id: 'g_pokemon_go',
    name: '포켓몬 GO',
    initial: '포',
    genre: 'AR 액션',
    color: '#2F5E9A',
    interestCount: 7540,
    imageKey: 'feedZero',
  },
  {
    id: 'g_girls_frontline_2',
    name: '소녀전선 2',
    initial: '소',
    genre: '전략 RPG',
    color: '#374B68',
    interestCount: 6100,
    imageKey: 'rankDrift',
  },
  {
    id: 'g_ihwan',
    name: '이환',
    initial: '이',
    genre: '액션 RPG',
    color: '#433B62',
    interestCount: 4980,
    imageKey: 'rankGrid',
  },
  {
    id: 'g_epic_seven',
    name: '에픽세븐',
    initial: '에',
    genre: '수집형 RPG',
    color: '#5D3A6E',
    interestCount: 4620,
    imageKey: 'rankSynth',
  },
  {
    id: 'g_trickcal_revive',
    name: '트릭컬 리바이브',
    initial: '트',
    genre: '볼따구 RPG',
    color: '#6B4D38',
    interestCount: 4200,
    imageKey: 'feedShadow',
  },
  {
    id: 'g_arknights',
    name: '명일방주',
    initial: '명',
    genre: '전략 RPG',
    color: '#3B454B',
    interestCount: 3980,
    imageKey: 'feedGrid',
  },
  {
    id: 'g_umamusume',
    name: '우마무스메',
    initial: '우',
    genre: '육성 시뮬레이션',
    color: '#7A3F58',
    interestCount: 3650,
    imageKey: 'feedCore',
  },
];

const now = Date.now();
const hoursAgo = (h: number) => new Date(now - h * 3600_000).toISOString();

const PREVIEW_CONTENT_SEED: ContentItem[] = [
  {
    id: 'c1',
    gameId: 'g_shadow',
    gameName: '프로젝트: 섀도우',
    kind: 'update',
    title: 'v2.4 패치 노트: 신규 전술 작전',
    summaryPoints: [
      '신규 전술 작전 섹터 개방',
      '보스 템플 난이도 조정',
      '장비 드롭률 밸런스 패치',
    ],
    officialUrl: 'https://example.com/preview/shadow-patch',
    publishedAt: hoursAgo(0.15),
    imageKey: 'coverTactical',
    importance: 3,
    analysis: {
      importance: 3,
      impactLevel: 'high',
      impactSummary: '새 작전과 보상 변경이 플레이 순서에 영향을 줄 수 있어요.',
      confidence: 'medium',
      communitySentiment: 'unknown',
      communitySummary: '반응은 조금 더 지켜볼게요.',
      communitySampleCount: 0,
    },
  },
  {
    id: 'c2',
    gameId: 'g_neon',
    gameName: '네온 신디케이트',
    kind: 'update',
    title: '북미 지역 서버 안정성 개선',
    summaryPoints: [
      '핫픽스: 매치메이킹 지연 완화',
      '북미 게이트웨이 라우팅 최적화',
    ],
    officialUrl: 'https://example.com/preview/neon-hotfix',
    publishedAt: hoursAgo(2),
    imageKey: 'coverOps',
    analysis: {
      importance: 2,
      impactLevel: 'medium',
      impactSummary: '매치메이킹 지연을 겪던 유저에게 도움이 될 수 있어요.',
      confidence: 'medium',
      communitySentiment: 'unknown',
      communitySummary: '반응은 조금 더 지켜볼게요.',
      communitySampleCount: 0,
    },
  },
  {
    id: 'c3',
    gameId: 'g_grid',
    gameName: '그리드_러너',
    kind: 'event',
    title: "시즌 4 '사이버-스톰'이 시작되었습니다",
    summaryPoints: [
      '시즌 패스 보상 라인업 공개',
      '신규 트랙: 네온 하이웨이',
      '주간 챌린지 리셋 일정 안내',
    ],
    officialUrl: 'https://example.com/preview/grid-s4',
    publishedAt: hoursAgo(5),
    startsAt: hoursAgo(5),
    endsAt: new Date(now + 14 * 86400_000).toISOString(),
    imageKey: 'feedCity',
    timeBoundType: 'season',
  },
  {
    id: 'c4',
    gameId: 'g_zero',
    gameName: '오퍼레이션: 제로',
    kind: 'update',
    title: "신규 전술 장비 'EMP 수류탄' 추가 안내",
    summaryPoints: [
      'EMP 수류탄 크래프트 레시피 추가',
      '전자기 교란 지속시간 밸런스',
    ],
    officialUrl: 'https://example.com/preview/zero-emp',
    publishedAt: hoursAgo(8),
    imageKey: 'feedZero',
  },
  {
    id: 'c5',
    gameId: 'g_drift',
    gameName: 'NEON DRIFT',
    kind: 'update',
    title: '도시 구역 텍스처 로딩 최적화 패치',
    summaryPoints: ['저사양 모드 텍스처 스트리밍 개선', '프레임 드랍 구간 수정'],
    officialUrl: 'https://example.com/preview/drift-opt',
    publishedAt: hoursAgo(12),
    imageKey: 'feedCity',
  },
  {
    id: 'c6',
    gameId: 'g_void',
    gameName: 'VOID RUNNER',
    kind: 'event',
    title: '보안 프로토콜 강화 및 보상 시스템 개편',
    summaryPoints: [
      '신규 보안 레이드 개방',
      '주간 보상 테이블 개편',
      '데이터 코어 교환소 리셋',
    ],
    officialUrl: 'https://example.com/preview/void-core',
    publishedAt: hoursAgo(18),
    startsAt: hoursAgo(18),
    endsAt: new Date(now + 7 * 86400_000).toISOString(),
    imageKey: 'feedCore',
    timeBoundType: 'exchange',
  },
  {
    id: 'c7',
    gameId: 'g_cyber',
    gameName: 'CYBER OPS',
    kind: 'popup',
    title: '서울 팝업 스토어 — 전술 키트 체험존',
    summaryPoints: ['성수 한정 굿즈 선공개', '현장 예약 필수', '주말 연장 운영'],
    officialUrl: 'https://example.com/preview/cyber-popup',
    publishedAt: hoursAgo(26),
    place: '서울 성수',
    startsAt: new Date(now + 2 * 86400_000).toISOString(),
    endsAt: new Date(now + 9 * 86400_000).toISOString(),
    reservationUrl: 'https://example.com/preview/cyber-rsvp',
    imageKey: 'coverOps',
    timeBoundType: 'collab',
  },
  {
    id: 'c8',
    gameId: 'g_shadow',
    gameName: '프로젝트: 섀도우',
    kind: 'goods',
    title: '한정 전술 재킷 프리오더 오픈',
    summaryPoints: ['시안 컬러웨이 2종', '48시간 얼리버드 특전'],
    officialUrl: 'https://example.com/preview/shadow-goods',
    publishedAt: hoursAgo(30),
    imageKey: 'coverTactical',
  },
  {
    id: 'c9',
    gameId: 'g_shadow',
    gameName: '프로젝트: 섀도우',
    kind: 'update',
    title: '신규 작전 보상 및 주간 미션 안내',
    summaryPoints: ['주간 미션 보상 상향', '작전 초기화 일정 변경'],
    officialUrl: 'https://example.com/preview/shadow-missions',
    publishedAt: hoursAgo(1.1),
    imageKey: 'feedShadow',
    importance: 2,
  },
  {
    id: 'c10',
    gameId: 'g_shadow',
    gameName: '프로젝트: 섀도우',
    kind: 'update',
    title: '개발자 코멘트: 다음 밸런스 조정 예고',
    summaryPoints: ['정찰병 스킬 사용감 개선'],
    officialUrl: 'https://example.com/preview/shadow-devnote',
    publishedAt: hoursAgo(2.4),
    imageKey: 'coverTactical',
    importance: 1,
  },
];

/**
 * 샘플 소식의 게임 연결은 카탈로그 순서로 재배치한다.
 * 픽션 ID가 남아 선택한 실제 후보 게임에서 빈 화면이 되지 않도록 하는
 * 미리보기 전용 변환이며, 실서비스에서는 API의 실제 game_id를 사용한다.
 */
export const PREVIEW_CONTENT: ContentItem[] = PREVIEW_CONTENT_SEED.map((item, index) => {
  const game = PREVIEW_GAMES[index % PREVIEW_GAMES.length];
  return {
    ...item,
    gameId: game.id,
    gameName: game.name,
  };
});

/** 미리보기에서도 운영 랭킹과 동일하게 관심 등록 수를 기준으로 정렬한다. */
export const PREVIEW_RANKINGS: RankingRow[] = [...PREVIEW_GAMES]
  .sort(
    (a, b) =>
      b.interestCount - a.interestCount
      || a.name.localeCompare(b.name, 'ko')
      || a.id.localeCompare(b.id),
  )
  .map((game, index) => ({
    gameId: game.id,
    gameName: game.name,
    interestCount: game.interestCount,
    rank: index + 1,
    initial: game.initial,
    color: game.color,
    imageKey: game.imageKey,
  }));

// 개발용 카탈로그가 운영 안내처럼 보이지 않도록 공지는 비워 둔다.
// 실제 운영 공지는 API에서 관리자가 발행한 항목만 노출한다.
export const PREVIEW_ANNOUNCEMENTS: ServiceAnnouncement[] = [];
