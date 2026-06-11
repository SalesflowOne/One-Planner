# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

import os

from plane.license.utils.instance_value import get_configuration_value


def _flag(key: str, default: str = "0") -> bool:
    value = get_configuration_value([{"key": key, "default": os.environ.get(key, default)}])[0]
    return str(value) == "1"


def is_oneplan_enabled() -> bool:
    return _flag("ENABLE_ONEPLAN_FEATURES", "1")


def is_ai_operator_enabled() -> bool:
    return is_oneplan_enabled() and _flag("ENABLE_AI_OPERATOR", "1")


def is_flow_constraints_enabled() -> bool:
    return is_oneplan_enabled() and _flag("ENABLE_FLOW_CONSTRAINTS", "1")


def is_supabase_auth_enabled() -> bool:
    return _flag("ENABLE_SUPABASE_AUTH")


def is_ceo_command_enabled() -> bool:
    return is_oneplan_enabled() and _flag("ENABLE_CEO_COMMAND_MODE", "1")


def is_pipedream_connectors_enabled() -> bool:
    return is_ai_operator_enabled() and _flag("ENABLE_PIPEDREAM_CONNECTORS", "1")


def get_oneplan_config() -> dict:
    return {
        "enable_oneplan_features": is_oneplan_enabled(),
        "enable_ai_operator": is_ai_operator_enabled(),
        "enable_flow_constraints": is_flow_constraints_enabled(),
        "enable_supabase_auth": is_supabase_auth_enabled(),
        "enable_ceo_command_mode": is_ceo_command_enabled(),
        "enable_pipedream_connectors": is_pipedream_connectors_enabled(),
        "ai_action_require_approval": _flag("AI_ACTION_REQUIRE_APPROVAL", "1"),
    }
