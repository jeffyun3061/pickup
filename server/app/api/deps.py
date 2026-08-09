import hmac

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models.entities import Installation
from app.security import decode_access_token
from app.services.installation_service import InstallationService

bearer = HTTPBearer(auto_error=False)


def db_session(db: Session = Depends(get_db)) -> Session:
    return db


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    subject = decode_access_token(credentials.credentials)
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return subject


def require_ingest_key(x_ingest_key: str | None = Header(default=None, alias="X-Ingest-Key")) -> None:
    settings = get_settings()
    expected = settings.ingest_api_key or ""
    provided = x_ingest_key or ""
    if not expected or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingest key")


def require_installation(
    db: Session = Depends(db_session),
    x_installation_id: str | None = Header(default=None, alias="X-Installation-Id"),
    x_installation_secret: str | None = Header(default=None, alias="X-Installation-Secret"),
) -> Installation:
    if not x_installation_id or not x_installation_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Installation credentials required",
        )
    return InstallationService(db).authenticate(x_installation_id, x_installation_secret)
