import typer

from datetime import datetime, timezone, timedelta
from typing import Optional
from konfwg.wg.render import write_client_bundle, write_server_config_file
from konfwg.database.controller import DBController
from konfwg.wg.commands import wg_genkey, wg_genpsk, wg_pubkey, wg_restart
from konfwg.config import configuration
from konfwg.security import generate_password, generate_url_token, hash_password
from konfwg.network import get_free_ip
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
def list_objects(argument: str):
    """
    Lists all specified objects

    Available arguments
    -----------------
    configs
    peers
    interfaces
    sites
    """
    print()
    db = None
    try:
        db = DBController()
        if argument == "config":
            for setting in configuration:
                print(setting)
        elif argument == "peers":
            peers = db.list_peers()
            for peer in peers:
                print(peer)
        elif argument == "interfaces":
            interfaces = db.list_interfaces()
            for interface in interfaces:
                print(interface)
        elif argument == "sites":
            sites = db.list_sites()
            for site in sites:
                print(site)
        else:
            raise typer.BadParameter("Argument must be one of: config, peers, interfaces, sites")
    finally:
        if db is not None:
            db.close()
    print()

@app.command()
def add_peer(name: str, iface_name: str = typer.Option("wg0", "--iface", help="Interface name"), expires_minutes: int = typer.Option(15, "--expires-minutes", min=1, help="Portal expiry in minutes")):
    """
    Creates a new peer.
    """
    db = DBController()
    try:
        iface = db.get_interface_by_name(iface_name)
        if not iface:
            raise typer.BadParameter(f"Interface '{iface_name}' not found.")
        
        name = name.strip()
        if not name:
            raise typer.BadParameter("Peer name cannot be empty.")

        password = generate_password()
        peers = db.list_peers_by_interface_id(iface.interface_id)
        address = get_free_ip(iface, peers)
        private_key = wg_genkey()
        public_key = wg_pubkey(private_key)
        preshared_key = wg_genpsk()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
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
            comment="User created peer.",
        )
        
        db.create_site(
            peer=peer,
            token=token,
            password=hash_password(password),
            expires_at=expires_at,
        )
        
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally: 
        db.close()

    write_client_bundle(token=token)

    print(f"\nNew peer {name} has been created successfully.")
    print(f"Configuration is accessible via: {configuration.BASE_URL}/conf/{token}")
    print(f"Password: {password}")
    print(f"The site expires on {expires_at}.\n")
    print(f"Apply WireGuard changes separately with elevated privileges for interface '{iface_name}'.")

@app.command()
def update_peer(
        peer_name: str,
        new_name: Optional[str] = typer.Option(None, "--new-name", help="New peer name"),
        address: Optional[str] = typer.Option(None, "--address", help="New peer address"),
        allowed_ips: Optional[str] = typer.Option(None, "--allowed-ips", help="New AllowedIPs value"),
        keepalive: Optional[int] = typer.Option(None, "--keepalive", help="New PersistentKeepalive value"),
        active: Optional[bool] = typer.Option(None, "--active/--inactive", help="Set peer active state"),
        comment: Optional[str] = typer.Option(None, "--comment", help="Peer comment"),
    ) -> None:
    """
    Updates a peer by name.
    """
    db = DBController()
    try:
        peer_name = peer_name.strip()
        if not peer_name:
            raise typer.BadParameter("Peer name cannot be empty.")

        peer = db.get_peer_by_name(peer_name)
        if peer is None:
            raise typer.BadParameter(f"Peer '{peer_name}' not found.")

        iface = peer.interface
        if iface is None:
            raise typer.BadParameter(f"Peer '{peer_name}' has no interface assigned.")

        db.update_peer(
            peer_id=peer.peer_id,
            name=new_name,
            address=address,
            allowed_ips=allowed_ips,
            keepalive=keepalive,
            active=active,
            comment=comment,
        )
        db.commit()
        iface_name = iface.name
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(f"Peer '{peer_name}' updated successfully.")
    print(f"Apply WireGuard changes separately with elevated privileges for interface '{iface_name}'.")

