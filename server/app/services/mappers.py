import json

from pydantic import ValidationError

from app.models.entities import Announcement, Content, Game, Inquiry
from app.schemas.common import (
    AnnouncementOut,
    ContentAnalysisOut,
    ContentOut,
    GameOut,
    InquiryOut,
    RankingOut,
)

_PUBLIC_IMAGE_RIGHTS = frozenset({"official", "licensed", "original"})


def _public_image_url(url: str | None, rights_status: str) -> str | None:
    return url if rights_status in _PUBLIC_IMAGE_RIGHTS else None


def game_to_out(
    game: Game,
    interest_count: int | None = None,
    *,
    public: bool = False,
) -> GameOut:
    return GameOut(
        id=game.id,
        name=game.name,
        initial=game.initial,
        genre=game.genre,
        color=game.color,
        interest_count=game.interest_count if interest_count is None else interest_count,
        image_url=(
            _public_image_url(game.image_url, game.image_rights_status)
            if public
            else game.image_url
        ),
        # 이미지 출처 메타데이터는 관리자 검수용이다. 공개 API에서
        # 원본 위치가 그대로 노출되면 미승인 이미지에 우회 접근할 수 있다.
        image_source_url=game.image_source_url if not public else None,
        image_rights_status=game.image_rights_status,
        fallback_image_key=game.fallback_image_key,
    )


def content_to_out(content: Content, include_status: bool = False) -> ContentOut:
    points: list[str]
    try:
        raw = json.loads(content.summary_points_json or "[]")
        points = [str(x) for x in raw] if isinstance(raw, list) else []
    except json.JSONDecodeError:
        points = []

    analysis = None
    try:
        raw_analysis = json.loads(content.analysis_json or "{}")
        if isinstance(raw_analysis, dict) and raw_analysis:
            analysis = ContentAnalysisOut.model_validate(raw_analysis)
    except (json.JSONDecodeError, ValidationError):
        analysis = None

    raw_excerpt = None
    if include_status and content.raw_text:
        raw_excerpt = content.raw_text[:1200]

    return ContentOut(
        id=content.id,
        game_id=content.game_id,
        game_name=content.game.name if content.game else content.game_id,
        kind=content.kind.value,
        title=content.title,
        summary_points=points,
        analysis=analysis,
        official_url=content.official_url,
        image_url=(
            _public_image_url(content.image_url, content.image_rights_status)
            if not include_status
            else content.image_url
        ),
        # 앱은 승인된 image_url만 필요하며 원본 출처 URL은 관리자 검수용이다.
        image_source_url=content.image_source_url if include_status else None,
        image_rights_status=content.image_rights_status,
        fallback_image_key=(
            content.game.fallback_image_key
            if content.game and content.game.fallback_image_key
            else "coverTactical"
        ),
        fallback_color=content.game.color if content.game else "#2A2A2B",
        place=content.place,
        reservation_url=content.reservation_url,
        starts_at=content.starts_at,
        ends_at=content.ends_at,
        published_at=content.published_at,
        status=content.status.value if include_status else None,
        idempotency_key=content.idempotency_key if include_status else None,
        summary_status=content.summary_status if include_status else None,
        source_id=content.source_id if include_status else None,
        created_at=content.created_at if include_status else None,
        summarized_at=content.summarized_at if include_status else None,
        origin_published_at=content.origin_published_at if include_status else None,
        raw_text_excerpt=raw_excerpt,
        needs_review_reason=content.needs_review_reason if include_status else None,
        scheduled_publish_at=content.scheduled_publish_at if include_status else None,
        link_broken=content.link_broken if include_status else None,
        auto_published=content.auto_published if include_status else None,
    )


def rankings_from_games(
    games: list[Game], interest_counts: dict[str, int] | None = None
) -> list[RankingOut]:
    counts = interest_counts or {}
    ordered = sorted(
        games,
        key=lambda g: (-counts.get(g.id, g.interest_count), g.name, g.id),
    )
    return [
        RankingOut(
            game_id=g.id,
            game_name=g.name,
            interest_count=counts.get(g.id, g.interest_count),
            rank=i + 1,
            initial=g.initial or g.name[:1],
            color=g.color,
            image_url=_public_image_url(g.image_url, g.image_rights_status),
            image_rights_status=g.image_rights_status,
            fallback_image_key=g.fallback_image_key,
        )
        for i, g in enumerate(ordered)
    ]


def announcement_to_out(item: Announcement) -> AnnouncementOut:
    return AnnouncementOut(
        id=item.id,
        title=item.title,
        body=item.body,
        published_at=item.published_at,
    )


def inquiry_to_out(item: Inquiry) -> InquiryOut:
    return InquiryOut(
        id=item.id,
        email=item.email,
        category=item.category,
        message=item.message,
        status=item.status.value,
        created_at=item.created_at,
    )
