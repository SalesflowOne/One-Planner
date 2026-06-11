# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from django.conf import settings
from django.db import models

from plane.db.models import BaseModel

from .base import OnePlanWorkspaceModel


class AIConversation(OnePlanWorkspaceModel):
    MODE_ASK = "ask"
    MODE_PLAN = "plan"
    MODE_ACT = "act"

    MODE_CHOICES = (
        (MODE_ASK, "Ask"),
        (MODE_PLAN, "Plan"),
        (MODE_ACT, "Act"),
    )

    title = models.CharField(max_length=255, blank=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_ASK)
    project = models.ForeignKey(
        "db.Project", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_conversations"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_conversations"
    )

    class Meta:
        db_table = "oneplan_ai_conversations"
        ordering = ("-created_at",)


class AIMessage(BaseModel):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_TOOL = "tool"
    ROLE_SYSTEM = "system"

    ROLE_CHOICES = (
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
        (ROLE_TOOL, "Tool"),
        (ROLE_SYSTEM, "System"),
    )

    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField(blank=True)
    tool_calls = models.JSONField(null=True, blank=True)
    citations = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "oneplan_ai_messages"
        ordering = ("created_at",)


class AIActionLog(OnePlanWorkspaceModel):
    STATUS_PREVIEW = "preview"
    STATUS_APPROVED = "approved"
    STATUS_EXECUTED = "executed"
    STATUS_FAILED = "failed"
    STATUS_REVERTED = "reverted"

    STATUS_CHOICES = (
        (STATUS_PREVIEW, "Preview"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_EXECUTED, "Executed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REVERTED, "Reverted"),
    )

    RISK_LOW = "low"
    RISK_MEDIUM = "medium"
    RISK_HIGH = "high"

    conversation = models.ForeignKey(AIConversation, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_action_logs")
    action_type = models.CharField(max_length=100, db_index=True)
    payload = models.JSONField(default=dict)
    result = models.JSONField(null=True, blank=True)
    pre_state = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PREVIEW)
    dry_run = models.BooleanField(default=True)
    risk_level = models.CharField(max_length=20, default=RISK_LOW)
    summary = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_ai_actions",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    preview_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "oneplan_ai_action_logs"
        ordering = ("-created_at",)


class UserAISettings(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_settings"
    )
    autonomous_mode = models.BooleanField(default=False)
    default_mode = models.CharField(max_length=20, default=AIConversation.MODE_ASK)

    class Meta:
        db_table = "oneplan_user_ai_settings"