@app.command()
def delete_peer(name: str):
    """
    Deletes a peer by name.
    """
    db = DBController()
    try:
        name = name.strip()
        if not name:
            raise typer.BadParameter("Peer name cannot be empty.")

        peer = db.get_peer_by_name(name)
        if peer is None:
            raise typer.BadParameter(f"Peer '{name}' not found.")

        iface = peer.interface
        if iface is None:
            raise typer.BadParameter(f"Peer '{name}' has no interface assigned.")

        iface_name = iface.name
        db.delete_peer_by_name(name)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(f"Peer '{name}' deleted from database.")
    print(f"Apply WireGuard changes separately with elevated privileges for interface '{iface_name}'.")


@app.command()
def add_interface(
    name: str = typer.Option("wg0", "--name", help="Interface name"),
    address: str = typer.Option("10.8.0.1/24", "--address", help="Interface CIDR address"),
    port: int = typer.Option(51820, "--port", min=1, help="Interface listen port")
    ) -> None:
    """
    Creates a new interface.
    """
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
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(f"Created: {name}")
    print(f"Apply WireGuard changes separately with elevated privileges for interface '{name}'.")

@app.command()
def update_interface(
    name: str,
    new_name: Optional[str] = typer.Option(None, "--new-name", help="New interface name"),
    address: Optional[str] = typer.Option(None, "--address", help="New interface address"),
    port: Optional[int] = typer.Option(None, "--port", min=1, help="New interface port"),
    endpoint: Optional[str] = typer.Option(None, "--endpoint", help="Endpoint override for clients"),
    comment: Optional[str] = typer.Option(None, "--comment", help="Interface comment"),
) -> None:
    """
    Updates an interface by name.
    """
    db = DBController()
    try:
        name = name.strip()
        if not name:
            raise typer.BadParameter("Interface name cannot be empty.")

        interface = db.get_interface_by_name(name)
        if interface is None:
            raise typer.BadParameter(f"Interface '{name}' not found.")

        db.update_interface(
            interface_id=interface.interface_id,
            name=new_name,
            address=address,
            port=port,
            endpoint=endpoint,
            comment=comment,
        )
        db.commit()
        final_name = new_name.strip() if new_name else interface.name
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(f"Interface '{name}' updated successfully.")
    print(f"Any existing system WireGuard config for '{final_name}' may need privileged manual cleanup.")

@app.command()
def delete_interface(name: str) -> None:
    """
    Deletes an interface by name.
    """
    db = DBController()
    try:
        name = name.strip()
        if not name:
            raise typer.BadParameter("Interface name cannot be empty.")

        interface = db.get_interface_by_name(name)
        if interface is None:
            raise typer.BadParameter(f"Interface '{name}' not found.")

        db.delete_interface_by_name(name)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(f"Interface '{name}' deleted from database.")
    print(f"Any existing system WireGuard config for '{name}' may need privileged manual cleanup.")

@app.command()
def sync_interface(name: str = typer.Option("wg0", "--name", help="Interface name")) -> None:
    """
    Regenerates and writes server config for an interface, then restarts WireGuard.
    This command is intended for the privileged execution path.
    """
    public_if = configuration.WG_PUBLICINT
    post_up = (
        f"iptables -A FORWARD -i {name} -o {public_if} -j ACCEPT; "
        f"iptables -A FORWARD -i {public_if} -o {name} -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT; "
        f"iptables -t nat -A POSTROUTING -o {public_if} -j MASQUERADE"
    )
    post_down = (
        f"iptables -D FORWARD -i {name} -o {public_if} -j ACCEPT; "
        f"iptables -D FORWARD -i {public_if} -o {name} -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT; "
        f"iptables -t nat -D POSTROUTING -o {public_if} -j MASQUERADE"
    )
    output_path = write_server_config_file(
        interface_name=name,
        post_up=post_up,
        post_down=post_down
    )

    wg_restart(name)
    print(f"Server config written to {output_path}")
    print(f"WireGuard interface '{name}' restarted.")
