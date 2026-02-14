import typer
import secrets
from datetime import datetime, timezone, timedelta

from konfwg.database.engine import SessionLocal
from konfwg.database.models import Site, Peer
from konfwg.web.app import sha256_hex, get_expiration_date
from konfwg.config import configuration
from konfwg.initialize import initialize

app = typer.Typer(no_args_is_help=True)

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
    Creates a database row for site and peer
    """
    initialize()

    token = secrets.token_urlsafe(24)
    password = secrets.token_urlsafe(12)
    time_now = datetime.now(timezone.utc)
    expires_at = time_now + timedelta(minutes=15)
    
    database = SessionLocal()
    try:
        peer = Peer(
            interface_id=1
        )

        site = Site(
            peer_id=1, # TODO: REPLACE WITH REAL PEER ID
            token=token,
            password=sha256_hex(password),
            expires_at=expires_at.isoformat(),
            revoked=0,
            created_at=time_now.isoformat(),
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
    
    print(f"URL: {configuration.BASE_URL}/conf/{token}")
    print(f"Password: {password}")
    print("Expires in 15 minutes.")

@app.command()
def update(peer: str):
    print(f"Updating peer {peer} not implemented yet!")

@app.command()
def delete(peer: str):
    print(f"Deleting peer {peer} not implemented yet!")