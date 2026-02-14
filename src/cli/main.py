import typer
import secrets
from datetime import datetime, timezone, timedelta

from konfwg.database.controller import DBController

from konfwg.wg.commands import wg_genkey, wg_genpsk, wg_pubkey

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
    print("SUCCESS: atleast something is working!")

@app.command()
def show(argument: str):
    """
    Returns information of specific object
    
    :param argument: argument information to be displayed
    :type argument: str
    
    Available arguments
    -----------------
    config
    peers
    interfaces
    sites
    """
    if argument == "config":
        for setting in configuration:
            print(setting)
    elif argument == "peers":
        database = DBController()
        peers = database.get_peers()
        for peer in peers:
            print(peer)
    elif argument == "interfaces":
        database = DBController()
        interfaces = database.get_interfaces()
        for interface in interfaces:
            print(interface)
    elif argument == "sites":
        database = DBController()
        sites = database.get_sites()
        for site in sites:
            print(site)
    else:
        print("ERROR: Argument not found!")
        return

@app.command()
def add(name: str, interface: str = "wg0"):
    """
    Creates a new peer.
    """
    initialize()

    token = secrets.token_urlsafe(24)
    password = secrets.token_urlsafe(12)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=15)
    database = DBController()

    try:
        iface = database.get_interface(interface)
        if not iface:
            raise typer.BadParameter(f"Interface '{interface}' not found.")

        private_key = wg_genkey()
        public_key = wg_pubkey(private_key)
        preshared_key = wg_genpsk()
        address = "10.8.0.2/32"
        allowed_ips = address
        
        peer = database.create_peer(
            interface=iface,
            name=name,
            address=address,
            public_key=public_key,
            private_key=private_key,
            preshared_key=preshared_key,
            allowed_ips=allowed_ips,
            keepalive=25,
        )
        
        site = database.create_site(
            peer=peer,
            token=token,
            password=sha256_hex(password),
            expires_at=expires_at.isoformat(),
        )

        database.commit()
    except:
        database.rollback()
        raise
    finally:
        database.close()

    print(f"\nNew peer {name} has been created successfully.")
    print(f"Configuration is accessible via: {configuration.BASE_URL}/conf/{token}")
    print(f"Password: {password}")
    print(f"The site expires on {expires_at}.\n")

@app.command()
def update(peer: str):
    print(f"Updating peer {peer} not implemented yet!")

@app.command()
def delete(peer: str):
    print(f"Deleting peer {peer} not implemented yet!")