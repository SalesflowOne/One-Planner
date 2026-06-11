# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from rest_framework import status
from rest_framework.response import Response

from plane.api.views.base import BaseAPIView
from plane.db.models import Workspace
from plane.oneplan.models import Constraint, Objective
from plane.oneplan.serializers.flow import ConstraintSerializer, ObjectiveSerializer
from plane.oneplan.services.actions.registry import TOOL_HANDLERS, execute_tool
from plane.oneplan.services.context import workspace_summary_text


class ExternalWorkspaceSummaryEndpoint(BaseAPIView):
    def get(self, request, workspace_slug):
        workspace = Workspace.objects.get(slug=workspace_slug)
        return Response({"summary": workspace_summary_text(workspace)})


class ExternalConstraintListEndpoint(BaseAPIView):
    def get(self, request, workspace_slug):
        items = Constraint.objects.filter(workspace__slug=workspace_slug).exclude(
            status=Constraint.STATUS_RESOLVED
        ).order_by("-priority_score")
        return Response(ConstraintSerializer(items, many=True).data)


class ExternalObjectiveListEndpoint(BaseAPIView):
    def get(self, request, workspace_slug):
        items = Objective.objects.filter(workspace__slug=workspace_slug)
        return Response(ObjectiveSerializer(items, many=True).data)


class ExternalToolExecuteEndpoint(BaseAPIView):
    def post(self, request, workspace_slug):
        workspace = Workspace.objects.get(slug=workspace_slug)
        tool_name = request.data.get("tool")
        arguments = request.data.get("arguments", {})
        dry_run = request.data.get("dry_run", True)
        if tool_name not in TOOL_HANDLERS:
            return Response({"error": "Unknown tool"}, status=status.HTTP_400_BAD_REQUEST)
        result = execute_tool(tool_name, arguments, request.user, workspace, dry_run=dry_run)
        return Response(result)
