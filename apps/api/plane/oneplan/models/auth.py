# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from django.conf import settings
from django.db import models

from plane.db.models import BaseModel


class ExternalIdentity(BaseModel):
    """Maps external identity providers (e.g. Supabase) to internal users."""

    PROVIDER_SUPABASE = "supabase"

    PROVIDER_CHOICES = ((PROVIDER_SUPABASE, "Supabase"),)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="external_identities")
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    external_id = models.CharField(max_length=255, db_index=True)
    email = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = "oneplan_external_identities"
        unique_together = ["provider", "external_id"]
        ordering = ("-created_at",)


class TenantMapping(BaseModel):
    """Maps external organization/tenant IDs to Plane workspaces."""

    external_org_id = models.CharField(max_length=255, db_index=True)
    provider = models.CharField(max_length=50, default=ExternalIdentity.PROVIDER_SUPABASE)
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="tenant_mappings")
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = "oneplan_tenant_mappings"
        unique_together = ["provider", "external_org_id"]
        ordering = ("-created_at",)
