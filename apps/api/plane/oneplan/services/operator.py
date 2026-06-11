# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

import json
import uuid

from plane.db.models import Workspace
from plane.oneplan.models import AIConversation, AIMessage
from plane.oneplan.services.actions.registry import (
    READ_TOOLS,
    TOOL_DEFINITIONS,
    execute_tool,
    log_action,
)
from plane.oneplan.services.context import workspace_summary_text
from plane.oneplan.services.feature_flags import is_ai_operator_enabled
from plane.oneplan.services.provider.base import chat_completion


SYSTEM_PROMPT = """You are Alfred, the OnePlan AI operator. You help users manage objectives, constraints, and work execution.

Modes:
- ask: Answer questions using read-only tools. Cite task IDs when referencing work items.
- plan: Propose changes using tools with dry_run. Never execute writes without approval.
- act: Execute approved actions only when user confirms.

Always respect workspace boundaries. Identify the highest-leverage constraint when asked about priorities.
"""


def run_operator(
    user,
    workspace: Workspace,
    message: str,
    mode: str = AIConversation.MODE_ASK,
    conversation_id: str | None = None,
    dry_run: bool = True,
) -> dict:
    if not is_ai_operator_enabled():
        return {"error": "AI operator is not enabled"}

    conversation = None
    if conversation_id:
        conversation = AIConversation.objects.filter(id=conversation_id, workspace=workspace, user=user).first()
    if not conversation:
        conversation = AIConversation.objects.create(
            workspace=workspace,
            user=user,
            mode=mode,
            title=message[:80],
        )

    AIMessage.objects.create(conversation=conversation, role=AIMessage.ROLE_USER, content=message)

    tools = TOOL_DEFINITIONS if mode != AIConversation.MODE_ASK else [t for t in TOOL_DEFINITIONS if t["function"]["name"] in READ_TOOLS]

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + f"\n\nWorkspace context:\n{workspace_summary_text(workspace)}"},
        {"role": "user", "content": message},
    ]

    content, tool_calls, error = chat_completion(messages, tools=tools if tools else None)
    if error:
        return {"error": error, "conversation_id": str(conversation.id)}

    tool_results = []
    previews = []

    if tool_calls:
        for tc in tool_calls:
            fn = tc["function"]
            tool_name = fn["name"]
            try:
                args = json.loads(fn["arguments"]) if fn["arguments"] else {}
            except json.JSONDecodeError:
                args = {}
            is_write = tool_name not in READ_TOOLS
            effective_dry_run = dry_run or mode == AIConversation.MODE_ASK or (mode == AIConversation.MODE_PLAN and is_write)
            result = execute_tool(tool_name, args, user, workspace, dry_run=effective_dry_run)
            tool_results.append({"tool": tool_name, "result": result})
            if is_write and effective_dry_run and result.get("preview"):
                preview_id = uuid.uuid4()
                log_action(
                    user=user,
                    workspace=workspace,
                    action_type=tool_name,
                    payload=args,
                    result=result,
                    dry_run=True,
                    status="preview",
                    summary=f"Preview: {tool_name}",
                    preview_id=preview_id,
                )
                previews.append({"preview_id": str(preview_id), "action": tool_name, "result": result})

        followup = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
            {"role": "assistant", "content": content or "", "tool_calls": tool_calls},
            {
                "role": "tool",
                "content": json.dumps(tool_results),
            },
        ]
        content, _, error = chat_completion(followup)

    AIMessage.objects.create(
        conversation=conversation,
        role=AIMessage.ROLE_ASSISTANT,
        content=content or "",
        tool_calls=tool_calls,
        citations=[{"type": "tool", "data": tool_results}] if tool_results else None,
    )

    return {
        "conversation_id": str(conversation.id),
        "response": content,
        "mode": mode,
        "tool_results": tool_results,
        "previews": previews,
        "requires_approval": len(previews) > 0,
    }
