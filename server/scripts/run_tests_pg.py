"""
임베디드 PostgreSQL로 전체 pytest 실행 (Docker 불필요).

프로덕션 DB(PostgreSQL) 호환성 검증용:
    .venv\\Scripts\\python scripts\\run_tests_pg.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    import pgserver

    server_dir = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="pickup-pg-") as tmp:
        pg = pgserver.get_server(Path(tmp) / "pgdata")
        try:
            uri = pg.get_uri("gamepickup_test")
            pg.psql("CREATE DATABASE gamepickup_test;")
            test_url = uri.replace("postgresql://", "postgresql+psycopg://", 1)
            print(f"embedded postgres: {test_url}")

            env = dict(os.environ, TEST_DATABASE_URL=test_url)
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", *sys.argv[1:]],
                cwd=server_dir,
                env=env,
            )
            return result.returncode
        finally:
            pg.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
