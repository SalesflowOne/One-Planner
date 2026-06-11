# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from django.urls import path

from plane.api.views.oneplan import (
    ExternalConstraintListEndpoint,
    ExternalObjectiveListEndpoint,
    ExternalToolExecuteEndpoint,
    ExternalWorkspaceSummaryEndpoint,
)

urlpatterns = [
    path(
        "workspaces/<str:workspace_slug>/summary/",
        ExternalWorkspaceSummaryEndpoint.as_view(),
        name="api-v1-workspace-summary",
    ),
    path(
        "workspaces/<str:workspace_slug>/constraints/",
        ExternalConstraintListEndpoint.as_view(),
        name="api-v1-constraints",
    ),
    path(
        "workspaces/<str:workspace_slug>/objectives/",
        ExternalObjectiveListEndpoint.as_view(),
        name="api-v1-objectives",
    ),
    path(
        "workspaces/<str:workspace_slug>/tools/execute/",
        ExternalToolExecuteEndpoint.as_view(),
        name="api-v1-tool-execute",
    ),
]
