from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, require_installation
from app.models.entities import Installation
from app.schemas.common import (
    DeviceTokenOut,
    DeviceTokenUpsert,
    InstallationCreateOut,
    InstallationPreferencesIn,
    InstallationPreferencesOut,
)
from app.services.installation_service import InstallationService

router = APIRouter(prefix="/api/v1/installations", tags=["installations"])


@router.post("", response_model=InstallationCreateOut, status_code=201)
def register_installation(db: Session = Depends(db_session)) -> InstallationCreateOut:
    return InstallationService(db).register()


@router.put("/me/device-token", response_model=DeviceTokenOut)
def upsert_device_token(
    body: DeviceTokenUpsert,
    installation: Installation = Depends(require_installation),
    db: Session = Depends(db_session),
) -> DeviceTokenOut:
    return InstallationService(db).upsert_device_token(installation, body)


@router.get("/me/preferences", response_model=InstallationPreferencesOut)
def get_preferences(
    installation: Installation = Depends(require_installation),
    db: Session = Depends(db_session),
) -> InstallationPreferencesOut:
    return InstallationService(db).get_preferences(installation)


@router.put("/me/preferences", response_model=InstallationPreferencesOut)
def put_preferences(
    body: InstallationPreferencesIn,
    installation: Installation = Depends(require_installation),
    db: Session = Depends(db_session),
) -> InstallationPreferencesOut:
    return InstallationService(db).update_preferences(installation, body)
