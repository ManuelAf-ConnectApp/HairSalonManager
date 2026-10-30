from __future__ import annotations

import re

from .errors import DomainError

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_email(value: str) -> str:
    email = value.strip().casefold()
    if not EMAIL_PATTERN.fullmatch(email):
        raise DomainError("Introduce un correo electrónico válido.")
    return email


def validate_password(password: str) -> None:
    if len(password) < 12:
        raise DomainError("La contraseña debe tener al menos 12 caracteres.")
    categories = sum((any(c.islower() for c in password), any(c.isupper() for c in password),
                      any(c.isdigit() for c in password), any(not c.isalnum() for c in password)))
    if categories < 3:
        raise DomainError("Usa mayúsculas, minúsculas, números o símbolos (al menos tres grupos).")
