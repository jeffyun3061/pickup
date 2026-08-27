/**
 * 이미지 에셋 인덱스 매핑.
 * - 경로 문자열을 화면에 흩지 않고 여기 키로만 접근한다.
 * - preview/* 는 Stitch Neon-Tactical 시안 AI 생성 에셋 (실서비스 IP 로고 아님).
 */
export const imageAssets = {
  mascot: require('../../assets/images/preview/mascot.jpg'),
  pikiMascot: require('../../assets/images/preview/piki_mascot.png'),
  heroRoom: require('../../assets/images/preview/hero_room.png'),
  feedShadow: require('../../assets/images/preview/feed_shadow.jpg'),
  feedNeon: require('../../assets/images/preview/feed_neon.jpg'),
  feedGrid: require('../../assets/images/preview/feed_grid.jpg'),
  feedZero: require('../../assets/images/preview/feed_zero.jpg'),
  feedCity: require('../../assets/images/preview/feed_city.jpg'),
  feedCore: require('../../assets/images/preview/feed_core.jpg'),
  coverTactical: require('../../assets/images/preview/cover_tactical.jpg'),
  coverOps: require('../../assets/images/preview/cover_ops.jpg'),
  rankVoid: require('../../assets/images/preview/rank_void.jpg'),
  rankDrift: require('../../assets/images/preview/rank_drift.jpg'),
  rankCyber: require('../../assets/images/preview/rank_cyber.jpg'),
  rankGrid: require('../../assets/images/preview/rank_grid.jpg'),
  rankSynth: require('../../assets/images/preview/rank_synth.jpg'),
  gameHonkai: require('../../assets/images/preview/games/game_honkai.png'),
  gameGenshin: require('../../assets/images/preview/games/game_genshin.png'),
  gameBlueArchive: require('../../assets/images/preview/games/game_blue_archive.png'),
  gameNikke: require('../../assets/images/preview/games/game_nikke.png'),
  gameSevenKnights: require('../../assets/images/preview/games/game_seven_knights.png'),
  gamePokemonGo: require('../../assets/images/preview/games/game_pokemon_go.png'),
  gameGirlsFrontline2: require('../../assets/images/preview/games/game_girls_frontline_2.png'),
  gameIhwan: require('../../assets/images/preview/games/game_ihwan.png'),
  gameEpicSeven: require('../../assets/images/preview/games/game_epic_seven.png'),
  gameTrickcal: require('../../assets/images/preview/games/game_trickcal.png'),
  gameArknights: require('../../assets/images/preview/games/game_arknights.png'),
  gameUmamusume: require('../../assets/images/preview/games/game_umamusume.png'),
} as const;

export type AppImageName = keyof typeof imageAssets;

/** 발표용으로 사용하는 게임별 자체 제작 커버. 공식 로고·캐릭터를 포함하지 않는다. */
export const GAME_IMAGE_KEYS: Record<string, AppImageName> = {
  g_honkai_star_rail: 'gameHonkai',
  g_genshin_impact: 'gameGenshin',
  g_blue_archive: 'gameBlueArchive',
  g_nikke: 'gameNikke',
  g_seven_knights: 'gameSevenKnights',
  g_pokemon_go: 'gamePokemonGo',
  g_girls_frontline_2: 'gameGirlsFrontline2',
  g_ihwan: 'gameIhwan',
  g_epic_seven: 'gameEpicSeven',
  g_trickcal_revive: 'gameTrickcal',
  g_arknights: 'gameArknights',
  g_umamusume: 'gameUmamusume',
};

export function resolveGameImageKey(gameId: string, fallback?: string): AppImageName | undefined {
  return GAME_IMAGE_KEYS[gameId] ?? (isAppImageName(fallback) ? fallback : undefined);
}

/** API가 보낸 폴백 이미지 키를 번들 자산 목록과 안전하게 대조한다. */
export function isAppImageName(value: unknown): value is AppImageName {
  return (
    typeof value === 'string' &&
    Object.prototype.hasOwnProperty.call(imageAssets, value)
  );
}

export function resolveImage(name?: AppImageName | null) {
  if (!name) return null;
  return imageAssets[name] ?? null;
}
