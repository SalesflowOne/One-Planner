# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from django.urls import path

from plane.oneplan.views.auth import SupabaseAuthEndpoint
from plane.oneplan.views.chat import (
    AIActionApproveEndpoint,
    AIActionLogEndpoint,
    AIChatEndpoint,
    AIConversationListEndpoint,
    OnePlanConfigEndpoint,
)
from plane.oneplan.views.connectors import (
    ConnectorsAppsEndpoint,
    ConnectorsRunEndpoint,
    ConnectorsStatusEndpoint,
    ConnectorsToolsEndpoint,
)
from plane.oneplan.views.flow import (
    CommandCenterEndpoint,
    ConstraintDashboardEndpoint,
    ConstraintDetailEndpoint,
    ConstraintEndpoint,
    ConstraintLinkEndpoint,
    ConstraintRankEndpoint,
    ObjectiveDetailEndpoint,
    ObjectiveEndpoint,
    PillarListEndpoint,
)

urlpatterns = [
    path("config/", OnePlanConfigEndpoint.as_view(), name="oneplan-config"),
    path("workspaces/<str:slug>/chat/", AIChatEndpoint.as_view(), name="oneplan-chat"),
    path("workspaces/<str:slug>/chat/conversations/", AIConversationListEndpoint.as_view(), name="oneplan-conversations"),
    path("workspaces/<str:slug>/actions/approve/", AIActionApproveEndpoint.as_view(), name="oneplan-approve"),
    path("workspaces/<str:slug>/actions/logs/", AIActionLogEndpoint.as_view(), name="oneplan-action-logs"),
    path("workspaces/<str:slug>/pillars/", PillarListEndpoint.as_view(), name="oneplan-pillars"),
    path("workspaces/<str:slug>/objectives/", ObjectiveEndpoint.as_view(), name="oneplan-objectives"),
    path("workspaces/<str:slug>/objectives/<uuid:objective_id>/", ObjectiveDetailEndpoint.as_view(), name="oneplan-objective-detail"),
    path("workspaces/<str:slug>/constraints/", ConstraintEndpoint.as_view(), name="oneplan-constraints"),
    path("workspaces/<str:slug>/constraints/rank/", ConstraintRankEndpoint.as_view(), name="oneplan-constraints-rank"),
    path("workspaces/<str:slug>/constraints/dashboard/", ConstraintDashboardEndpoint.as_view(), name="oneplan-constraints-dashboard"),
    path("workspaces/<str:slug>/constraints/<uuid:constraint_id>/", ConstraintDetailEndpoint.as_view(), name="oneplan-constraint-detail"),
    path("workspaces/<str:slug>/constraints/<uuid:constraint_id>/issues/", ConstraintLinkEndpoint.as_view(), name="oneplan-constraint-link"),
    path("workspaces/<str:slug>/command/", CommandCenterEndpoint.as_view(), name="oneplan-command"),
    path("connectors/status/", ConnectorsStatusEndpoint.as_view(), name="oneplan-connectors-status"),
    path("workspaces/<str:slug>/connectors/apps/", ConnectorsAppsEndpoint.as_view(), name="oneplan-connectors-apps"),
    path("workspaces/<str:slug>/connectors/tools/", ConnectorsToolsEndpoint.as_view(), name="oneplan-connectors-tools"),
    path("workspaces/<str:slug>/connectors/run/", ConnectorsRunEndpoint.as_view(), name="oneplan-connectors-run"),
]

auth_urlpatterns = [
    path("supabase/", SupabaseAuthEndpoint.as_view(), name="supabase-auth"),
]
