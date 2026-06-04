"""
model_manager.py — owns the llama-server subprocess.

The ModelManager keeps exactly one llama-server running at a time. When the
pipeline needs a different model than what's loaded, ModelManager stops the
current process and starts a new one.

This is the only module that knows about subprocess management. Everything
else just calls ensure_model() and trusts the right model is up afterward.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Optional

import httpx


# ────────── Configuration ──────────

LLAMA_SERVER_EXE = Path(r"D:\tools\llama.cpp\llama-server.exe")
MODELS_DIR = Path(r"D:\tools\models")

# Model definitions. Each entry says: where the GGUF lives, what extra flags
# llama-server needs for it. Add more entries here when you add models.
MODELS = {
    "qwen": {
        "model_path": MODELS_DIR / "qwen2.5-7b-instruct-q5_k_m-00001-of-00002.gguf",
        "mmproj_path": None,
        "context_size": 8192,
    },
    "minicpm": {
        "model_path": MODELS_DIR / "ggml-model-Q4_K_M.gguf",
        "mmproj_path": MODELS_DIR / "mmproj-model-f16.gguf",
        "context_size": 4096,
    },
}

# llama-server runs on this address. Hardcoded for now.
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8090
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

# How long to wait for a model to become reachable after we start it.
# 60s is generous — Qwen Q5 takes ~15s, MiniCPM Q4 takes ~10s.
STARTUP_TIMEOUT_SECONDS = 60


class ModelManager:
    """Single-process owner of llama-server. Use as a singleton."""

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None
        self._current_model: Optional[str] = None

    # ────────── Public API ──────────

    @property
    def current_model(self) -> Optional[str]:
        """Name of the currently loaded model, or None if nothing is loaded."""
        return self._current_model

    def ensure_model(self, name: str) -> None:
        """Make sure the named model is loaded. Swap if a different one is up.

        After this method returns successfully, llama-server is reachable on
        SERVER_URL with the requested model loaded.
        """
        if name not in MODELS:
            raise ValueError(
                f"Unknown model: {name}. Available: {list(MODELS.keys())}"
            )

        if self._current_model == name and self._is_alive():
            # Already running; nothing to do.
            return

        # Either no model loaded, or a different one is. Stop and restart.
        if self._process is not None:
            self._stop()
        self._start(name)

    def shutdown(self) -> None:
        """Clean shutdown — call this when FastAPI exits."""
        if self._process is not None:
            self._stop()

    # ────────── Internals ──────────

    def _start(self, name: str) -> None:
        """Launch llama-server with the given model and wait for readiness."""
        config = MODELS[name]

        if not config["model_path"].exists():
            raise FileNotFoundError(
                f"Model file not found: {config['model_path']}"
            )

        # Build the command line. Mirrors what you'd type in a terminal.
        cmd = [
            str(LLAMA_SERVER_EXE),
            "-m", str(config["model_path"]),
            "--host", SERVER_HOST,
            "--port", str(SERVER_PORT),
            "-ngl", "99",
            "-c", str(config["context_size"]),
        ]
        if config["mmproj_path"] is not None:
            cmd += ["--mmproj", str(config["mmproj_path"])]

        print(f"[ModelManager] Starting {name}...")
        # CREATE_NEW_PROCESS_GROUP on Windows lets us cleanly kill the whole
        # process tree later. stdout/stderr piped to DEVNULL keeps logs
        # silent — flip to None if you want to see llama-server output.
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )

        # Poll the server until it answers /health, or timeout.
        self._wait_for_ready()
        self._current_model = name
        print(f"[ModelManager] {name} ready.")

    def _stop(self) -> None:
        """Stop the current llama-server process."""
        if self._process is None:
            return
        print(f"[ModelManager] Stopping {self._current_model}...")
        self._process.terminate()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            # Didn't shut down nicely — force kill.
            self._process.kill()
            self._process.wait(timeout=5)
        self._process = None
        self._current_model = None

    def _is_alive(self) -> bool:
        """Quick check that the subprocess is still running."""
        if self._process is None:
            return False
        return self._process.poll() is None

    def _wait_for_ready(self) -> None:
        """Poll /health until it responds or we timeout."""
        deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            # If the process died during startup, fail immediately.
            if not self._is_alive():
                raise RuntimeError(
                    "llama-server died during startup. "
                    "Run llama-server manually with the same args to see the error."
                )
            try:
                # Short timeout per attempt — we'll retry quickly.
                response = httpx.get(f"{SERVER_URL}/health", timeout=2.0)
                if response.status_code == 200:
                    return
            except httpx.RequestError:
                # Connection refused — server still booting. Wait and retry.
                pass
            time.sleep(0.5)

        # Timed out waiting. Kill the process so we don't leak.
        self._stop()
        raise TimeoutError(
            f"llama-server didn't become ready within {STARTUP_TIMEOUT_SECONDS}s."
        )


# Singleton instance — import this from other modules.
manager = ModelManager()