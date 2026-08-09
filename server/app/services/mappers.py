import json

from app.models.entities import Announcement, Content, Game, Inquiry
from app.schemas.common import AnnouncementOut, ContentOut, GameOut, InquiryOut, RankingOut


def game_to_out(game: Game) -> GameOut:
    return GameOut(
        id=game.id,
        name=game.name,
        initial=game.initial,
        genre=game.genre,
        color=game.color,
        interest_count=game.interest_count,
        image_url=game.image_url,
    )


def content_to_out(content: Content, include_status: bool = False) -> ContentOut:
    points: list[str]
    try:
        raw = json.loads(content.summary_points_json or "[]")
        points = [str(x) for x in raw] if isinstance(raw, list) else []
    except json.JSONDecodeError:
        points = []

    return ContentOut(
        id=content.id,
        game_id=content.game_id,
        game_name=content.game.name if content.game else content.game_id,
        kind=content.kind.value,
        title=content.title,
        summary_points=points,
        official_url=content.official_url,
        image_url=content.image_url,
        place=content.place,
        reservation_url=content.reservation_url,
        starts_at=content.starts_at,
        ends_at=content.ends_at,
        published_at=content.published_at,
        status=content.status.value if include_status else None,
    )


def rankings_from_games(games: list[Game]) -> list[RankingOut]:
    ordered = sorted(games, key=lambda g: g.interest_count, reverse=True)
    return [
        RankingOut(
            game_id=g.id,
            game_name=g.name,
            interest_count=g.interest_count,
            rank=i + 1,
            initial=g.initial or g.name[:1],
            color=g.color,
            image_url=g.image_url,
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
