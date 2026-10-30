from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


class PasswordHasher:
    """Hash con scrypt de la biblioteca estándar; los valores no contienen contraseñas."""

    algorithm = "scrypt"
    n = 2**14
    r = 8
    p = 1

    def hash(self, secret: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(secret.encode("utf-8"), salt=salt, n=self.n, r=self.r, p=self.p)
        return "$".join((self.algorithm, str(self.n), str(self.r), str(self.p),
                          base64.b64encode(salt).decode(), base64.b64encode(digest).decode()))

    def verify(self, secret: str, encoded: str) -> bool:
        try:
            algorithm, n, r, p, encoded_salt, expected = encoded.split("$")
            if algorithm != self.algorithm:
                return False
            digest = hashlib.scrypt(secret.encode("utf-8"), salt=base64.b64decode(encoded_salt),
                                    n=int(n), r=int(r), p=int(p))
            return hmac.compare_digest(digest, base64.b64decode(expected))
        except (ValueError, TypeError, UnicodeError):
            return False


def generate_recovery_code() -> str:
    # 160 bits de entropía; el guion solo mejora la lectura.
    token = secrets.token_urlsafe(20).upper()
    return "-".join((token[:7], token[7:14], token[14:]))
