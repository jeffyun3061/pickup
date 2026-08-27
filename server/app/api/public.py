import time
from collections import defaultdict, deque
from html import escape

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.common import (
    AnnouncementOut,
    ContentOut,
    GameOut,
    InquiryCreate,
    InquiryOut,
    RankingOut,
)
from app.services.catalog_service import CatalogService
from app.services.inquiry_service import InquiryService

router = APIRouter(prefix="/api/v1", tags=["public"])

# 문의 스팸 방지: IP당 10분에 5건 (단일 워커 인메모리 — 워커 1개 운용 전제)
_INQUIRY_WINDOW_SECONDS = 600
_INQUIRY_MAX_PER_WINDOW = 5
_inquiry_hits: dict[str, deque[float]] = defaultdict(deque)
_MAX_GAME_FILTER_IDS = 8


def _check_inquiry_rate_limit(client_ip: str) -> None:
    now = time.monotonic()
    hits = _inquiry_hits[client_ip]
    while hits and now - hits[0] > _INQUIRY_WINDOW_SECONDS:
        hits.popleft()
    if len(hits) >= _INQUIRY_MAX_PER_WINDOW:
        raise HTTPException(status_code=429, detail="Too many inquiries; try again later")
    hits.append(now)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/live")
def health_live() -> dict[str, str]:
    """컨테이너 프로세스 생존 확인용. 외부 의존성은 검사하지 않는다."""
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready(db: Session = Depends(db_session)) -> dict[str, str]:
    """트래픽 수신 가능 여부를 DB 연결까지 포함해 확인한다."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="database not ready") from exc
    return {"status": "ok", "database": "ok"}


@router.get("/meta")
def meta() -> dict[str, str]:
    """앱 부트 시 확인하는 메타 정보 (최소 지원 버전 등)."""
    from app.config import get_settings

    return {"min_app_version": get_settings().min_app_version}


@router.get("/games", response_model=list[GameOut])
def list_games(db: Session = Depends(db_session)) -> list[GameOut]:
    return CatalogService(db).list_games()


@router.get("/contents", response_model=list[ContentOut])
def list_contents(
    scope: str = Query(default="all", pattern="^(all|mine)$"),
    game_ids: str = Query(default="", description="comma-separated ids for scope=mine"),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(db_session),
) -> list[ContentOut]:
    ids = [x.strip() for x in game_ids.split(",") if x.strip()]
    if scope == "mine" and len(ids) > _MAX_GAME_FILTER_IDS:
        raise HTTPException(
            status_code=422,
            detail=f"You can filter up to {_MAX_GAME_FILTER_IDS} games",
        )
    return CatalogService(db).list_contents(scope, ids, limit=limit)


@router.get("/rankings", response_model=list[RankingOut])
def list_rankings(db: Session = Depends(db_session)) -> list[RankingOut]:
    return CatalogService(db).list_rankings()


@router.get("/announcements", response_model=list[AnnouncementOut])
def list_announcements(db: Session = Depends(db_session)) -> list[AnnouncementOut]:
    return CatalogService(db).list_announcements()


@router.post("/inquiries", response_model=InquiryOut, status_code=201)
def create_inquiry(
    body: InquiryCreate,
    request: Request,
    db: Session = Depends(db_session),
) -> InquiryOut:
    _check_inquiry_rate_limit(request.client.host if request.client else "unknown")
    return InquiryService(db).create(body)


_PRIVACY_HTML = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PIKY 개인정보처리방침</title>
  <style>
    body { font-family: -apple-system, "Segoe UI", "Malgun Gothic", sans-serif;
           max-width: 720px; margin: 40px auto; padding: 0 20px; line-height: 1.7; color: #222; }
    h1 { font-size: 24px; } h2 { font-size: 18px; margin-top: 28px; }
  </style>
</head>
<body>
  <h1>PIKY(게임픽업) 개인정보처리방침</h1>
  <p>PIKY는 회원가입 없이 사용하는 게임 소식 앱입니다. 계정·이름·연락처를 요구하지 않으며,
     서비스 제공에 필요한 최소한의 정보만 처리합니다.</p>

  <h2>1. 수집하는 정보</h2>
  <ul>
    <li><strong>설치 식별자</strong>: 앱 설치 시 서버가 발급하는 무작위 ID (개인을 직접 식별하지 않음)</li>
    <li><strong>푸시 토큰</strong>: 알림 수신에 동의한 경우에만 등록</li>
    <li><strong>설정 정보</strong>: 관심 게임 목록, 알림 종류 설정</li>
    <li><strong>문의 내용</strong>: 문의하기 이용 시 작성 내용과 (선택 입력한) 이메일</li>
  </ul>

  <h2>2. 이용 목적</h2>
  <ul>
    <li>관심 게임의 새 소식·이벤트 마감 푸시 알림 발송</li>
    <li>문의 답변 및 서비스 개선</li>
  </ul>

  <h2>3. 보관 및 파기</h2>
  <p>알림을 끄거나 앱의 '데이터 초기화'를 실행하면 해당 설치는 즉시 발송 대상에서
     제외되고, 관심 게임과 푸시 토큰 연결을 해지합니다. 앱 삭제 사실은 서버가 직접
     알 수 없으므로 이후 발송 실패를 기록하며 운영 정리 시 토큰을 삭제합니다.
     비활성 설치 데이터와 문의 내용은 운영 보존정책에 따라 검토 후 파기합니다.
     문의 내용은 답변 완료 후 6개월 이내 처리를 원칙으로 합니다.</p>

  <h2>4. 제3자 제공</h2>
  <p>법령에 따른 경우를 제외하고 개인정보를 제3자에게 제공하지 않습니다.
     푸시 발송을 위해 Expo Push Service(미국)를 통해 푸시 토큰이 전송됩니다.</p>

  <h2>5. 문의처</h2>
  <p>앱 내 문의하기 또는 __CONTACT_EMAIL__로 연락해 주세요.</p>

  <p>시행일: 2026-08-25</p>
</body>
</html>"""

