"""JWT verification. Token issuance is handled by Keycloak (auth-service)."""

from jose import JWTError, jwt

from backend.shared.exceptions import SessionExpired


def decode_token(token: str, secret: str, algorithms: list[str] = ["HS256"]) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=algorithms)
    except JWTError as exc:
        raise SessionExpired(detail=str(exc)) from exc


def issue_token(claims: dict, secret: str, algorithm: str = "HS256") -> str:
    """Used only in tests and local dev. Production tokens come from Keycloak."""
    return jwt.encode(claims, secret, algorithm=algorithm)
