# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.app.views import BaseAPIView
from plane.db.models import Workspace
from plane.oneplan.models import AIActionLog, AIConversation
from plane.oneplan.services.actions.registry import execute_tool
from plane.oneplan.services.feature_flags import get_oneplan_config, is_ai_operator_enabled
from plane.oneplan.services.operator import run_operator
from plane.utils.ip_address import get_client_ip


class OnePlanConfigEndpoint(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(get_oneplan_config())


class AIChatEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug):
        if not is_ai_operator_enabled():
            return Response({"error": "AI operator not enabled"}, status=status.HTTP_403_FORBIDDEN)

        workspace = Workspace.objects.get(slug=slug)
        data = request.data
        message = data.get("message", "")
        mode = data.get("mode", AIConversation.MODE_ASK)
        conversation_id = data.get("conversation_id")
        dry_run = data.get("dry_run", mode != AIConversation.MODE_ACT)

        result = run_operator(
            user=request.user,
            workspace=workspace,
            message=message,
            mode=mode,
            conversation_id=conversation_id,
            dry_run=dry_run,
        )
        if result.get("error"):
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)


class AIActionApproveEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug):
        workspace = Workspace.objects.get(slug=slug)
        preview_id = request.data.get("preview_id")
        action_log = AIActionLog.objects.filter(
            workspace=workspace,
            preview_id=preview_id,
            status=AIActionLog.STATUS_PREVIEW,
            user=request.user,
        ).first()
        if not action_log:
            return Response({"error": "Preview not found"}, status=status.HTTP_404_NOT_FOUND)

        result = execute_tool(
            action_log.action_type,
            action_log.payload,
            request.user,
            workspace,
            dry_run=False,
        )
        action_log.status = AIActionLog.STATUS_EXECUTED if not result.get("error") else AIActionLog.STATUS_FAILED
        action_log.result = result
        action_log.dry_run = False
        action_log.approved_by = request.user
        action_log.ip_address = get_client_ip(request)
        action_log.save()

        return Response({"executed": True, "result": result, "action_log_id": str(action_log.id)})


class AIConversationListEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        conversations = AIConversation.objects.filter(
            workspace__slug=slug, user=request.user
        ).values("id", "title", "mode", "created_at")[:50]
        return Response({"conversations": list(conversations)})


class AIActionLogEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        logs = AIActionLog.objects.filter(workspace__slug=slug).values(
            "id", "action_type", "status", "summary", "dry_run", "created_at", "user_id"
        )[:100]
        return Response({"logs": list(logs)})
