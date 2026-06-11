# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.app.views import BaseAPIView
from plane.oneplan.services.feature_flags import is_ai_operator_enabled, is_oneplan_enabled
from plane.oneplan.services.pipedream_mcp import (
    get_connect_instructions,
    is_pipedream_configured,
    list_connector_apps,
    list_connector_tools,
    run_connector_tool,
)


class ConnectorsStatusEndpoint(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "enabled": is_oneplan_enabled() and is_ai_operator_enabled(),
                "pipedream_configured": is_pipedream_configured(),
            }
        )


class ConnectorsAppsEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        if not is_oneplan_enabled():
            return Response({"error": "OnePlan not enabled"}, status=status.HTTP_403_FORBIDDEN)
        return Response({"apps": list_connector_apps()})


class ConnectorsToolsEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        app_slug = request.query_params.get("app")
        if not app_slug:
            return Response({"error": "app query param required"}, status=status.HTTP_400_BAD_REQUEST)
        external_user_id = f"oneplan-{request.user.id}"
        result = list_connector_tools(external_user_id, app_slug)
        if result.get("error"):
            return Response({**result, **get_connect_instructions(app_slug)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)


class ConnectorsRunEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug):
        if not is_ai_operator_enabled():
            return Response({"error": "AI operator not enabled"}, status=status.HTTP_403_FORBIDDEN)
        app_slug = request.data.get("app_slug")
        tool_name = request.data.get("tool_name")
        arguments = request.data.get("arguments", {})
        if not app_slug or not tool_name:
            return Response({"error": "app_slug and tool_name required"}, status=status.HTTP_400_BAD_REQUEST)
        external_user_id = f"oneplan-{request.user.id}"
        result = run_connector_tool(external_user_id, app_slug, tool_name, arguments)
        if result.get("error"):
            return Response({**result, **get_connect_instructions(app_slug)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)
