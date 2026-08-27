import { useEffect, useState } from 'react';
import type { ImageSourcePropType } from 'react-native';

import {
  resolveGameImageKey,
  resolveImage,
  type AppImageName,
} from '@/src/assets/images';

/** 승인된 원격 이미지가 깨지면 번들된 자체 제작 테마 이미지로 전환한다. */
export function useCatalogImage(
  imageUrl?: string,
  imageKey?: string,
  gameId?: string,
): {
  source: ImageSourcePropType | null;
  isFallback: boolean;
  isGeneratedGameArt: boolean;
  onError: () => void;
} {
  const [remoteFailed, setRemoteFailed] = useState(false);

  useEffect(() => {
    setRemoteFailed(false);
  }, [imageUrl]);

  const resolvedKey = resolveGameImageKey(gameId ?? '', imageKey);
  const fallback = resolveImage(resolvedKey as AppImageName | undefined);
  const isGeneratedGameArt = Boolean(gameId && resolvedKey && resolvedKey !== imageKey);
  const source = isGeneratedGameArt
    ? fallback
    : imageUrl && !remoteFailed
      ? { uri: imageUrl }
      : fallback;

  return {
    source,
    isFallback: !imageUrl || remoteFailed || isGeneratedGameArt,
    isGeneratedGameArt,
    onError: () => setRemoteFailed(true),
  };
}
