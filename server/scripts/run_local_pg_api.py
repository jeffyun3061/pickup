"""Docker 없이 로컬 PostgreSQL과 FastAPI를 함께 실행한다.

개발 전용 실행 경로다. ``pgserver``가 제공하는 PostgreSQL 바이너리를
``server/tmp/gamepickup-postgres``에 초기화하므로 컨테이너가 필요하지 않고,
프로세스를 종료해도 데이터 디렉터리는 보존된다. 운영에서는 이 스크립트가
아니라 Railway PostgreSQL을 사용한다.

실행::

    cd C:\\Users\\user\\Projects\\pickup\\server
    .\\.venv\\Scripts\\python scripts\\run_local_pg_api.py

앱 연결은 Metro를 별도로 API 모드로 실행한다::

    $env:EXPO_PUBLIC_CATALOG_MODE = "api"
    $env:EXPO_PUBLIC_API_URL = "http://127.0.0.1:8000"
    cd ..
    npm start
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pgserver


def main() -> int:
    server_dir = Path(__file__).resolve().parents[1]
    pgdata = server_dir / "tmp" / "gamepickup-postgres"
    pgdata.parent.mkdir(parents=True, exist_ok=True)

    pg = pgserver.get_server(pgdata, cleanup_mode="stop")
    try:
        databases = pg.psql("SELECT 1 FROM pg_database WHERE datname=$$gamepickup$$")
        if "1" not in databases.split():
            pg.psql("CREATE DATABASE gamepickup;")

        env = os.environ.copy()
        env["DATABASE_URL"] = pg.get_uri("gamepickup").replace(
            "postgresql://", "postgresql+psycopg://", 1
        )
        env.setdefault("ENV", "development")
        env.setdefault("SCHEDULER_ENABLED", "false")
        env.setdefault("EXPO_PUSH_ENABLED", "false")
        env["PYTHONUNBUFFERED"] = "1"

        # 앱과 동일한 SQLAlchemy 엔진으로 스키마를 만들고, 기본 카탈로그만 넣는다.
        sys.path.insert(0, str(server_dir))
        os.chdir(server_dir)
        os.environ.update(env)
        import app.main as api_main  # noqa: PLC0415

        api_main._initialize_database()
        subprocess.run(
            [sys.executable, "scripts/seed_demo_games.py"],
            cwd=server_dir,
            env=env,
            check=True,
        )

        print(f"로컬 PostgreSQL 준비 완료: {env['DATABASE_URL']}", flush=True)
        print("FastAPI: http://127.0.0.1:8000 (Ctrl+C로 종료, DB 파일은 보존)", flush=True)
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            cwd=server_dir,
            env=env,
        ).returncode
    finally:
        # cleanup_mode="stop"은 서버만 정지하고 pgdata는 삭제하지 않는다.
        pg.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
