import pytest

from app.domain.content_status import ContentStatusMachine, InvalidTransitionError


def test_happy_path_to_published() -> None:
    assert ContentStatusMachine.transition("draft", "reviewed") == "reviewed"
    assert ContentStatusMachine.transition("reviewed", "published") == "published"


def test_reject_skips_review() -> None:
    with pytest.raises(InvalidTransitionError):
        ContentStatusMachine.transition("draft", "published")


def test_unpublish_to_reviewed() -> None:
    assert ContentStatusMachine.transition("published", "reviewed") == "reviewed"


def test_same_status_noop() -> None:
    assert ContentStatusMachine.transition("draft", "draft") == "draft"


def test_requires_published_at_flag() -> None:
    assert ContentStatusMachine.requires_published_at("reviewed", "published") is True
    assert ContentStatusMachine.requires_published_at("published", "published") is False
