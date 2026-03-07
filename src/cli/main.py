import typer
import secrets
from datetime import datetime, timezone, timedelta

from konfwg.database.controller import DBController

from konfwg.wg.commands import wg_genkey, wg_genpsk, wg_pubkey

from konfwg.config import configuration
from konfwg.initialize import initialize

app = typer.Typer(no_args_is_help=True)

@app.callback(invoke_without_command=False)
def root(context: typer.Context, no_init: bool = typer.Option(False, "--no-init", help="Skip initialization checks")):
    """
    Callback function that runs everytime you use the tool.
    For checking initializing and checking if everything is setup correctly.

    Does not run when user just uses --help etc.
    """
    if no_init:
        return
    if context.resilient_parsing:
        return
    
    initialize()

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
    print()
    database = None
    try:
        database = DBController()
        if argument == "config":
            for setting in configuration:
                print(setting)
        elif argument == "peers":
            peers = database.get_peers()
            for peer in peers:
                print(peer)
        elif argument == "interfaces":
            interfaces = database.get_interfaces()
            for interface in interfaces:
                print(interface)
        elif argument == "sites":
            sites = database.get_sites()
            for site in sites:
                print(site)
        else:
            print("ERROR: Argument not found!")
    except Exception:
        raise
    finally:
        if database is not None:
            database.close()
    print()

@app.command()
def add_peer(name: str, interface: str = "wg0"):
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
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()

    print(f"\nNew peer {name} has been created successfully.")
    print(f"Configuration is accessible via: {configuration.BASE_URL}/conf/{token}")
    print(f"Password: {password}")
    print(f"The site expires on {expires_at}.\n")

@app.command()
def update_peer(peer: str):
    print(f"Updating peer {peer} not implemented yet!")

@app.command()
def delete_peer(peer: str):
    print(f"Deleting peer {peer} not implemented yet!")

@app.command()
def add_interface(name: str = "wg0", address: str = "10.8.0.1/24", port: int = 51820):
    database = DBController()
    try:
        private_key = wg_genkey()
        public_key = wg_pubkey(private_key)
        interface = database.create_interface(
            name=name,
            address=address,
            port=port,
            private_key=private_key,
            public_key=public_key,
            comment="User created interface",
        )
        database.commit()
        print(f"Created: {interface}")
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()