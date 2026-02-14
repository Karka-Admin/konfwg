from __future__ import annotations

import os
import sys
import time
import subprocess
import urllib.request
from urllib.error import URLError
from pathlib import Path

from konfwg.config import configuration
from konfwg.database.base import Base
from konfwg.database import engine

def ensure_dir(path: Path, mode: int | None = None) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if mode is not None:
        os.chmod(path, mode)

def ensure_file(path: Path, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()
    if mode is not None:
        os.chmod(path, mode)

def ensure_paths() -> None:
    return

def web_running() -> bool:
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1)
        return True
    except URLError:
        return False

def ensure_web():
    if web_running():
        return

    print("Starting konfwg web server...")
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "konfwg.web.app:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    for attempt in range(10):
        if web_running():
            print("Web server started.")
            return
        time.sleep(0.5)
    print("Warning: Web server may not have started correctly.")

def init_database() -> None:
    Base.metadata.create_all(bind=engine)
    
def initialize():
    init_database()
    ensure_paths()
    ensure_web()