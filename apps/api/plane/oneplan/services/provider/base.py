# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

import os
from typing import Any

from openai import OpenAI

from plane.app.views.external.base import SUPPORTED_PROVIDERS, get_llm_config
from plane.utils.exception_logger import log_exception


def chat_completion(messages: list[dict[str, str]], tools: list[dict] | None = None) -> tuple[str | None, list | None, str | None]:
    """Run LLM chat completion. Returns (content, tool_calls, error)."""
    api_key, model, provider_key = get_llm_config()
    if not api_key or not model:
        return None, None, "LLM is not configured. Set LLM_API_KEY in instance settings."

    try:
        if provider_key and provider_key.lower() == "gemini":
            model = f"gemini/{model}"

        client = OpenAI(api_key=api_key)
        kwargs: dict[str, Any] = {"model": model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0].message
        tool_calls = None
        if choice.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in choice.tool_calls
            ]
        return choice.content or "", tool_calls, None
    except Exception as e:
        log_exception(e)
        return None, None, str(e)
