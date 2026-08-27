from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# 모든 환경이 PostgreSQL이므로 같은 연결 안정성 정책을 사용한다.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
    # 부팅 시 DB가 아직 준비되지 않은 경우에도 각 재시도가 무한히
    # 기다리지 않게 한다. 운영 네트워크가 정상화되면 풀 연결은 그대로 재사용한다.
    connect_args={"connect_timeout": 3},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """요청 단위 트랜잭션: 성공 시 commit, 예외 시 rollback."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
