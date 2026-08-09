"""Usage: python scripts/make_password_hash.py your-password"""

import sys

from passlib.context import CryptContext


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/make_password_hash.py <password>")
        raise SystemExit(1)
    print(CryptContext(schemes=["bcrypt"]).hash(sys.argv[1]))


if __name__ == "__main__":
    main()
