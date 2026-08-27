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
        rows = self.games.list_active_with_interest_counts()
        return [game_to_out(game, count, public=True) for game, count in rows]

    def list_contents(
        self,
        scope: str,
        game_ids: list[str],
        *,
        limit: int = 100,
    ) -> list[ContentOut]:
        if scope == "mine":
            if not game_ids:
                return []
            rows = self.contents.list_published(game_ids, limit=limit)
        else:
            rows = self.contents.list_published(None, limit=limit)
        return [content_to_out(c) for c in rows]

    def list_rankings(self) -> list[RankingOut]:
        rows = self.games.list_active_with_interest_counts()
        games = [game for game, _count in rows]
        counts = {game.id: count for game, count in rows}
        return rankings_from_games(games, counts)

    def list_announcements(self) -> list[AnnouncementOut]:
        return [announcement_to_out(a) for a in self.announcements.list_published()]
