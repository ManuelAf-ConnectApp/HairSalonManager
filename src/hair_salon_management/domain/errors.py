class DomainError(ValueError):
    """Error de una regla de negocio que puede mostrarse de forma segura."""


class AuthenticationError(DomainError):
    """Credenciales inválidas o cuenta no utilizable."""


class DuplicateEmailError(DomainError):
    """El correo normalizado ya pertenece a una cuenta."""


class RecoveryError(DomainError):
    """Código de recuperación no válido o no utilizable."""
