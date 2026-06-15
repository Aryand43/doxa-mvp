"""
Authentication and authorisation helpers.

The production product requirements call for JWT forwarding, RBAC, and tenant
isolation by buyer_company_uuid. This module keeps that security context in one
place so routes, data access, retrieval, and future agents all enforce the same
claims.

Local development can run without a token while AUTH_REQUIRED=false. Set
AUTH_REQUIRED=true and AUTH_JWT_SECRET to enforce signed bearer tokens.
"""

from __future__ import annotations

import base64
import contextlib
import contextvars
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from typing import Any, Iterator

import pandas as pd
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config import (
    AUTH_JWT_ALGORITHM,
    AUTH_JWT_AUDIENCE,
    AUTH_JWT_ISSUER,
    AUTH_JWT_SECRET,
    AUTH_REQUIRED,
)

UNAUTHORIZED_MODULE_MESSAGE = "You don't have access to that module. Please contact your admin."

_bearer = HTTPBearer(auto_error=False)
_current_auth: contextvars.ContextVar[AuthContext | None] = contextvars.ContextVar(
    "current_auth",
    default=None,
)


class AuthError(ValueError):
    """Raised when a bearer token is missing, malformed, or invalid."""


class PermissionError(ValueError):
    """Raised when a valid user lacks the required role, authority, or tenant."""


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    companies: frozenset[str] = field(default_factory=frozenset)
    authorities: frozenset[str] = field(default_factory=frozenset)
    roles: frozenset[str] = field(default_factory=frozenset)
    raw_token: str | None = None
    claims: dict[str, Any] = field(default_factory=dict)

    @property
    def is_development_bypass(self) -> bool:
        return self.user_id == "local-dev"

    def has_company(self, buyer_company_uuid: str | None) -> bool:
        if not buyer_company_uuid:
            return False
        return "*" in self.companies or str(buyer_company_uuid) in self.companies

    def has_authority(self, authority: str) -> bool:
        if "*" in self.authorities:
            return True
        if authority in self.authorities:
            return True
        namespace, _, action = authority.partition(":")
        return bool(namespace and f"{namespace}:*" in self.authorities) or bool(
            action and f"*:{action}" in self.authorities
        )


def current_auth_context() -> AuthContext | None:
    return _current_auth.get()


@contextlib.contextmanager
def auth_context(user: AuthContext) -> Iterator[None]:
    """Bind auth claims to the current request/task."""
    token = _current_auth.set(user)
    try:
        yield
    finally:
        _current_auth.reset(token)


def development_auth_context() -> AuthContext:
    """Wide-open context for local demo mode when AUTH_REQUIRED=false."""
    return AuthContext(
        user_id="local-dev",
        companies=frozenset({"*"}),
        authorities=frozenset({"*"}),
        roles=frozenset({"LOCAL_DEV"}),
    )


def _b64url_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        return list(value)
    if isinstance(value, str):
        separator = "," if "," in value else " "
        return [part.strip() for part in value.split(separator) if part.strip()]
    return [value]


def _claim_strings(claims: dict[str, Any], *names: str) -> frozenset[str]:
    values: list[str] = []
    for name in names:
        for item in _as_list(claims.get(name)):
            if isinstance(item, dict):
                for key in ("buyer_company_uuid", "company_uuid", "uuid", "id", "name"):
                    if item.get(key):
                        values.append(str(item[key]))
                        break
            elif item is not None:
                values.append(str(item))
    return frozenset(v for v in values if v)


def _validate_registered_claims(claims: dict[str, Any]) -> None:
    now = int(time.time())
    exp = claims.get("exp")
    if exp is not None and int(exp) < now:
        raise AuthError("JWT has expired.")

    nbf = claims.get("nbf")
    if nbf is not None and int(nbf) > now:
        raise AuthError("JWT is not active yet.")

    if AUTH_JWT_ISSUER and claims.get("iss") != AUTH_JWT_ISSUER:
        raise AuthError("JWT issuer is invalid.")

    if AUTH_JWT_AUDIENCE:
        audiences = _as_list(claims.get("aud"))
        if AUTH_JWT_AUDIENCE not in {str(aud) for aud in audiences}:
            raise AuthError("JWT audience is invalid.")


