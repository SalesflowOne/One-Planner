# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

import json
import uuid
from typing import Any

from django.utils import timezone

from plane.app.permissions import ROLE
from plane.app.serializers import IssueCreateSerializer
from plane.db.models import Issue, IssueAssignee, IssueComment, Project, ProjectMember, State, Workspace, WorkspaceMember
from plane.oneplan.models import AIActionLog, Constraint, ConstraintIssueLink, Objective
from plane.oneplan.services.context import get_workspace_context, workspace_summary_text
from plane.oneplan.services.feature_flags import is_pipedream_connectors_enabled
from plane.oneplan.services.pipedream_mcp import (
    get_connect_instructions,
    is_pipedream_configured,
    list_connector_apps,
    run_connector_tool,
)
from plane.utils.exception_logger import log_exception


RISK_LEVELS = {
    "search_tasks": "low",
    "get_task": "low",
    "list_projects": "low",
    "get_workspace_summary": "low",
    "find_stale_tasks": "low",
    "find_overloaded_assignees": "low",
    "list_constraints": "low",
    "rank_constraints": "low",
    "create_task": "low",
    "update_task": "medium",
    "move_task_state": "medium",
    "assign_task": "medium",
    "add_comment": "low",
    "create_project": "medium",
    "create_objective": "low",
    "create_constraint": "low",
    "link_task_to_constraint": "low",
    "mark_constraint_resolved": "medium",
    "generate_execution_plan": "low",
    "list_connectors": "low",
    "run_connector": "medium",
}

READ_TOOLS = {
    "search_tasks",
    "get_task",
    "list_projects",
    "get_workspace_summary",
    "find_stale_tasks",
    "find_overloaded_assignees",
    "list_constraints",
    "rank_constraints",
    "summarize_workspace",
    "get_daily_priorities",
    "list_connectors",
}


def _check_workspace_member(user, workspace: Workspace, min_role: int = ROLE.GUEST.value) -> bool:
    return WorkspaceMember.objects.filter(
        member=user, workspace=workspace, is_active=True, role__gte=min_role
    ).exists()


def _check_project_member(user, workspace: Workspace, project_id: str, min_role: int = ROLE.MEMBER.value) -> bool:
    if ProjectMember.objects.filter(
        member=user,
        workspace=workspace,
        project_id=project_id,
        is_active=True,
        role__gte=min_role,
    ).exists():
        return True
    return (
        WorkspaceMember.objects.filter(
            member=user, workspace=workspace, is_active=True, role=ROLE.ADMIN.value
        ).exists()
        and ProjectMember.objects.filter(
            member=user, workspace=workspace, project_id=project_id, is_active=True
        ).exists()
    )


def execute_tool(
    tool_name: str,
    arguments: dict,
    user,
    workspace: Workspace,
    dry_run: bool = True,
) -> dict[str, Any]:
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    if tool_name not in READ_TOOLS and not _check_workspace_member(user, workspace, ROLE.MEMBER.value):
        return {"error": "Permission denied"}
    try:
        return handler(user=user, workspace=workspace, dry_run=dry_run, **arguments)
    except Exception as e:
        log_exception(e)
        return {"error": str(e)}


def _search_tasks(user, workspace, dry_run, query="", project_id=None, limit=20, **_) -> dict:
    qs = Issue.objects.filter(workspace=workspace)
    if project_id:
        qs = qs.filter(project_id=project_id)
    if query:
        qs = qs.filter(name__icontains=query)
    items = list(qs.values("id", "name", "project_id", "state_id", "priority")[:limit])
    return {"tasks": items, "count": len(items)}


def _get_task(user, workspace, dry_run, task_id, **_) -> dict:
    issue = Issue.objects.filter(workspace=workspace, id=task_id).first()
    if not issue:
        return {"error": "Task not found"}
    return {
        "task": {
            "id": str(issue.id),
            "name": issue.name,
            "description_html": issue.description_html,
            "state_id": str(issue.state_id) if issue.state_id else None,
            "priority": issue.priority,
            "project_id": str(issue.project_id),
        }
    }


def _list_projects(user, workspace, dry_run, **_) -> dict:
    projects = list(Project.objects.filter(workspace=workspace).values("id", "name", "identifier"))
    return {"projects": projects}


def _get_workspace_summary(user, workspace, dry_run, **_) -> dict:
    return {"summary": workspace_summary_text(workspace), "context": get_workspace_context(workspace)}


def _find_stale_tasks(user, workspace, dry_run, days=14, **_) -> dict:
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=days)
    items = list(
        Issue.objects.filter(workspace=workspace, updated_at__lt=cutoff)
        .exclude(state__group="completed")
        .values("id", "name", "updated_at")[:20]
    )
    return {"stale_tasks": items}


