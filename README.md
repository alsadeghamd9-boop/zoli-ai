# zoli-ai

## Local AI agent (Arabic/English UI)

A dependency-free Python agent that runs on your computer, uses a local model through [Ollama](https://ollama.com), and can read/write files in a workspace, run shell commands there, and fetch web pages.

### Setup
1. Install Python 3.9+ and Ollama, then pull a model with tool support, e.g. `ollama pull llama3.1`.
2. Start the agent:
   ```bash
   cd zoli-ai/agent
   OLLAMA_MODEL=llama3.1 python3 server.py
   ```
3. Open http://127.0.0.1:8000 and chat.

### Settings (environment variables)
- `OLLAMA_URL` (default `http://localhost:11434`)
- `OLLAMA_MODEL` (default `llama3.1`)
- `AGENT_WORKSPACE` (default `../workspace`) — file tools are confined to this folder.
- `HOST` (default `127.0.0.1`) and `PORT` (default `8000`).

### Safety
`run_command` executes real shell commands inside the workspace. Only run the agent with a model and prompts you trust, and keep `HOST` on `127.0.0.1` unless you understand the risk.