def _verify_hmac_signature(signing_input: str, signature: str, algorithm: str) -> None:
    digest_name = {"HS256": "sha256", "HS384": "sha384", "HS512": "sha512"}.get(algorithm)
    if digest_name is None:
        raise AuthError(f"Unsupported JWT algorithm: {algorithm}.")
    if not AUTH_JWT_SECRET:
        raise AuthError("AUTH_JWT_SECRET is required to validate bearer tokens.")

    digest = hmac.new(
        AUTH_JWT_SECRET.encode("utf-8"),
        signing_input.encode("ascii"),
        getattr(hashlib, digest_name),
    ).digest()
    expected = _b64url_encode(digest)
    if not hmac.compare_digest(expected, signature):
        raise AuthError("JWT signature is invalid.")


def decode_jwt(token: str) -> dict[str, Any]:
    """Validate and decode a compact JWT.

    This MVP implementation supports HMAC-signed tokens because the repo has no
    crypto/JWKS dependency installed. The claim contract is the same one the
    production JWKS verifier will consume.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthError("Bearer token must be a compact JWT.")

    header_raw, payload_raw, signature = parts
    try:
        header = json.loads(_b64url_decode(header_raw))
        claims = json.loads(_b64url_decode(payload_raw))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthError("Bearer token is malformed.") from exc

    algorithm = str(header.get("alg") or "")
    if algorithm != AUTH_JWT_ALGORITHM:
        raise AuthError("JWT algorithm is not allowed.")
    if not algorithm.startswith("HS"):
        raise AuthError("Only HMAC JWT validation is available in this MVP.")

    _verify_hmac_signature(f"{header_raw}.{payload_raw}", signature, algorithm)
    _validate_registered_claims(claims)
    return claims


def context_from_claims(claims: dict[str, Any], raw_token: str | None = None) -> AuthContext:
    user_id = str(claims.get("sub") or claims.get("user_uuid") or claims.get("user_id") or "")
    if not user_id:
        raise AuthError("JWT is missing a user identifier.")

    companies = _claim_strings(
        claims,
        "companies",
        "company_uuids",
        "buyer_company_uuids",
        "buyer_company_uuid",
        "company_uuid",
    )
    authorities = _claim_strings(claims, "authorities", "permissions", "scope", "scp")
    roles = _claim_strings(claims, "roles", "role")

    return AuthContext(
        user_id=user_id,
        companies=companies,
        authorities=authorities,
        roles=roles,
        raw_token=raw_token,
        claims=claims,
    )


def decode_auth_context(token: str) -> AuthContext:
    return context_from_claims(decode_jwt(token), raw_token=token)


def _auth_http_error(exc: AuthError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=str(exc),
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthContext:
    """FastAPI dependency that binds the current user for downstream services."""
    if credentials is None:
        if AUTH_REQUIRED:
            raise _auth_http_error(AuthError("Authentication required."))
        user = development_auth_context()
    else:
        try:
            user = decode_auth_context(credentials.credentials)
        except AuthError as exc:
            raise _auth_http_error(exc) from exc

    request.state.auth = user
    _current_auth.set(user)
    return user


def ensure_authority(user: AuthContext, authority: str) -> None:
    if not user.has_authority(authority):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=UNAUTHORIZED_MODULE_MESSAGE,
        )


def require_authority(authority: str):
    async def dependency(user: AuthContext = Depends(get_current_user)) -> AuthContext:
        ensure_authority(user, authority)
        return user

    return dependency


def can_access_record(record: dict[str, Any]) -> bool:
    user = current_auth_context()
    if user is None or "*" in user.companies:
        return True
    return user.has_company(record.get("buyer_company_uuid"))


def scope_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply row-level buyer_company_uuid filtering for the active user."""
    user = current_auth_context()
    if user is None or "*" in user.companies or "buyer_company_uuid" not in df.columns:
        return df.copy()
    return df[df["buyer_company_uuid"].astype(str).isin(user.companies)].copy()


def create_test_token(claims: dict[str, Any]) -> str:
    """Small helper for backend tests and local scripts."""
    header = {"alg": AUTH_JWT_ALGORITHM, "typ": "JWT"}
    header_raw = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_raw = _b64url_encode(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
    digest_name = {"HS256": "sha256", "HS384": "sha384", "HS512": "sha512"}[AUTH_JWT_ALGORITHM]
    signature = hmac.new(
        AUTH_JWT_SECRET.encode("utf-8"),
        f"{header_raw}.{payload_raw}".encode("ascii"),
        getattr(hashlib, digest_name),
    ).digest()
    return f"{header_raw}.{payload_raw}.{_b64url_encode(signature)}"