def _find_overloaded_assignees(user, workspace, dry_run, **_) -> dict:
    from django.db.models import Count

    data = list(
        Issue.objects.filter(workspace=workspace)
        .exclude(state__group="completed")
        .values("assignees__display_name")
        .annotate(open_count=Count("id"))
        .order_by("-open_count")[:10]
    )
    return {"assignees": data}


def _list_constraints(user, workspace, dry_run, status=None, **_) -> dict:
    qs = Constraint.objects.filter(workspace=workspace)
    if status:
        qs = qs.filter(status=status)
    items = list(qs.values("id", "title", "status", "priority_score", "objective_id")[:50])
    return {"constraints": items}


def _rank_constraints(user, workspace, dry_run, **_) -> dict:
    items = list(
        Constraint.objects.filter(workspace=workspace)
        .exclude(status=Constraint.STATUS_RESOLVED)
        .order_by("-priority_score")
        .values("id", "title", "status", "priority_score", "priority_factors")[:20]
    )
    return {"ranked_constraints": items}


def _summarize_workspace(user, workspace, dry_run, **_) -> dict:
    return _get_workspace_summary(user, workspace, dry_run)


def _get_daily_priorities(user, workspace, dry_run, **_) -> dict:
    overdue = list(
        Issue.objects.filter(workspace=workspace, target_date__lte=timezone.now().date())
        .exclude(state__group="completed")
        .values("id", "name", "target_date", "priority")[:10]
    )
    constraints = list(
        Constraint.objects.filter(workspace=workspace, status=Constraint.STATUS_ACTIVE)
        .order_by("-priority_score")
        .values("id", "title", "priority_score")[:5]
    )
    return {"overdue_tasks": overdue, "top_constraints": constraints}


def _create_task(user, workspace, dry_run, project_id, name, description_html="", priority="none", state_id=None, **_) -> dict:
    if not _check_project_member(user, workspace, project_id):
        return {"error": "Permission denied for project"}
    payload = {"name": name, "description_html": description_html or "", "priority": priority}
    if state_id:
        payload["state_id"] = state_id
    if dry_run:
        return {"preview": True, "action": "create_task", "payload": {"project_id": project_id, **payload}}
    serializer = IssueCreateSerializer(
        data=payload,
        context={"project_id": project_id, "workspace_id": workspace.id},
    )
    if not serializer.is_valid():
        return {"error": serializer.errors}
    issue = serializer.save()
    return {"created": True, "task_id": str(issue.id), "name": issue.name}


def _update_task(user, workspace, dry_run, task_id, **fields) -> dict:
    issue = Issue.objects.filter(workspace=workspace, id=task_id).first()
    if not issue:
        return {"error": "Task not found"}
    if not _check_project_member(user, workspace, str(issue.project_id)):
        return {"error": "Permission denied"}
    allowed = {k: v for k, v in fields.items() if k in ("name", "description_html", "priority", "target_date")}
    if dry_run:
        return {"preview": True, "action": "update_task", "task_id": task_id, "changes": allowed}
    for k, v in allowed.items():
        setattr(issue, k, v)
    issue.save()
    return {"updated": True, "task_id": task_id}


def _move_task_state(user, workspace, dry_run, task_id, state_id, **_) -> dict:
    issue = Issue.objects.filter(workspace=workspace, id=task_id).first()
    if not issue:
        return {"error": "Task not found"}
    if not _check_project_member(user, workspace, str(issue.project_id)):
        return {"error": "Permission denied"}
    state = State.objects.filter(project_id=issue.project_id, id=state_id).first()
    if not state:
        return {"error": "State not found"}
    if dry_run:
        return {"preview": True, "action": "move_task_state", "task_id": task_id, "state_id": state_id}
    issue.state = state
    issue.save()
    return {"updated": True, "task_id": task_id, "state_id": state_id}


def _assign_task(user, workspace, dry_run, task_id, assignee_ids, **_) -> dict:
    issue = Issue.objects.filter(workspace=workspace, id=task_id).first()
    if not issue:
        return {"error": "Task not found"}
    if not _check_project_member(user, workspace, str(issue.project_id)):
        return {"error": "Permission denied"}
    if dry_run:
        return {"preview": True, "action": "assign_task", "task_id": task_id, "assignee_ids": assignee_ids}
    IssueAssignee.objects.filter(issue=issue).delete()
    for aid in assignee_ids:
        IssueAssignee.objects.create(issue=issue, assignee_id=aid, project=issue.project, workspace=workspace)
    return {"assigned": True, "task_id": task_id}


