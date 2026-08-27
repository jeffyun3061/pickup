import { useEffect, useState } from 'react';
import type { ImageSourcePropType } from 'react-native';

import { isAppImageName, resolveImage, type AppImageName } from '@/src/assets/images';

/** 승인된 원격 이미지가 깨지면 번들된 자체 제작 테마 이미지로 전환한다. */
export function useCatalogImage(
  imageUrl?: string,
  imageKey?: string,
): {
  source: ImageSourcePropType | null;
  isFallback: boolean;
  onError: () => void;
} {
  const [remoteFailed, setRemoteFailed] = useState(false);

  useEffect(() => {
    setRemoteFailed(false);
  }, [imageUrl]);

  const fallback = resolveImage(
    isAppImageName(imageKey) ? (imageKey as AppImageName) : undefined,
  );
  const source = imageUrl && !remoteFailed ? { uri: imageUrl } : fallback;

  return {
    source,
    isFallback: !imageUrl || remoteFailed,
    onError: () => setRemoteFailed(true),
  };
}
