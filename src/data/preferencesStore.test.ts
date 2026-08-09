import { describe, expect, it } from 'vitest';

import {
  defaultPreferences,
  parsePreferences,
  serializePreferences,
} from '@/src/data/preferencesStore';

describe('preferencesStore serialization', () => {
  it('round-trips valid preferences', () => {
    const input = {
      ...defaultPreferences,
      onboardingCompleted: true,
      gameIds: ['g1', 'g2'],
      notifications: {
        selectedGameNews: false,
        eventEnding: true,
        serviceNotices: false,
      },
    };
    expect(parsePreferences(serializePreferences(input))).toEqual(input);
  });

  it('falls back safely on corrupt json', () => {
    expect(parsePreferences('{broken')).toEqual(defaultPreferences);
    expect(parsePreferences(null)).toEqual(defaultPreferences);
  });

  it('ignores non-string game ids', () => {
    const raw = JSON.stringify({
      onboardingCompleted: true,
      gameIds: ['ok', 1, null, 'also'],
    });
    expect(parsePreferences(raw).gameIds).toEqual(['ok', 'also']);
  });
});
