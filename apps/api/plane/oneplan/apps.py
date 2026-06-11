# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from django.apps import AppConfig


class OnePlanConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "plane.oneplan"
    verbose_name = "OnePlan"
