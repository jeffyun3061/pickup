"""
LLM 요약 + 자동 발행 파이프라인.

- ingest로 draft가 생기면 백그라운드에서 요약하고, 신뢰 소스(auto_publish)면
  상태머신 전이(draft→reviewed→published)를 자동 수행한다. ingest 권한이 발행하는 게
  아니라 서버가 검수 전이를 대행하는 구조라 권한 경계는 유지된다 (ADR-012).
- OPENAI_API_KEY가 없으면 collector의 규칙 기반 요약을 그대로 쓴다(요약 상태 none).
- 요약 실패 시 draft로 남겨 관리자 검수로 폴백한다. 자동 발행하지 않는다.
- 일일 호출 상한(SUMMARIZE_DAILY_LIMIT)으로 비용 폭주를 막는다.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, time as dtime, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models.entities import Content, ContentKind
from app.repositories.ingest_repository import IngestRepository

logger = logging.getLogger(__name__)

_VALID_KINDS = {"update", "event", "popup", "goods"}
_MAX_INPUT_CHARS = 8000

_SYSTEM_PROMPT = (
    "너는 모바일 게임 공지 요약 편집자다. 주어진 공지 원문을 읽고 JSON으로만 답한다. "
    '형식: {"summary_points": ["...", "...", "..."], "kind": "update|event|popup|goods", '
    '"analysis": {"importance": 1|2|3, "impact_level": "low|medium|high", '
    '"impact_summary": "...", "confidence": "low|medium|high"}}. '
    "summary_points는 한국어 완결 문장 최대 3개, 각 80자 이내로 핵심(무엇이, 언제, 유저가 할 일)만 담는다. "
    "kind는 공지 성격에 맞게 고른다: update(업데이트·점검·패치), event(이벤트·기간 한정), "
    "popup(오프라인 팝업·전시), goods(굿즈·상품 판매). "
    "analysis는 공식 공지에서 확인할 수 있는 범위만 판단하고, 커뮤니티 반응은 추측하지 않는다. "
    "importance는 유저 행동·보상·점검 영향이 클수록 3, 단순 안내는 1이다."
)


class SummarizeError(RuntimeError):
    pass


def call_llm(settings: Settings, title: str, text: str) -> dict:
    """OpenAI Chat Completions 호출. 테스트에서 monkeypatch하는 유일한 진입점."""
    response = httpx.post(
        f"{settings.openai_base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        json={
            "model": settings.openai_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"제목: {title}\n\n원문:\n{text[:_MAX_INPUT_CHARS]}",
                },
            ],
        },
        timeout=45.0,
    )
    response.raise_for_status()
    try:
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise SummarizeError("LLM response shape is invalid") from exc
    if not isinstance(parsed, dict):
        raise SummarizeError("LLM response must be a JSON object")
    return parsed


class SummarizeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    @property
    def configured(self) -> bool:
        return bool(self.settings.openai_api_key)

    def _today_count(self) -> int:
        start = datetime.combine(datetime.now(timezone.utc).date(), dtime.min, tzinfo=timezone.utc)
        stmt = select(func.count(Content.id)).where(Content.summarized_at >= start)
        return int(self.db.scalar(stmt) or 0)

    @staticmethod
    def _normalize_analysis(result: dict) -> dict | None:
        """LLM 분석을 공개 계약에 맞게 제한한다.

        커뮤니티 근거를 별도로 수집하지 않은 단계에서는 sentiment를 절대 추정하지
        않는다. 알 수 없는 값은 UI가 '자료 수집 전'으로 표시할 수 있도록 unknown으로
        고정한다.
        """
        raw = result.get("analysis")
        if not isinstance(raw, dict):
            return None
        try:
            importance = int(raw.get("importance"))
        except (TypeError, ValueError):
            return None
        impact_level = str(raw.get("impact_level", "")).strip()
        confidence = str(raw.get("confidence", "")).strip()
        impact_summary = str(raw.get("impact_summary", "")).strip()
        if importance not in {1, 2, 3}:
            return None
        if impact_level not in {"low", "medium", "high"}:
            return None
        if confidence not in {"low", "medium", "high"}:
            return None
        if not impact_summary or len(impact_summary) > 80:
            return None
        return {
            "importance": importance,
            "impact_level": impact_level,
            "impact_summary": impact_summary,
            "confidence": confidence,
            "community_sentiment": "unknown",
            "community_summary": "반응은 조금 더 지켜볼게요.",
            "community_sample_count": 0,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def summarize(self, content: Content) -> bool:
        """성공 시 summary_points/kind 갱신 + done. 실패 시 failed. 상한 도달 시 pending 유지."""
        if not self.configured:
            content.summary_status = "none"
            return False
        if self._today_count() >= self.settings.summarize_daily_limit:
            logger.warning("summarize daily limit reached; content %s left pending", content.id)
            content.summary_status = "pending"
            return False

        source_text = (content.raw_text or "").strip()
        if not source_text:
            source_text = " ".join(self._current_points(content)) or content.title

        try:
            result = call_llm(self.settings, content.title, source_text)
            points = [str(p).strip() for p in result.get("summary_points", []) if str(p).strip()]
            if not points:
                raise SummarizeError("LLM returned no summary points")
            content.summary_points_json = json.dumps(points[:3], ensure_ascii=False)
            analysis = self._normalize_analysis(result)
            if analysis:
                content.analysis_json = json.dumps(analysis, ensure_ascii=False)
            kind = str(result.get("kind", "")).strip()
            if kind in _VALID_KINDS:
                content.kind = ContentKind(kind)
            content.summary_status = "done"
            content.summarized_at = datetime.now(timezone.utc)
            return True
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, SummarizeError) as exc:
            logger.warning("summarize failed for content %s: %s", content.id, exc)
            content.summary_status = "failed"
            content.summarized_at = datetime.now(timezone.utc)
            return False

    @staticmethod
    def _current_points(content: Content) -> list[str]:
        try:
            raw = json.loads(content.summary_points_json or "[]")
            return [str(x) for x in raw] if isinstance(raw, list) else []
        except json.JSONDecodeError:
            return []

    def post_ingest(self, content_id: str) -> None:
        """ingest 직후 파이프라인: 요약 → 품질 게이트 → (신뢰 소스면) 자동 발행 + 푸시."""
        from app.domain.content_quality import classify_kind, evaluate_summary

        content = self.db.get(Content, content_id)
        if content is None or content.status.value != "draft":
            return

        summarized = self.summarize(content) if content.summary_status == "pending" else False

        # LLM 요약이 없으면 제목 키워드로 종류 폴백 분류 (소스 기본값 보정)
        if content.summary_status == "none":
            fallback_kind = classify_kind(content.title)
            if fallback_kind and fallback_kind != content.kind.value:
                content.kind = ContentKind(fallback_kind)
        self.db.flush()

        if not content.source_id:
            return
        source = IngestRepository(self.db).get_source(content.source_id)
        if source is None or not source.auto_publish:
            return
        # 요약 실패(failed)나 상한 대기(pending)면 자동 발행하지 않고 검수로 넘긴다.
        if content.summary_status not in {"done", "none"}:
            return

        # 품질 게이트: 통과 못 하면 사유를 남기고 검수 큐로 보낸다 ('자동이지만 정확')
        reason = evaluate_summary(content.title, self._current_points(content))
        if reason:
            content.needs_review_reason = reason
            self.db.flush()
            logger.info(
                "quality gate blocked auto-publish for content %s: %s", content.id, reason
            )
            return
        content.needs_review_reason = None

        from app.schemas.common import ContentUpdate
        from app.services.admin_service import AdminService

        admin = AdminService(self.db)
        admin.update_content(content.id, ContentUpdate(status="reviewed"), actor="auto")
        admin.update_content(content.id, ContentUpdate(status="published"), actor="auto")
        admin.dispatch_push(limit=500)
        logger.info(
            "auto-published content %s from source %s (summarized=%s)",
            content.id,
            source.id,
            summarized,
        )


def run_post_ingest(content_id: str) -> None:
    """BackgroundTasks 진입점 — 요청 트랜잭션과 분리된 새 세션에서 실행."""
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        SummarizeService(db).post_ingest(content_id)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("post-ingest pipeline failed for content %s", content_id)
    finally:
        db.close()
