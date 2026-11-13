"""Tools the local agent can call. All file paths are confined to WORKSPACE."""
import html
import os
import re
import subprocess
import urllib.request

WORKSPACE = os.path.abspath(os.environ.get("AGENT_WORKSPACE", os.path.join(os.path.dirname(__file__), "..", "workspace")))
os.makedirs(WORKSPACE, exist_ok=True)
MAX_OUT = 8000


def _safe_path(p: str) -> str:
    full = os.path.abspath(os.path.join(WORKSPACE, p))
    if os.path.commonpath([full, WORKSPACE]) != WORKSPACE:
        raise ValueError("path is outside the workspace")
    return full


def _clip(s: str) -> str:
    return s if len(s) <= MAX_OUT else s[:MAX_OUT] + "\n...[truncated]"


def list_dir(path: str = ".") -> str:
    entries = sorted(os.listdir(_safe_path(path)))
    return "\n".join(e + ("/" if os.path.isdir(os.path.join(_safe_path(path), e)) else "") for e in entries) or "(empty)"


def read_file(path: str) -> str:
    with open(_safe_path(path), encoding="utf-8", errors="replace") as f:
        return _clip(f.read())


def write_file(path: str, content: str) -> str:
    full = _safe_path(path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return f"wrote {len(content)} chars to {path}"


def run_command(command: str) -> str:
    """Runs a shell command inside the workspace with a 60s timeout."""
    try:
        r = subprocess.run(command, shell=True, cwd=WORKSPACE, capture_output=True, text=True, timeout=60)
        return _clip(f"exit={r.returncode}\n{r.stdout}{r.stderr}")
    except subprocess.TimeoutExpired:
        return "error: command timed out after 60s"


def fetch_url(url: str) -> str:
    """Fetches a web page and returns its text (HTML stripped)."""
    if not url.startswith(("http://", "https://")):
        return "error: url must start with http:// or https://"
    req = urllib.request.Request(url, headers={"User-Agent": "zoli-agent/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read(2_000_000).decode("utf-8", errors="replace")
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return _clip(text)


TOOL_FUNCS = {
    "list_dir": list_dir,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "fetch_url": fetch_url,
}

TOOL_SPECS = [
    {"type": "function", "function": {"name": "list_dir", "description": "List files in a workspace folder.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a text file in the workspace.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Create or overwrite a text file in the workspace.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "run_command", "description": "Run a shell command in the workspace (60s timeout).",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "fetch_url", "description": "Download a web page from the internet and return its text.",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
]


def execute(name: str, args: dict) -> str:
    fn = TOOL_FUNCS.get(name)
    if fn is None:
        return f"error: unknown tool {name}"
    try:
        return fn(**args)
    except Exception as e:  # return errors to the model so it can recover
        return f"error: {e}"
