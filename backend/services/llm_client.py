"""
LLM client for Qwen model via Fireworks AI (OpenAI-compatible API).

Handles Qwen3's thinking mode where responses come in 'reasoning_content'
field while 'content' may be null.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ─── Client Setup ────────────────────────────────────────────────────────────

_api_key: str = ""
_model_id: str = ""
_base_url: str = ""


def _init_config():
    """Initialize config from environment (lazy)."""
    global _api_key, _model_id, _base_url
    if not _api_key:
        _api_key = os.getenv("FIREWORKS_API_KEY", "")
        _model_id = os.getenv("MODEL_ID", "accounts/fireworks/models/qwen3p6-plus")
        _base_url = os.getenv("LLM_BASE_URL", "https://api.fireworks.ai/inference/v1")
        if not _api_key:
            raise ValueError(
                "FIREWORKS_API_KEY environment variable is required. "
                "Get your key at https://fireworks.ai/account/api-keys"
            )
        logger.info(f"Configured LLM client for model: {_model_id}")


def get_model_id() -> str:
    """Get the model ID from environment."""
    _init_config()
    return _model_id


# ─── Core LLM Functions ──────────────────────────────────────────────────────

def chat_completion(
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 4096,
    response_format: Optional[str] = None,
) -> str:
    """
    Send a chat completion request to the LLM via Fireworks AI.

    Handles Qwen3's thinking mode where the actual response may be in
    'reasoning_content' instead of 'content'.
    """
    _init_config()

    if response_format == "json":
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += "\n\nRespond ONLY with valid JSON. No markdown, no extra text, no thinking tags."

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_api_key}",
    }

    payload = {
        "model": _model_id,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": 0.8,
    }

    try:
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]["message"]
        content = choice.get("content")
        reasoning = choice.get("reasoning_content", "")

        # Qwen3 thinking mode: content is null, answer is at the end of reasoning
        if content is None or content.strip() == "":
            if reasoning:
                # The actual answer is usually after the thinking process
                # Try to find JSON or the final answer in the reasoning
                content = reasoning
            else:
                content = ""

        # Strip thinking tags if present
        if "<think>" in content:
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        return content

    except httpx.HTTPStatusError as e:
        logger.error(f"LLM HTTP error {e.response.status_code}: {e.response.text[:200]}")
        raise RuntimeError(f"LLM request failed: {e.response.text[:200]}") from e
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise RuntimeError(f"Failed to get response from LLM: {e}") from e


def generate_json(
    messages: list[dict],
    temperature: float = 0.6,
    max_tokens: int = 4096,
) -> dict:
    """
    Generate a structured JSON response from the LLM.

    Returns parsed JSON dict, or raises ValueError if parsing fails.
    """
    raw = chat_completion(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format="json",
    )

    # Try to extract JSON from the response
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in code blocks
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find the outermost JSON object or array using find/rfind
    try:
        start_obj = raw.find('{')
        start_arr = raw.find('[')
        
        # Determine if the outermost structure is an object or array
        start_idx = -1
        end_idx = -1
        
        if start_obj != -1 and (start_arr == -1 or start_obj < start_arr):
            start_idx = start_obj
            end_idx = raw.rfind('}')
        elif start_arr != -1:
            start_idx = start_arr
            end_idx = raw.rfind(']')
            
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = raw[start_idx:end_idx+1]
            return json.loads(json_str)
    except Exception as e:
        logger.warning(f"Manual bounds extraction failed: {e}")

    logger.error(f"Failed to parse JSON from LLM response:\n{raw[:800]}")
    raise ValueError(f"Could not parse JSON from LLM response")
