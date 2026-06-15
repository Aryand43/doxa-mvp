"""Authentication endpoints."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from fastapi import HTTPException, status
from pydantic import BaseModel

from backend.auth import AuthContext, create_test_token, get_current_user
from backend.config import AUTH_DEV_LOGIN_ENABLED, AUTH_JWT_SECRET, AUTH_TOKEN_TTL_SECONDS
from backend.data_access import loader

router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthInfo(BaseModel):
    user_id: str
    companies: list[str]
    authorities: list[str]
    roles: list[str]
    auth_required: bool


class DevTenant(BaseModel):
    buyer_company_uuid: str
    entity_name: str
    tenant_code: str


class DevAccessProfile(BaseModel):
    id: str
    label: str
    authorities: list[str]
    roles: list[str]


class DevLoginOptions(BaseModel):
    tenants: list[DevTenant]
    profiles: list[DevAccessProfile]


class DevLoginRequest(BaseModel):
    user_id: str = "demo-user"
    buyer_company_uuid: str
    profile_id: str = "executive"


class DevLoginResponse(BaseModel):
    token: str
    expires_at: int
    user: AuthInfo


_ACCESS_PROFILES: dict[str, DevAccessProfile] = {
    "executive": DevAccessProfile(
        id="executive",
        label="Executive",
        authorities=["AI:read", "REPORT:read", "CRAWLER:read"],
        roles=["EXEC"],
    ),
    "assistant": DevAccessProfile(
        id="assistant",
        label="Assistant only",
        authorities=["AI:read"],
        roles=["USER"],
    ),
    "reports": DevAccessProfile(
        id="reports",
        label="Reports only",
        authorities=["REPORT:read"],
        roles=["ANALYST"],
    ),
    "crawler": DevAccessProfile(
        id="crawler",
        label="Crawler only",
        authorities=["CRAWLER:read"],
        roles=["RISK_REVIEWER"],
    ),
}


def _dev_login_available() -> None:
    if not AUTH_DEV_LOGIN_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Development login is disabled.",
        )
    if not AUTH_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AUTH_JWT_SECRET must be configured before issuing login tokens.",
        )


def _tenants() -> list[DevTenant]:
    entities = loader.load("entities")
    return [
        DevTenant(
            buyer_company_uuid=str(row["buyer_company_uuid"]),
            entity_name=str(row["entity_name"]),
            tenant_code=str(row.get("tenant_code", "")),
        )
        for _, row in entities.iterrows()
    ]


def _auth_info_from_claims(claims: dict) -> AuthInfo:
    return AuthInfo(
        user_id=str(claims["sub"]),
        companies=[str(claims["companies"][0])],
        authorities=list(claims["authorities"]),
        roles=list(claims["roles"]),
        auth_required=True,
    )


@router.get("/me", response_model=AuthInfo)
async def me(user: AuthContext = Depends(get_current_user)) -> AuthInfo:
    return AuthInfo(
        user_id=user.user_id,
        companies=sorted(user.companies),
        authorities=sorted(user.authorities),
        roles=sorted(user.roles),
        auth_required=not user.is_development_bypass,
    )


@router.get("/dev-options", response_model=DevLoginOptions)
async def dev_options() -> DevLoginOptions:
    _dev_login_available()
    return DevLoginOptions(
        tenants=_tenants(),
        profiles=list(_ACCESS_PROFILES.values()),
    )


@router.post("/dev-login", response_model=DevLoginResponse)
async def dev_login(body: DevLoginRequest) -> DevLoginResponse:
    _dev_login_available()
    tenant_ids = {tenant.buyer_company_uuid for tenant in _tenants()}
    if body.buyer_company_uuid not in tenant_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown tenant.")

    profile = _ACCESS_PROFILES.get(body.profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown access profile.")

    expires_at = int(time.time()) + AUTH_TOKEN_TTL_SECONDS
    claims = {
        "sub": body.user_id.strip() or "demo-user",
        "companies": [body.buyer_company_uuid],
        "authorities": profile.authorities,
        "roles": profile.roles,
        "exp": expires_at,
    }
    return DevLoginResponse(
        token=create_test_token(claims),
        expires_at=expires_at,
        user=_auth_info_from_claims(claims),
    )
