import uuid


def new_id(prefix: str) -> str:
    """짧은 유니크 id. DB PK·외부 참조용."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
