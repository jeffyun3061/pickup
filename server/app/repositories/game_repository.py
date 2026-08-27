from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.entities import Content, Game, Installation, InstallationGame


class GameRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_active(self) -> list[Game]:
        """활성 게임을 실제 활성 설치 수 순서로 반환한다.

        공개 카탈로그·랭킹과 동일한 집계 경계를 사용해, 이 편의 메서드가
        다시 호출되더라도 관리자가 입력한 레거시 ``interest_count``를
        사용자 수처럼 노출하지 않도록 한다.
        """
        return [game for game, _count in self.list_active_with_interest_counts()]

    def list_active_with_interest_counts(self) -> list[tuple[Game, int]]:
        """활성 게임과 유효 설치 기준 관심 등록 수를 함께 조회한다.

        관리자 입력값인 games.interest_count는 레거시/시드 호환용으로만
        남겨두고, 공개 랭킹은 설치-게임 관계를 distinct count한다.
        """
        count_expr = func.count(func.distinct(Installation.id))
        stmt = (
            select(Game, count_expr.label("interest_count"))
            .outerjoin(InstallationGame, InstallationGame.game_id == Game.id)
            .outerjoin(
                Installation,
                and_(
                    Installation.id == InstallationGame.installation_id,
                    Installation.revoked_at.is_(None),
                ),
            )
            .where(Game.is_active.is_(True))
            # PostgreSQL requires every selected Game column in GROUP BY.
            # Listing the table columns keeps the aggregate query explicit.
            .group_by(*Game.__table__.columns)
            .order_by(count_expr.desc(), Game.name.asc(), Game.id.asc())
        )
        return [(game, int(count)) for game, count in self.db.execute(stmt).all()]

    def list_all_with_interest_counts(self) -> list[tuple[Game, int]]:
        """관리자 카탈로그도 공개 랭킹과 같은 설치 집계를 사용한다."""
        count_expr = func.count(func.distinct(Installation.id))
        stmt = (
            select(Game, count_expr.label("interest_count"))
            .outerjoin(InstallationGame, InstallationGame.game_id == Game.id)
            .outerjoin(
                Installation,
                and_(
                    Installation.id == InstallationGame.installation_id,
                    Installation.revoked_at.is_(None),
                ),
            )
            .group_by(*Game.__table__.columns)
            .order_by(Game.is_active.desc(), Game.name.asc(), Game.id.asc())
        )
        return [(game, int(count)) for game, count in self.db.execute(stmt).all()]

    def list_active_ids(self) -> set[str]:
        stmt = select(Game.id).where(Game.is_active.is_(True))
        return set(self.db.scalars(stmt).all())

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
