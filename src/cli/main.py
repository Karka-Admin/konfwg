import typer
import secrets
from datetime import datetime, timezone, timedelta

from konfwg.wg.render import write_client_bundle, write_server_config_file
from konfwg.database.controller import DBController
from konfwg.wg.commands import wg_genkey, wg_genpsk, wg_pubkey, wg_restart
from konfwg.config import configuration
from konfwg.security import *
from konfwg.network import *
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
    db = DBController()
    try:
        iface = db.get_interface(interface)
        if not iface:
            raise typer.BadParameter(f"Interface '{interface}' not found.")
        
        name = name.strip()
        if not name:
            raise typer.BadParameter("Peer name cannot be empty.")

        password = generate_password()
        peers = db.get_peers_by_interface(iface.interface_id)
        address = get_free_ip(iface, peers)
        private_key = wg_genkey()
        public_key = wg_pubkey(private_key)
        preshared_key = wg_genpsk()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        token=generate_url_token()

        peer = db.create_peer(
            interface=iface,
            name=name,
            address=address,
            public_key=public_key,
            private_key=private_key,
            preshared_key=preshared_key,
            allowed_ips=address,
            keepalive=25,
        )
        
        db.create_site(
            peer=peer,
            token=token,
            password=hash_password(password),
            expires_at=expires_at.isoformat(),
        )
        
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally: 
        db.close()

    write_client_bundle(token=token)
    wg_restart(interface)

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
    db = DBController()
    try:
        private_key = wg_genkey()
        public_key = wg_pubkey(private_key)
        interface = db.create_interface(
            name=name,
            address=address,
            port=port,
            private_key=private_key,
            public_key=public_key,
            comment="User created interface",
        )
        db.commit()
        print(f"Created: {interface}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@app.command()
def sync_interface(name: str = "wg0"):
    output_path = write_server_config_file(
        interface_name=name,
        post_up="iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE",
        post_down="iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE",
    )
    wg_restart(name)
    print(f"Server config written to {output_path}")