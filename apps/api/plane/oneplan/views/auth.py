# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from plane.app.views import BaseAPIView
from plane.authentication.utils.login import user_login
from plane.oneplan.services.feature_flags import is_supabase_auth_enabled
from plane.oneplan.services.supabase_auth import get_or_create_user_from_supabase, validate_supabase_jwt


class SupabaseAuthEndpoint(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not is_supabase_auth_enabled():
            return Response({"error": "Supabase auth not enabled"}, status=status.HTTP_403_FORBIDDEN)

        token = request.data.get("access_token") or request.data.get("token")
        if not token:
            return Response({"error": "Missing access_token"}, status=status.HTTP_400_BAD_REQUEST)

        payload = validate_supabase_jwt(token)
        if not payload:
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

        user = get_or_create_user_from_supabase(payload)
        if not user:
            return Response({"error": "Could not provision user"}, status=status.HTTP_400_BAD_REQUEST)

        user_login(request, user, is_app=True)
        return Response({
            "success": True,
            "user_id": str(user.id),
            "email": user.email,
        })