def _add_comment(user, workspace, dry_run, task_id, comment_html, **_) -> dict:
    issue = Issue.objects.filter(workspace=workspace, id=task_id).first()
    if not issue:
        return {"error": "Task not found"}
    if not _check_project_member(user, workspace, str(issue.project_id)):
        return {"error": "Permission denied"}
    if dry_run:
        return {"preview": True, "action": "add_comment", "task_id": task_id}
    comment = IssueComment.objects.create(
        issue=issue,
        project=issue.project,
        workspace=workspace,
        comment_html=comment_html,
        actor=user,
    )
    return {"created": True, "comment_id": str(comment.id)}


def _create_project(user, workspace, dry_run, name, identifier, **_) -> dict:
    if not _check_workspace_member(user, workspace, ROLE.MEMBER.value):
        return {"error": "Permission denied"}
    if dry_run:
        return {"preview": True, "action": "create_project", "name": name, "identifier": identifier}
    project = Project.objects.create(
        workspace=workspace,
        name=name,
        identifier=identifier.upper()[:6],
        created_by=user,
    )
    ProjectMember.objects.create(
        project=project,
        workspace=workspace,
        member=user,
        role=ROLE.ADMIN.value,
    )
    return {"created": True, "project_id": str(project.id)}


def _create_objective(user, workspace, dry_run, title, description="", pillar_id=None, **_) -> dict:
    if dry_run:
        return {"preview": True, "action": "create_objective", "title": title}
    obj = Objective.objects.create(
        workspace=workspace,
        title=title,
        description=description,
        pillar_id=pillar_id,
        owner=user,
    )
    return {"created": True, "objective_id": str(obj.id)}


def _create_constraint(user, workspace, dry_run, title, description="", objective_id=None, pillar_id=None, **_) -> dict:
    if dry_run:
        return {"preview": True, "action": "create_constraint", "title": title}
    c = Constraint.objects.create(
        workspace=workspace,
        title=title,
        description=description,
        objective_id=objective_id,
        pillar_id=pillar_id,
        owner=user,
        status=Constraint.STATUS_IDENTIFIED,
    )
    return {"created": True, "constraint_id": str(c.id)}


def _link_task_to_constraint(user, workspace, dry_run, constraint_id, task_id, **_) -> dict:
    if dry_run:
        return {"preview": True, "action": "link_task_to_constraint", "constraint_id": constraint_id, "task_id": task_id}
    link, _ = ConstraintIssueLink.objects.get_or_create(
        constraint_id=constraint_id,
        issue_id=task_id,
    )
    return {"linked": True, "link_id": str(link.id)}


def _mark_constraint_resolved(user, workspace, dry_run, constraint_id, **_) -> dict:
    c = Constraint.objects.filter(workspace=workspace, id=constraint_id).first()
    if not c:
        return {"error": "Constraint not found"}
    if dry_run:
        return {"preview": True, "action": "mark_constraint_resolved", "constraint_id": constraint_id}
    c.status = Constraint.STATUS_RESOLVED
    c.resolved_at = timezone.now()
    c.save()
    return {"resolved": True, "constraint_id": constraint_id}


def _list_connectors(user, workspace, dry_run, **_) -> dict:
    if not is_pipedream_connectors_enabled():
        return {"error": "Pipedream connectors not enabled"}
    if not is_pipedream_configured():
        return {"error": "Pipedream MCP not configured", "apps": []}
    return {"apps": list_connector_apps()}


def _run_connector(user, workspace, dry_run, app_slug, tool_name, arguments=None, **_) -> dict:
    if not is_pipedream_connectors_enabled():
        return {"error": "Pipedream connectors not enabled"}
    if not is_pipedream_configured():
        return {"error": "Pipedream MCP not configured"}
    if dry_run:
        return {
            "preview": True,
            "action": "run_connector",
            "app_slug": app_slug,
            "tool_name": tool_name,
            "arguments": arguments or {},
        }
    external_user_id = f"oneplan-{user.id}"
    result = run_connector_tool(external_user_id, app_slug, tool_name, arguments or {})
    if result.get("error"):
        return {**result, **get_connect_instructions(app_slug)}
    return result


