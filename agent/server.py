"""Local web server: serves the chat page and a JSON API. Bind to 127.0.0.1 by default."""
import json
import os
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

import agent
import tools

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
STATIC = os.path.join(os.path.dirname(__file__), "static")
history: list = []


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(STATIC, "index.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if self.path == "/api/status":
            return self._send(200, json.dumps({"model": agent.MODEL, "ollama": agent.OLLAMA_URL, "workspace": tools.WORKSPACE}), "application/json")
        self._send(404, "not found", "text/plain")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        if self.path == "/api/reset":
            history.clear()
            return self._send(200, "{}", "application/json")
        if self.path == "/api/chat":
            text = (payload.get("message") or "").strip()
            if not text:
                return self._send(400, json.dumps({"error": "empty message"}), "application/json")
            try:
                result = agent.run_turn(history, text)
                return self._send(200, json.dumps(result, ensure_ascii=False), "application/json")
            except Exception as e:
                return self._send(502, json.dumps({"error": f"model call failed: {e}"}, ensure_ascii=False), "application/json")
        self._send(404, "not found", "text/plain")


if __name__ == "__main__":
    print(f"Agent UI on http://{HOST}:{PORT}  model={agent.MODEL}  ollama={agent.OLLAMA_URL}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