_TERMS_HTML = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PIKY 이용약관</title>
  <style>
    body { font-family: -apple-system, "Segoe UI", "Malgun Gothic", sans-serif;
           max-width: 720px; margin: 40px auto; padding: 0 20px; line-height: 1.7; color: #222; }
    h1 { font-size: 24px; } h2 { font-size: 18px; margin-top: 28px; }
  </style>
</head>
<body>
  <h1>PIKY(게임픽업) 이용약관</h1>
  <p>PIKY는 사용자가 선택한 게임의 공식 소식과 행사 정보를 원문 링크와 함께
     정리해 보여주는 서비스입니다.</p>

  <h2>1. 콘텐츠 이용</h2>
  <p>소식의 저작권과 상표권은 각 발행처와 권리자에게 있습니다. PIKY는 원문을
     대체하지 않으며, 원문 링크·발행처·공개된 메타데이터를 기준으로 안내합니다.
     원문을 확인할 때는 해당 발행처의 이용약관을 따릅니다.</p>

  <h2>2. 타키의 정리</h2>
  <p>앱에 표시되는 중요도·영향·반응 문구는 수집된 공식 공지를 바탕으로 한 참고용
     자동 정리입니다. 사실·일정·보상은 반드시 원문을 확인해야 하며, 게임 플레이나
     결제에 관한 결정을 대신하지 않습니다.</p>

  <h2>3. 오류·삭제 요청</h2>
  <p>권리 침해, 잘못된 내용, 삭제 또는 정정 요청은 앱 내 문의하기 또는
     __CONTACT_EMAIL__로 보내 주세요. 확인 후 해당 콘텐츠의 비공개·수정·원문 링크
     교체를 처리합니다.</p>

  <h2>4. 서비스 변경</h2>
  <p>소스 제공 여부, 알림 기능, 화면 구성은 운영·권리·기술 사정에 따라 변경될 수
     있습니다. 중대한 변경은 앱 공지로 안내합니다.</p>

  <p>시행일: 2026-08-25</p>
</body>
</html>"""


# prefix 없는 라우터 — 스토어 등록용 URL을 https://<도메인>/privacy 로 노출
root_router = APIRouter(tags=["public"])


@root_router.get("/health/live")
def root_health_live() -> dict[str, str]:
    return {"status": "ok"}


@root_router.get("/health/ready")
def root_health_ready(db: Session = Depends(db_session)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="database not ready") from exc
    return {"status": "ok", "database": "ok"}


@root_router.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
def privacy_policy() -> HTMLResponse:
    """스토어 등록용 개인정보처리방침 (계정 없는 서비스 기준)."""
    from app.config import get_settings

    contact = get_settings().privacy_contact_email.strip()
    contact_html = escape(contact) if contact else "앱 내 문의하기"
    return HTMLResponse(_PRIVACY_HTML.replace("__CONTACT_EMAIL__", contact_html))


@root_router.get("/terms", response_class=HTMLResponse, include_in_schema=False)
def terms_policy() -> HTMLResponse:
    """스토어·앱 링크용 이용약관 및 자동 정리 고지."""
    from app.config import get_settings

    contact = get_settings().privacy_contact_email.strip()
    contact_html = escape(contact) if contact else "앱 내 문의하기"
    return HTMLResponse(_TERMS_HTML.replace("__CONTACT_EMAIL__", contact_html))
