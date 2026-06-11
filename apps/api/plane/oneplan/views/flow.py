# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from django.db.models import Count
from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.app.views import BaseAPIView
from plane.db.models import Issue, Workspace
from plane.oneplan.models import Constraint, ConstraintIssueLink, Objective, Pillar
from plane.oneplan.serializers.flow import (
    ConstraintIssueLinkSerializer,
    ConstraintSerializer,
    ObjectiveSerializer,
    PillarSerializer,
)
from plane.oneplan.services.feature_flags import is_flow_constraints_enabled


DEFAULT_PILLARS = [
    {"name": "Security", "color": "#22c55e", "sort_order": 0},
    {"name": "Evolution", "color": "#3b82f6", "sort_order": 1},
    {"name": "Legacy", "color": "#a855f7", "sort_order": 2},
]


def ensure_default_pillars(workspace: Workspace):
    if Pillar.objects.filter(workspace=workspace).exists():
        return
    for p in DEFAULT_PILLARS:
        Pillar.objects.create(workspace=workspace, **p)


def compute_priority_score(constraint: Constraint) -> float:
    factors = constraint.priority_factors or {}
    urgency = float(factors.get("urgency", 0.5))
    leverage = float(factors.get("leverage", 0.5))
    dependency = float(factors.get("dependency", 0.5))
    cash_impact = float(factors.get("cash_impact", 0.5))
    time_sensitivity = float(factors.get("time_sensitivity", 0.5))
    return round(urgency * leverage * dependency * cash_impact * time_sensitivity * 100, 2)


class PillarListEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def get(self, request, slug):
        workspace = Workspace.objects.get(slug=slug)
        ensure_default_pillars(workspace)
        pillars = PillarSerializer(Pillar.objects.filter(workspace=workspace), many=True)
        return Response(pillars.data)


class ObjectiveEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def get(self, request, slug):
        objs = Objective.objects.filter(workspace__slug=slug)
        return Response(ObjectiveSerializer(objs, many=True).data)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug):
        workspace = Workspace.objects.get(slug=slug)
        serializer = ObjectiveSerializer(data={**request.data, "workspace": workspace.id})
        serializer.is_valid(raise_exception=True)
        serializer.save(workspace=workspace)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ObjectiveDetailEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def patch(self, request, slug, objective_id):
        obj = Objective.objects.get(workspace__slug=slug, id=objective_id)
        serializer = ObjectiveSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ConstraintEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def get(self, request, slug):
        if not is_flow_constraints_enabled():
            return Response({"error": "Flow & Constraints not enabled"}, status=status.HTTP_403_FORBIDDEN)
        qs = Constraint.objects.filter(workspace__slug=slug)
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(ConstraintSerializer(qs, many=True).data)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug):
        workspace = Workspace.objects.get(slug=slug)
        data = {**request.data, "workspace": workspace.id}
        serializer = ConstraintSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        constraint = serializer.save(workspace=workspace, owner=request.user)
        constraint.priority_score = compute_priority_score(constraint)
        constraint.save(update_fields=["priority_score"])
        return Response(ConstraintSerializer(constraint).data, status=status.HTTP_201_CREATED)


class ConstraintDetailEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def patch(self, request, slug, constraint_id):
        c = Constraint.objects.get(workspace__slug=slug, id=constraint_id)
        serializer = ConstraintSerializer(c, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        constraint = serializer.save()
        constraint.priority_score = compute_priority_score(constraint)
        if request.data.get("status") == Constraint.STATUS_RESOLVED:
            constraint.resolved_at = timezone.now()
        constraint.save()
        return Response(ConstraintSerializer(constraint).data)


class ConstraintRankEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def get(self, request, slug):
        items = (
            Constraint.objects.filter(workspace__slug=slug)
            .exclude(status=Constraint.STATUS_RESOLVED)
            .order_by("-priority_score")
        )
        return Response(ConstraintSerializer(items, many=True).data)


class ConstraintLinkEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, constraint_id):
        link = ConstraintIssueLink.objects.create(
            constraint_id=constraint_id,
            issue_id=request.data.get("issue_id"),
        )
        return Response(ConstraintIssueLinkSerializer(link).data, status=status.HTTP_201_CREATED)


class ConstraintDashboardEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def get(self, request, slug):
        workspace = Workspace.objects.get(slug=slug)
        ensure_default_pillars(workspace)
        top_constraints = list(
            Constraint.objects.filter(workspace=workspace)
            .exclude(status=Constraint.STATUS_RESOLVED)
            .order_by("-priority_score")[:10]
            .values("id", "title", "status", "priority_score", "owner_id")
        )
        overdue = list(
            Issue.objects.filter(workspace=workspace, target_date__lt=timezone.now().date())
            .exclude(state__group="completed")
            .values("id", "name", "target_date")[:10]
        )
        stuck = list(
            Issue.objects.filter(workspace=workspace, state__group="started")
            .values("id", "name", "updated_at")[:10]
        )
        return Response({
            "top_constraints": top_constraints,
            "overdue_tasks": overdue,
            "stuck_tasks": stuck,
            "active_objectives": Objective.objects.filter(
                workspace=workspace, status=Objective.STATUS_ACTIVE
            ).count(),
        })


class CommandCenterEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        workspace = Workspace.objects.get(slug=slug)
        from plane.oneplan.services.actions.registry import _get_daily_priorities

        daily = _get_daily_priorities(request.user, workspace, dry_run=True)
        dashboard = ConstraintDashboardEndpoint()
        dashboard.request = request
        dash_data = dashboard.get(request, slug).data
        return Response({
            **dash_data,
            **daily,
            "attention_summary": f"{len(dash_data.get('overdue_tasks', []))} overdue, {len(dash_data.get('top_constraints', []))} active constraints",
        })
