from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import Content, Game


class GameRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_active(self) -> list[Game]:
        stmt = select(Game).where(Game.is_active.is_(True)).order_by(Game.interest_count.desc())
        return list(self.db.scalars(stmt).all())

    def list_all(self) -> list[Game]:
        stmt = select(Game).order_by(Game.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get(self, game_id: str) -> Game | None:
        return self.db.get(Game, game_id)

    def count_contents(self, game_id: str) -> int:
        stmt = select(func.count()).select_from(Content).where(Content.game_id == game_id)
        return int(self.db.scalar(stmt) or 0)

    def add(self, game: Game) -> Game:
        self.db.add(game)
        self.db.flush()
        return game

    def save(self, game: Game) -> Game:
        self.db.add(game)
        self.db.flush()
        return game

    def delete(self, game: Game) -> None:
        self.db.delete(game)
        self.db.flush()
