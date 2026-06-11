# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from django.conf import settings
from django.db import models

from plane.db.models import BaseModel

from .base import OnePlanWorkspaceModel


class Pillar(OnePlanWorkspaceModel):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20, default="#6366f1")
    sort_order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "oneplan_pillars"
        ordering = ("sort_order", "name")
        unique_together = ["workspace", "name", "deleted_at"]


class Objective(OnePlanWorkspaceModel):
    STATUS_ACTIVE = "active"
    STATUS_ACHIEVED = "achieved"
    STATUS_PAUSED = "paused"
    STATUS_ABANDONED = "abandoned"

    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active"),
        (STATUS_ACHIEVED, "Achieved"),
        (STATUS_PAUSED, "Paused"),
        (STATUS_ABANDONED, "Abandoned"),
    )

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    pillar = models.ForeignKey(Pillar, on_delete=models.SET_NULL, null=True, blank=True, related_name="objectives")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    target_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="owned_objectives"
    )

    class Meta:
        db_table = "oneplan_objectives"
        ordering = ("-created_at",)


class Constraint(OnePlanWorkspaceModel):
    STATUS_IDENTIFIED = "identified"
    STATUS_ACTIVE = "active"
    STATUS_DELEGATED = "delegated"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_BLOCKED = "blocked"
    STATUS_RESOLVED = "resolved"

    STATUS_CHOICES = (
        (STATUS_IDENTIFIED, "Identified"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_DELEGATED, "Delegated"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_BLOCKED, "Blocked"),
        (STATUS_RESOLVED, "Resolved"),
    )

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    objective = models.ForeignKey(
        Objective, on_delete=models.SET_NULL, null=True, blank=True, related_name="constraints"
    )
    pillar = models.ForeignKey(Pillar, on_delete=models.SET_NULL, null=True, blank=True, related_name="constraints")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IDENTIFIED)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="owned_constraints"
    )
    priority_score = models.FloatField(default=0.0)
    priority_factors = models.JSONField(default=dict)
    kpi_metric = models.CharField(max_length=255, blank=True)
    kpi_target = models.CharField(max_length=255, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "oneplan_constraints"
        ordering = ("-priority_score", "-created_at")


class ConstraintIssueLink(BaseModel):
    constraint = models.ForeignKey(Constraint, on_delete=models.CASCADE, related_name="issue_links")
    issue = models.ForeignKey("db.Issue", on_delete=models.CASCADE, related_name="constraint_links")

    class Meta:
        db_table = "oneplan_constraint_issue_links"
        unique_together = ["constraint", "issue", "deleted_at"]


class ConstraintScoreHistory(BaseModel):
    constraint = models.ForeignKey(Constraint, on_delete=models.CASCADE, related_name="score_history")
    score = models.FloatField()
    factors = models.JSONField(default=dict)

    class Meta:
        db_table = "oneplan_constraint_score_history"
        ordering = ("-created_at",)
