import AsyncStorage from '@react-native-async-storage/async-storage/lib/commonjs/index.js';
import { useSyncExternalStore } from 'react';

/**
 * AsyncStorage 기반 id 집합 스토어 (북마크·읽음 표시).
 * 화면 간 즉시 동기화를 위해 모듈 싱글턴 + useSyncExternalStore 패턴을 쓴다.
 */
export class IdSetStore {
  private ids: string[] = [];
  private lookup = new Set<string>();
  private loadStarted = false;
  private listeners = new Set<() => void>();

  constructor(
    private readonly storageKey: string,
    private readonly cap: number,
  ) {}

  private notify(): void {
    this.ids = [...this.lookup];
    for (const listener of this.listeners) listener();
  }

  private persist(): void {
    AsyncStorage.setItem(this.storageKey, JSON.stringify(this.ids)).catch(() => {});
  }

  private trimToCap(): void {
    // 오래된 항목부터 정리 (Set 삽입 순서 활용)
    while (this.lookup.size > this.cap) {
      const oldest = this.lookup.values().next().value;
      if (oldest === undefined) break;
      this.lookup.delete(oldest);
    }
  }

  private ensureLoaded(): void {
    if (this.loadStarted) return;
    this.loadStarted = true;
    AsyncStorage.getItem(this.storageKey)
      .then((raw) => {
        if (!raw) return;
        const parsed = JSON.parse(raw) as unknown;
        if (!Array.isArray(parsed)) return;
        for (const id of parsed) {
          if (typeof id === 'string') this.lookup.add(id);
        }
        this.notify();
      })
      .catch(() => {});
  }

  subscribe = (listener: () => void): (() => void) => {
    this.ensureLoaded();
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getSnapshot = (): string[] => this.ids;

  has(id: string): boolean {
    return this.lookup.has(id);
  }

  add(id: string): void {
    if (this.lookup.has(id)) return;
    this.lookup.add(id);
    this.trimToCap();
    this.notify();
    this.persist();
  }

  toggle(id: string): void {
    if (this.lookup.has(id)) this.lookup.delete(id);
    else {
      this.lookup.add(id);
      this.trimToCap();
    }
    this.notify();
    this.persist();
  }

  clear(): void {
    this.lookup.clear();
    this.notify();
    this.persist();
  }
}

export const bookmarkStore = new IdSetStore('gamepickup.bookmarks.v1', 200);
export const readStore = new IdSetStore('gamepickup.read.v1', 500);

export function useIdSet(store: IdSetStore): string[] {
  return useSyncExternalStore(store.subscribe, store.getSnapshot, store.getSnapshot);
}
