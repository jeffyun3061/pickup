import { ApiCatalogRepository } from '@/src/data/ApiCatalogRepository';
import { EmptyCatalogRepository } from '@/src/data/EmptyCatalogRepository';
import { PreviewCatalogRepository } from '@/src/data/PreviewCatalogRepository';
import type { CatalogRepository } from '@/src/data/types';

/**
 * 활성 CatalogRepository 단일 진입점.
 * - api: 실서비스 FastAPI
 * - preview: Stitch 시안 퀄리티
 * - empty: EmptyState 검증
 */
// 개발 중에는 시안을 바로 확인할 수 있지만, release 빌드가 환경변수
// 누락으로 가짜 데이터로 나가는 일은 막는다. 운영은 명시적으로 api를 쓴다.
const developmentDefault = typeof __DEV__ !== 'undefined' && __DEV__ ? 'preview' : 'api';
const mode = (process.env.EXPO_PUBLIC_CATALOG_MODE ?? developmentDefault).trim().toLowerCase();

export type CatalogMode = 'api' | 'preview' | 'empty';

const supportedModes: CatalogMode[] = ['api', 'preview', 'empty'];
if (!supportedModes.includes(mode as CatalogMode)) {
  throw new Error(
    `알 수 없는 카탈로그 모드입니다: ${mode || '(빈 값)'}. ` +
      'EXPO_PUBLIC_CATALOG_MODE는 api, preview, empty 중 하나여야 합니다.',
  );
}

export const catalogMode = mode as CatalogMode;

export const catalogRepository: CatalogRepository =
  catalogMode === 'api'
    ? new ApiCatalogRepository()
    : catalogMode === 'empty'
      ? new EmptyCatalogRepository()
      : new PreviewCatalogRepository();
