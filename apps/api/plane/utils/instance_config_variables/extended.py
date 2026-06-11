# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

import os

extended_config_variables = [
    {
        "key": "ENABLE_ONEPLAN_FEATURES",
        "value": os.environ.get("ENABLE_ONEPLAN_FEATURES", "1"),
        "category": "ONEPLAN",
        "is_encrypted": False,
    },
    {
        "key": "ENABLE_AI_OPERATOR",
        "value": os.environ.get("ENABLE_AI_OPERATOR", "1"),
        "category": "ONEPLAN",
        "is_encrypted": False,
    },
    {
        "key": "ENABLE_FLOW_CONSTRAINTS",
        "value": os.environ.get("ENABLE_FLOW_CONSTRAINTS", "1"),
        "category": "ONEPLAN",
        "is_encrypted": False,
    },
    {
        "key": "ENABLE_SUPABASE_AUTH",
        "value": os.environ.get("ENABLE_SUPABASE_AUTH", "0"),
        "category": "ONEPLAN",
        "is_encrypted": False,
    },
    {
        "key": "ENABLE_CEO_COMMAND_MODE",
        "value": os.environ.get("ENABLE_CEO_COMMAND_MODE", "1"),
        "category": "ONEPLAN",
        "is_encrypted": False,
    },
    {
        "key": "AI_ACTION_REQUIRE_APPROVAL",
        "value": os.environ.get("AI_ACTION_REQUIRE_APPROVAL", "1"),
        "category": "ONEPLAN",
        "is_encrypted": False,
    },
    {
        "key": "ENABLE_PIPEDREAM_CONNECTORS",
        "value": os.environ.get("ENABLE_PIPEDREAM_CONNECTORS", "1"),
        "category": "ONEPLAN",
        "is_encrypted": False,
    },
]
