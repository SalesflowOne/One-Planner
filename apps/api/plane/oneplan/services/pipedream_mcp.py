# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

import json
import os
import uuid
from typing import Any

import requests

from plane.utils.exception_logger import log_exception

PIPEDREAM_MCP_URL = os.environ.get("PIPEDREAM_MCP_URL", "https://remote.mcp.pipedream.net/v3")
PIPEDREAM_TOKEN_URL = "https://api.pipedream.com/v1/oauth/token"

POPULAR_APPS = [
    {"slug": "slack", "name": "Slack"},
    {"slug": "github", "name": "GitHub"},
    {"slug": "google_sheets", "name": "Google Sheets"},
    {"slug": "notion", "name": "Notion"},
    {"slug": "gmail", "name": "Gmail"},
    {"slug": "linear", "name": "Linear"},
    {"slug": "hubspot", "name": "HubSpot"},
    {"slug": "salesforce", "name": "Salesforce"},
]


def is_pipedream_configured() -> bool:
    return bool(
        os.environ.get("PIPEDREAM_CLIENT_ID")
        and os.environ.get("PIPEDREAM_CLIENT_SECRET")
        and os.environ.get("PIPEDREAM_PROJECT_ID")
    )


def _pd_config() -> dict[str, str]:
    return {
        "client_id": os.environ.get("PIPEDREAM_CLIENT_ID", ""),
        "client_secret": os.environ.get("PIPEDREAM_CLIENT_SECRET", ""),
        "project_id": os.environ.get("PIPEDREAM_PROJECT_ID", ""),
        "environment": os.environ.get("PIPEDREAM_ENVIRONMENT", "production"),
    }


def get_access_token() -> str | None:
    cfg = _pd_config()
    if not all([cfg["client_id"], cfg["client_secret"]]):
        return None
    try:
        res = requests.post(
            PIPEDREAM_TOKEN_URL,
            json={
                "grant_type": "client_credentials",
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
            },
            timeout=30,
        )
        res.raise_for_status()
        return res.json().get("access_token")
    except Exception as e:
        log_exception(e)
        return None


def _mcp_headers(external_user_id: str, app_slug: str) -> dict[str, str] | None:
    token = get_access_token()
    cfg = _pd_config()
    if not token or not cfg["project_id"]:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-pd-project-id": cfg["project_id"],
        "x-pd-environment": cfg["environment"],
        "x-pd-external-user-id": external_user_id,
        "x-pd-app-slug": app_slug,
    }


def _mcp_request(external_user_id: str, app_slug: str, method: str, params: dict | None = None) -> dict[str, Any]:
    headers = _mcp_headers(external_user_id, app_slug)
    if not headers:
        return {"error": "Pipedream MCP is not configured"}

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
        "params": params or {},
    }
    try:
        res = requests.post(PIPEDREAM_MCP_URL, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        data = res.json()
        if data.get("error"):
            return {"error": data["error"]}
        return data.get("result", data)
    except Exception as e:
        log_exception(e)
        return {"error": str(e)}


def list_connector_apps() -> list[dict]:
    if not is_pipedream_configured():
        return []
    return POPULAR_APPS


def list_connector_tools(external_user_id: str, app_slug: str) -> dict[str, Any]:
    return _mcp_request(external_user_id, app_slug, "tools/list")


def run_connector_tool(
    external_user_id: str,
    app_slug: str,
    tool_name: str,
    arguments: dict | None = None,
) -> dict[str, Any]:
    return _mcp_request(
        external_user_id,
        app_slug,
        "tools/call",
        {"name": tool_name, "arguments": arguments or {}},
    )


def get_connect_instructions(app_slug: str) -> dict[str, str]:
    return {
        "app_slug": app_slug,
        "connect_url": f"https://mcp.pipedream.com/app/{app_slug}",
        "message": "Connect this app via Pipedream MCP, then retry the action.",
    }
