@echo off
REM Starts the Zoli agent on this Windows PC. Requires Python 3 and Ollama.
cd /d "%~dp0"
if "%OLLAMA_MODEL%"=="" set OLLAMA_MODEL=llama3.2
echo Model: %OLLAMA_MODEL%  ^|  Open http://127.0.0.1:8000
where python >nul 2>nul && (python server.py & goto :eof)
py -3 server.py
