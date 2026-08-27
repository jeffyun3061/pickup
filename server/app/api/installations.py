import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
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

# 무인 설치 발급은 DB에 행과 bcrypt 해시를 만들기 때문에 공개 엔드포인트라도
# 무제한으로 두면 비용·저장소가 먼저 고갈될 수 있다. API는 단일 워커로 운영하고,
# 확장 시 이 카운터를 Redis 같은 공유 저장소로 옮긴다.
_REGISTER_WINDOW_SECONDS = 600
_REGISTER_MAX_PER_IP = 30
_register_hits: dict[str, deque[float]] = defaultdict(deque)


def _check_register_rate_limit(client_ip: str) -> None:
    now = time.monotonic()
    hits = _register_hits[client_ip]
    while hits and now - hits[0] > _REGISTER_WINDOW_SECONDS:
        hits.popleft()
    if len(hits) >= _REGISTER_MAX_PER_IP:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many installation registrations; try again later",
            headers={"Retry-After": str(_REGISTER_WINDOW_SECONDS)},
        )
    hits.append(now)


@router.post("", response_model=InstallationCreateOut, status_code=201)
def register_installation(
    request: Request,
    db: Session = Depends(db_session),
) -> InstallationCreateOut:
    _check_register_rate_limit(request.client.host if request.client else "unknown")
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


@router.delete("/me", status_code=204)
def revoke_installation(
    installation: Installation = Depends(require_installation),
    db: Session = Depends(db_session),
) -> Response:
    InstallationService(db).revoke(installation)
    return Response(status_code=204)
