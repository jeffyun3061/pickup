import uuid

from sqlalchemy.orm import Session

from app.models.entities import Inquiry, InquiryStatus
from app.repositories.inquiry_repository import InquiryRepository
from app.schemas.common import InquiryCreate, InquiryOut
from app.services.mappers import inquiry_to_out


class InquiryService:
    def __init__(self, db: Session) -> None:
        self.repo = InquiryRepository(db)

    def create(self, body: InquiryCreate) -> InquiryOut:
        item = Inquiry(
            id=f"inq_{uuid.uuid4().hex[:12]}",
            email=body.email,
            category=body.category,
            message=body.message.strip(),
            status=InquiryStatus.open,
        )
        return inquiry_to_out(self.repo.add(item))
