"""Test double for Ollama: first asks to run a tool, then answers using the tool result."""
import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        has_tool = any(m["role"] == "tool" for m in body["messages"])
        if not has_tool:
            msg = {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "write_file", "arguments": {"path": "hello.txt", "content": "مرحبا من الوكيل"}}}]}
        else:
            msg = {"role": "assistant", "content": "تم إنشاء الملف hello.txt بنجاح."}
        data = json.dumps({"message": msg}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self, *a): pass

ThreadingHTTPServer(("127.0.0.1", 11999), H).serve_forever()