def _generate_execution_plan(user, workspace, dry_run, constraint_id, **_) -> dict:
    c = Constraint.objects.filter(workspace=workspace, id=constraint_id).first()
    if not c:
        return {"error": "Constraint not found"}
    linked = list(
        ConstraintIssueLink.objects.filter(constraint=c).values_list("issue__name", flat=True)
    )
    plan = {
        "constraint": c.title,
        "steps": [
            f"Clarify scope: {c.description or c.title}",
            "Assign owner and set deadline",
            "Break into 3-5 actionable tasks",
            "Link tasks to this constraint",
            "Review weekly until resolved",
        ],
        "linked_tasks": linked,
    }
    return {"plan": plan, "dry_run": dry_run}


TOOL_DEFINITIONS = [
    {"type": "function", "function": {"name": "search_tasks", "description": "Search work items in workspace", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "project_id": {"type": "string"}, "limit": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_task", "description": "Get task details", "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "list_projects", "description": "List projects", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_workspace_summary", "description": "Summarize workspace state", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "list_constraints", "description": "List constraints", "parameters": {"type": "object", "properties": {"status": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "rank_constraints", "description": "Rank constraints by priority", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "create_task", "description": "Create a work item", "parameters": {"type": "object", "properties": {"project_id": {"type": "string"}, "name": {"type": "string"}, "description_html": {"type": "string"}, "priority": {"type": "string"}}, "required": ["project_id", "name"]}}},
    {"type": "function", "function": {"name": "update_task", "description": "Update a work item", "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}, "name": {"type": "string"}, "priority": {"type": "string"}}, "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "move_task_state", "description": "Move task to a state", "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}, "state_id": {"type": "string"}}, "required": ["task_id", "state_id"]}}},
    {"type": "function", "function": {"name": "assign_task", "description": "Assign task to users", "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}, "assignee_ids": {"type": "array", "items": {"type": "string"}}}, "required": ["task_id", "assignee_ids"]}}},
    {"type": "function", "function": {"name": "add_comment", "description": "Add comment to task", "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}, "comment_html": {"type": "string"}}, "required": ["task_id", "comment_html"]}}},
    {"type": "function", "function": {"name": "create_constraint", "description": "Create a constraint", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "description": {"type": "string"}, "objective_id": {"type": "string"}}, "required": ["title"]}}},
    {"type": "function", "function": {"name": "link_task_to_constraint", "description": "Link task to constraint", "parameters": {"type": "object", "properties": {"constraint_id": {"type": "string"}, "task_id": {"type": "string"}}, "required": ["constraint_id", "task_id"]}}},
    {"type": "function", "function": {"name": "mark_constraint_resolved", "description": "Mark constraint resolved", "parameters": {"type": "object", "properties": {"constraint_id": {"type": "string"}}, "required": ["constraint_id"]}}},
    {"type": "function", "function": {"name": "generate_execution_plan", "description": "Generate plan to resolve constraint", "parameters": {"type": "object", "properties": {"constraint_id": {"type": "string"}}, "required": ["constraint_id"]}}},
    {"type": "function", "function": {"name": "list_connectors", "description": "List Pipedream MCP connector apps available", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "run_connector", "description": "Run a Pipedream MCP connector tool (Slack, GitHub, etc.)", "parameters": {"type": "object", "properties": {"app_slug": {"type": "string"}, "tool_name": {"type": "string"}, "arguments": {"type": "object"}}, "required": ["app_slug", "tool_name"]}}},
]

TOOL_HANDLERS = {
    "search_tasks": _search_tasks,
    "get_task": _get_task,
    "list_projects": _list_projects,
    "get_workspace_summary": _get_workspace_summary,
    "find_stale_tasks": _find_stale_tasks,
    "find_overloaded_assignees": _find_overloaded_assignees,
    "list_constraints": _list_constraints,
    "rank_constraints": _rank_constraints,
    "summarize_workspace": _summarize_workspace,
    "get_daily_priorities": _get_daily_priorities,
    "create_task": _create_task,
    "update_task": _update_task,
    "move_task_state": _move_task_state,
    "assign_task": _assign_task,
    "add_comment": _add_comment,
    "create_project": _create_project,
    "create_objective": _create_objective,
    "create_constraint": _create_constraint,
    "link_task_to_constraint": _link_task_to_constraint,
    "mark_constraint_resolved": _mark_constraint_resolved,
    "generate_execution_plan": _generate_execution_plan,
    "list_connectors": _list_connectors,
    "run_connector": _run_connector,
}


def log_action(user, workspace, action_type, payload, result, dry_run, status, summary="", preview_id=None):
    return AIActionLog.objects.create(
        user=user,
        workspace=workspace,
        action_type=action_type,
        payload=payload,
        result=result,
        dry_run=dry_run,
        status=status,
        risk_level=RISK_LEVELS.get(action_type, "medium"),
        summary=summary,
        preview_id=preview_id or uuid.uuid4(),
    )
