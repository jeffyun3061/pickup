"""이미지 업로드 · /privacy · 문의 rate limit 검증."""

from __future__ import annotations

# 1x1 투명 PNG
_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c626001000000ffff03000006000557bfabd40000000049454e44ae426082"
)


def _admin_headers(client):
    c, password = client
    token = c.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": password},
    ).json()["access_token"]
    return c, {"Authorization": f"Bearer {token}"}


def test_upload_image_saves_and_serves(client):
    c, headers = _admin_headers(client)
    res = c.post(
        "/api/v1/admin/uploads",
        headers=headers,
        files={"file": ("cover.png", _PNG, "image/png")},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["path"].startswith("/media/img_")
    assert body["url"].endswith(body["path"])

    served = c.get(body["path"])
    assert served.status_code == 200
    assert served.content == _PNG


def test_upload_rejects_non_image(client):
    c, headers = _admin_headers(client)
    res = c.post(
        "/api/v1/admin/uploads",
        headers=headers,
        files={"file": ("note.txt", b"hello", "text/plain")},
    )
    assert res.status_code == 400


def test_upload_requires_admin(client):
    c, _password = client
    res = c.post(
        "/api/v1/admin/uploads",
        files={"file": ("cover.png", _PNG, "image/png")},
    )
    assert res.status_code in {401, 403}


def test_privacy_page_served_at_root(client):
    c, _password = client
    res = c.get("/privacy")
    assert res.status_code == 200
    assert "개인정보처리방침" in res.text


def test_inquiry_rate_limit(client):
    c, _password = client
    payload = {"category": "etc", "message": "rate limit 확인용 문의입니다"}
    for _ in range(5):
        res = c.post("/api/v1/inquiries", json=payload)
        assert res.status_code == 201, res.text
    blocked = c.post("/api/v1/inquiries", json=payload)
    assert blocked.status_code == 429
