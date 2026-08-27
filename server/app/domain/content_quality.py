"""
콘텐츠 품질 규칙 (순수 도메인).

- 요약 품질 게이트: 자동 발행 전 최소 품질을 강제해 '자동이지만 정확'을 보장한다.
  통과 못 하면 발행하지 않고 사유와 함께 검수 큐로 보낸다.
- kind 키워드 분류: LLM 요약이 없을 때 제목으로 종류를 추정하는 폴백.
"""

from __future__ import annotations

_MIN_POINT_LEN = 5
_MAX_POINT_LEN = 140
_MAX_POINTS = 5

# 게임 공지에 나올 수 없는 스팸/광고 마커
_BANNED_TOKENS = ("카지노", "토토", "출장", "성인용품", "대출문의")

_KIND_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("popup", ("팝업", "팝업스토어", "전시", "체험존", "오프라인 매장")),
    ("goods", ("굿즈", "피규어", "인형", "머천", "상품 출시", "한정판 판매")),
    ("event", ("이벤트", "사전등록", "사전 등록", "출석", "쿠폰", "보상 지급", "기간 한정")),
    ("update", ("업데이트", "패치", "점검", "버그 수정", "밸런스", "신규 캐릭터", "시즌 오픈")),
]


def evaluate_summary(title: str, points: list[str]) -> str | None:
    """품질 게이트. 통과하면 None, 아니면 사람이 읽을 사유를 돌려준다."""
    cleaned = [p.strip() for p in points if p and p.strip()]
    if not cleaned:
        return "요약이 비어 있음"
    if len(cleaned) > _MAX_POINTS:
        return f"요약 포인트가 너무 많음 ({len(cleaned)}개)"

    normalized_title = title.strip().lower()
    for point in cleaned:
        if len(point) < _MIN_POINT_LEN:
            return f"요약 문장이 너무 짧음 ('{point[:20]}')"
        if len(point) > _MAX_POINT_LEN:
            return "요약 문장이 너무 김 (140자 초과)"
        if point.strip().lower() == normalized_title:
            return "요약이 제목을 그대로 복사함"
        for token in _BANNED_TOKENS:
            if token in point:
                return f"금칙어 포함 ('{token}')"

    for token in _BANNED_TOKENS:
        if token in title:
            return f"제목에 금칙어 포함 ('{token}')"
    return None


def classify_kind(title: str) -> str | None:
    """제목 키워드로 kind 추정. 확신 없으면 None (소스 기본값 유지)."""
    for kind, keywords in _KIND_KEYWORDS:
        if any(keyword in title for keyword in keywords):
            return kind
    return None
