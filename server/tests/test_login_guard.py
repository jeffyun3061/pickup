def _login(c, password: str):
    return c.post("/api/v1/admin/login", json={"username": "admin", "password": password})


def test_login_locks_after_repeated_failures(client):
    c, password = client
    for _ in range(5):
        assert _login(c, "wrong-password").status_code == 401

    # 잠금 중에는 올바른 비밀번호도 거부된다
    locked = _login(c, password)
    assert locked.status_code == 429
    assert "Retry-After" in locked.headers


def test_login_success_resets_failure_counter(client):
    c, password = client
    for _ in range(4):
        assert _login(c, "wrong-password").status_code == 401

    assert _login(c, password).status_code == 200

    # 성공으로 카운터가 초기화되어 이후 4회 실패로는 잠기지 않는다
    for _ in range(4):
        assert _login(c, "wrong-password").status_code == 401
    assert _login(c, password).status_code == 200
