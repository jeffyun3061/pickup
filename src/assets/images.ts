/**
 * 이미지 에셋 인덱스 매핑.
 * - 경로 문자열을 화면에 흩지 않고 여기 키로만 접근한다.
 * - preview/* 는 Stitch Neon-Tactical 시안 AI 생성 에셋 (실서비스 IP 로고 아님).
 */
export const imageAssets = {
  mascot: require('../../assets/images/preview/mascot.jpg'),
  takiMascot: require('../../assets/images/preview/taki_mascot.png'),
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
} as const;

export type AppImageName = keyof typeof imageAssets;

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
