from sqlalchemy.orm import Session

from app.repositories.announcement_repository import AnnouncementRepository
from app.repositories.content_repository import ContentRepository
from app.repositories.game_repository import GameRepository
from app.schemas.common import AnnouncementOut, ContentOut, GameOut, RankingOut
from app.services.mappers import (
    announcement_to_out,
    content_to_out,
    game_to_out,
    rankings_from_games,
)


class CatalogService:
    def __init__(self, db: Session) -> None:
        self.games = GameRepository(db)
        self.contents = ContentRepository(db)
        self.announcements = AnnouncementRepository(db)

    def list_games(self) -> list[GameOut]:
        return [game_to_out(g) for g in self.games.list_active()]

    def list_contents(self, scope: str, game_ids: list[str]) -> list[ContentOut]:
        if scope == "mine":
            if not game_ids:
                return []
            rows = self.contents.list_published(game_ids)
        else:
            rows = self.contents.list_published(None)
        return [content_to_out(c) for c in rows]

    def list_rankings(self) -> list[RankingOut]:
        return rankings_from_games(self.games.list_active())

    def list_announcements(self) -> list[AnnouncementOut]:
        return [announcement_to_out(a) for a in self.announcements.list_published()]
