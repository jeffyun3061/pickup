"""
Content 발행 상태 머신.

허용 전이만 정의한다. Service/Repository는 이 모듈을 통해서만 status를 바꾼다.
면접 포인트: 잘못된 발행을 인프라가 아니라 도메인 규칙으로 막는다.
"""

from __future__ import annotations


class InvalidTransitionError(ValueError):
    """허용되지 않은 상태 전이."""


# 현재 상태 → 허용 다음 상태 집합
_ALLOWED: dict[str, frozenset[str]] = {
    "draft": frozenset({"reviewed"}),
    "reviewed": frozenset({"published", "draft"}),
    "published": frozenset({"reviewed"}),
}


class ContentStatusMachine:
    STATUSES = frozenset({"draft", "reviewed", "published"})

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        if current == target:
            return True
        return target in _ALLOWED.get(current, frozenset())

    @classmethod
    def transition(cls, current: str, target: str) -> str:
        if current not in cls.STATUSES or target not in cls.STATUSES:
            raise InvalidTransitionError(f"Unknown status: {current!r} -> {target!r}")
        if current == target:
            return current
        if not cls.can_transition(current, target):
            raise InvalidTransitionError(
                f"Transition not allowed: {current} -> {target}. "
                f"Allowed from {current}: {sorted(_ALLOWED.get(current, frozenset()))}"
            )
        return target

    @classmethod
    def requires_published_at(cls, previous: str, next_status: str) -> bool:
        """publish 전이 시 published_at 스탬프가 필요한지."""
        return previous != "published" and next_status == "published"
