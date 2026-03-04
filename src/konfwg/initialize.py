from __future__ import annotations

import subprocess

from konfwg.database.base import Base
from konfwg.database import engine

def init_database() -> None:
    """
    Initializes the database engine.
    """
    Base.metadata.create_all(bind=engine)
    
def service_running(name: str) -> bool:
    """
    Helper returns true if specified service is running.
    """
    subprocess.run(["systemctl", "is-active", "--quiet", name]).returncode == 0

def ensure_service() -> None:
    """
    Checks if konfwg.service (web server fastapi + uvicorn) is started before using the tool.
    """
    if service_running("konfwg.service"):
        return
    raise RuntimeError(
        "konfwg.service is not running. Start it with: sudo systemctl start konfwg.service"
    )


def initialize():
    init_database()

 #verify configuration
 #check permissions
 #verify wireguard exists
 #verify caddy exists
 #sanity checks