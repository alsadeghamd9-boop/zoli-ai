"""Agent loop: sends the conversation to a local Ollama model and executes tool calls."""
import json
import os
import urllib.request

import tools

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
MAX_STEPS = 8
SYSTEM = (
    "You are a helpful local AI agent running on the user's computer. "
    "You can list, read and write files in the workspace, run shell commands there, "
    "and fetch web pages. Use tools when they help, then answer clearly in the user's language."
)


def chat_once(messages: list) -> dict:
    body = json.dumps({"model": MODEL, "messages": messages, "tools": tools.TOOL_SPECS, "stream": False}).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read())["message"]


def run_turn(history: list, user_text: str) -> dict:
    """Appends the user message to history, runs tool loop, returns reply and trace."""
    history.append({"role": "user", "content": user_text})
    trace = []
    for _ in range(MAX_STEPS):
        msg = chat_once([{"role": "system", "content": SYSTEM}] + history)
        history.append({"role": "assistant", "content": msg.get("content", ""), **({"tool_calls": msg["tool_calls"]} if msg.get("tool_calls") else {})})
        calls = msg.get("tool_calls") or []
        if not calls:
            return {"reply": msg.get("content", ""), "trace": trace}
        for call in calls:
            fn = call["function"]
            args = fn.get("arguments") or {}
            if isinstance(args, str):
                args = json.loads(args)
            result = tools.execute(fn["name"], args)
            trace.append({"tool": fn["name"], "args": args, "result": result[:500]})
            history.append({"role": "tool", "name": fn["name"], "content": result})
    return {"reply": "Stopped: too many tool steps.", "trace": trace}
