"""JWT issuance and verification (delegated to Keycloak in production)."""


def decode_token(token: str) -> dict:
    raise NotImplementedError


def issue_token(claims: dict) -> str:
    raise NotImplementedError
