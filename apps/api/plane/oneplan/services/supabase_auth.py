# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

import os
from typing import Any

import jwt
import requests

from django.contrib.auth import get_user_model
from django.utils import timezone

from plane.db.models import Profile
from plane.oneplan.models import ExternalIdentity
from plane.oneplan.services.feature_flags import is_supabase_auth_enabled
from plane.utils.exception_logger import log_exception

User = get_user_model()


def get_supabase_config() -> tuple[str | None, str | None]:
    url = os.environ.get("SUPABASE_URL")
    secret = os.environ.get("SUPABASE_JWT_SECRET")
    return url, secret


def validate_supabase_jwt(token: str) -> dict[str, Any] | None:
    if not is_supabase_auth_enabled():
        return None
    _, secret = get_supabase_config()
    if not secret:
        return None
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_aud": True},
        )
        return payload
    except jwt.PyJWTError as e:
        log_exception(e)
        return None


def get_or_create_user_from_supabase(payload: dict) -> User | None:
    external_id = payload.get("sub")
    email = (payload.get("email") or "").lower().strip()
    if not external_id:
        return None

    identity = ExternalIdentity.objects.filter(
        provider=ExternalIdentity.PROVIDER_SUPABASE,
        external_id=external_id,
    ).select_related("user").first()

    if identity:
        return identity.user

    user = None
    if email:
        user = User.objects.filter(email=email).first()

    if not user:
        username = email or f"supabase_{external_id[:8]}"
        user = User.objects.create(
            email=email or None,
            username=username,
            display_name=payload.get("user_metadata", {}).get("full_name", email or username),
            is_active=True,
        )
        Profile.objects.get_or_create(user=user)

    ExternalIdentity.objects.create(
        user=user,
        provider=ExternalIdentity.PROVIDER_SUPABASE,
        external_id=external_id,
        email=email,
        metadata={"user_metadata": payload.get("user_metadata", {})},
    )
    return user
