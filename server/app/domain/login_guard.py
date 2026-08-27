"""
관리자 로그인 무차별 대입 방어.

단일 인스턴스 배포 전제(ADR-009)의 프로세스 내 메모리 카운터.
수평 확장 시 Redis 등 공유 저장소로 교체한다.
"""

from __future__ import annotations

import threading
import time


class LoginGuard:
    def __init__(
        self,
        max_failures: int = 5,
        window_seconds: int = 600,
        lock_seconds: int = 600,
    ) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.lock_seconds = lock_seconds
        self._lock = threading.Lock()
        self._failures: dict[str, list[float]] = {}
        self._locked_until: dict[str, float] = {}

    def retry_after(self, key: str) -> int | None:
        """잠금 상태면 남은 초를, 아니면 None을 반환한다."""
        now = time.monotonic()
        with self._lock:
            locked_until = self._locked_until.get(key)
            if locked_until is None:
                return None
            if now >= locked_until:
                del self._locked_until[key]
                self._failures.pop(key, None)
                return None
            return max(1, int(locked_until - now))

    def record_failure(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            attempts = [
                ts for ts in self._failures.get(key, []) if now - ts < self.window_seconds
            ]
            attempts.append(now)
            self._failures[key] = attempts
            if len(attempts) >= self.max_failures:
                self._locked_until[key] = now + self.lock_seconds

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)
            self._locked_until.pop(key, None)


login_guard = LoginGuard()
