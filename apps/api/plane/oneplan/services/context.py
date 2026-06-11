# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from plane.db.models import Issue, Project, State, Workspace, WorkspaceMember
from plane.oneplan.models import Constraint, Objective


def get_workspace_context(workspace: Workspace, max_issues: int = 50) -> dict:
    """Build read-only workspace context for AI."""
    projects = list(
        Project.objects.filter(workspace=workspace)
        .values("id", "name", "identifier")[:20]
    )
    members = list(
        WorkspaceMember.objects.filter(workspace=workspace, is_active=True)
        .select_related("member")
        .values("member_id", "member__display_name", "role")[:30]
    )
    stale_cutoff = timezone.now() - timedelta(days=14)
    stale_issues = list(
        Issue.objects.filter(workspace=workspace, updated_at__lt=stale_cutoff)
        .exclude(state__group="completed")
        .values("id", "name", "project_id", "updated_at")[:10]
    )
    overdue = list(
        Issue.objects.filter(
            workspace=workspace,
            target_date__lt=timezone.now().date(),
        )
        .exclude(state__group="completed")
        .values("id", "name", "project_id", "target_date")[:10]
    )
    overloaded = (
        Issue.objects.filter(workspace=workspace)
        .exclude(state__group="completed")
        .values("assignees__id", "assignees__display_name")
        .annotate(count=Count("id"))
        .filter(count__gt=5)
        .order_by("-count")[:5]
    )
    context: dict = {
        "workspace": {"id": str(workspace.id), "name": workspace.name, "slug": workspace.slug},
        "projects": projects,
        "member_count": len(members),
        "stale_issues": stale_issues,
        "overdue_issues": overdue,
        "overloaded_assignees": list(overloaded),
    }
    try:
        context["top_constraints"] = list(
            Constraint.objects.filter(workspace=workspace)
            .exclude(status=Constraint.STATUS_RESOLVED)
            .values("id", "title", "status", "priority_score")[:10]
        )
        context["objectives"] = list(
            Objective.objects.filter(workspace=workspace, status=Objective.STATUS_ACTIVE).values(
                "id", "title", "status"
            )[:10]
        )
    except Exception:
        pass
    return context


def workspace_summary_text(workspace: Workspace) -> str:
    ctx = get_workspace_context(workspace)
    lines = [
        f"Workspace: {ctx['workspace']['name']}",
        f"Projects: {len(ctx['projects'])}",
        f"Overdue tasks: {len(ctx['overdue_issues'])}",
        f"Stale tasks (14+ days): {len(ctx['stale_issues'])}",
    ]
    if ctx.get("top_constraints"):
        lines.append("Top constraints:")
        for c in ctx["top_constraints"][:5]:
            lines.append(f"  - [{c['priority_score']:.1f}] {c['title']} ({c['status']})")
    return "\n".join(lines)
