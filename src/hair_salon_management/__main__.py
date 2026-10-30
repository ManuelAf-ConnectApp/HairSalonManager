from hair_salon_management.bootstrap import build_auth_service
from hair_salon_management.presentation.app import run


def main() -> int:
    return run(build_auth_service())


if __name__ == "__main__":
    raise SystemExit(main())
