"""
start.py — AgentPress launcher
Starts both the FastAPI backend and the Vite frontend in one command.
Usage: python start.py
"""

import subprocess
import sys
import os
import signal
import time
from pathlib import Path

ROOT = Path(__file__).parent
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
VENV_UVICORN = ROOT / ".venv" / "bin" / "uvicorn"

processes = []


def start_all():
    # Backend
    api = subprocess.Popen(
        [str(VENV_UVICORN), "main:app", "--reload", "--port", "8000"],
        cwd=ROOT,
    )
    processes.append(api)
    print(f"[API] Started — PID {api.pid} — http://localhost:8000")

    # Frontend
    ui = subprocess.Popen(
        ["npm", "--prefix", "ui/web", "run", "dev"],
        cwd=ROOT,
    )
    processes.append(ui)
    print(f"[UI]  Started — PID {ui.pid}  — http://localhost:3000")

    return api, ui


def stop_all():
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass
    for p in processes:
        try:
            p.wait(timeout=5)
        except Exception:
            p.kill()
    processes.clear()


def handle_signal(sig, frame):
    print("\nShutting down...")
    stop_all()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Write PIDs to file so the restart endpoint can find them
    api_proc, ui_proc = start_all()
    pid_file = ROOT / ".pids"
    pid_file.write_text(f"{api_proc.pid}\n{ui_proc.pid}")

    print("\nAgentPress running. Press Ctrl+C to stop.\n")

    # Keep alive — restart either process if it dies unexpectedly
    while True:
        time.sleep(2)
        if api_proc.poll() is not None:
            print("[API] Process died — restarting...")
            processes.remove(api_proc)
            api_proc = subprocess.Popen(
                [str(VENV_UVICORN), "main:app", "--reload", "--port", "8000"],
                cwd=ROOT,
            )
            processes.append(api_proc)
            pid_file.write_text(f"{api_proc.pid}\n{ui_proc.pid}")
