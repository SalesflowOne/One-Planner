# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from django.db import models

from plane.db.models import BaseModel


class OnePlanWorkspaceModel(BaseModel):
    """Workspace-scoped OnePlan entity."""

    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="oneplan_%(class)s")

    class Meta:
        abstract = True
