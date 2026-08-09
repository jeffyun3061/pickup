/**
 * 이미지 에셋 인덱스 매핑.
 * - 경로 문자열을 화면에 흩지 않고 여기 키로만 접근한다.
 * - preview/* 는 Stitch Neon-Tactical 시안 AI 생성 에셋 (실서비스 IP 로고 아님).
 */
export const imageAssets = {
  mascot: require('../../assets/images/preview/mascot.jpg'),
  feedShadow: require('../../assets/images/preview/feed_shadow.jpg'),
  feedNeon: require('../../assets/images/preview/feed_neon.jpg'),
  feedGrid: require('../../assets/images/preview/feed_grid.jpg'),
  feedZero: require('../../assets/images/preview/feed_zero.jpg'),
  feedCity: require('../../assets/images/preview/feed_city.jpg'),
  feedCore: require('../../assets/images/preview/feed_core.jpg'),
  coverTactical: require('../../assets/images/preview/cover_tactical.jpg'),
  coverOps: require('../../assets/images/preview/cover_ops.jpg'),
  pickShadow: require('../../assets/images/preview/pick_shadow.jpg'),
  pickNeon: require('../../assets/images/preview/pick_neon.jpg'),
  pickGrid: require('../../assets/images/preview/pick_grid.jpg'),
  rankVoid: require('../../assets/images/preview/rank_void.jpg'),
  rankDrift: require('../../assets/images/preview/rank_drift.jpg'),
  rankCyber: require('../../assets/images/preview/rank_cyber.jpg'),
  rankGrid: require('../../assets/images/preview/rank_grid.jpg'),
  rankSynth: require('../../assets/images/preview/rank_synth.jpg'),
} as const;

export type AppImageName = keyof typeof imageAssets;

export function resolveImage(name?: AppImageName | null) {
  if (!name) return null;
  return imageAssets[name] ?? null;
}
