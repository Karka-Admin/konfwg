import typer
import subprocess
import sys
import time
import secrets
import urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.error import URLError

from konfwg.database.engine import SessionLocal
from konfwg.database.models import Site
from konfwg.web.app import sha256_hex, utc_now, parse_iso
from konfwg.config import configuration

app = typer.Typer(no_args_is_help=True)

TMP_PATH = Path("/var/lib/konfwg/tmp")

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

    for i in range(10):
        if web_running():
            print("Web server started.")
            return
        time.sleep(0.5)
    print("Warning: Web server may not have started correctly.")

@app.command()
def status():
    """
    Shows konfwg status and health related to its
    configuration and web server
    """
    print("Well atleast the command is running!")

@app.command()
def show(argument: str):
    """
    Display information for specified argument
    
    :param argument: argument information to be displayed
    :type argument: str
    
    Available arguments
    -----------------
    config
    peers
    """
    if argument == "config":
        for setting in configuration:
            print(setting)
    elif argument == "peers":
        print("SHOW PEERS NOT IMPLEMENTED CURRENTLY!")

@app.command()
def add(peer: str):
    """
    Creates a new peer. The process is as follows:
    
    Starts up the web server if not running yet.
    Generates a token, password and get the current time
    Creates a database row
    """
    ensure_web()

    token = secrets.token_urlsafe(24)
    password = secrets.token_urlsafe(12)
    time_now = datetime.now(timezone.utc)
    expires_at = parse_iso(utc_now + timedelta(minutes=15))
    
    # TODO: replace with real peer_id
    peer_id = 1
    
    database = SessionLocal()
    try:
        site = Site(
            peer_id=peer_id,
            token=token,
            password=sha256_hex(password),
            expires_at=expires_at,
            revoked=0,
            created_at=parse_iso(utc_now),
            last_access_at=None,
        )
        database.add(site)
        database.commit()
    finally:
        database.close()
        
    #directory = TMP_PATH / token
    #directory.mkdir(parents=True, exist_ok=True)
    #(directory / "peer.conf").write_text(f"# temp config for {peer}\n", encoding="utf-8")
    #(directory / "peer.png").touch()
    
    print(f"URL: {configuration.base_url}/conf/{token}")
    print(f"Password: {password}")
    print("Expires in 15 minutes.")

@app.command()
def update(peer: str):
    print(f"Updating peer {peer} not implemented yet!")

@app.command()
def delete(peer: str):
    print(f"Deleting peer {peer} not implemented yet!")