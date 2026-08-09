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
const mode = (process.env.EXPO_PUBLIC_CATALOG_MODE ?? 'preview').toLowerCase();

export type CatalogMode = 'api' | 'preview' | 'empty';

export const catalogMode: CatalogMode =
  mode === 'api' ? 'api' : mode === 'empty' ? 'empty' : 'preview';

export const catalogRepository: CatalogRepository =
  catalogMode === 'api'
    ? new ApiCatalogRepository()
    : catalogMode === 'empty'
      ? new EmptyCatalogRepository()
      : new PreviewCatalogRepository();
