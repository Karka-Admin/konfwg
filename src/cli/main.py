import typer
import secrets
import ipaddress
import subprocess
import re

from datetime import datetime, timezone, timedelta

from konfwg.database.engine import SessionLocal
from konfwg.database.models import Site, Peer, Interface
from konfwg.database.sync import sync_wireguard_state

from konfwg.wg.commands import wg_genkey, wg_genpsk, wg_pubkey
from konfwg.wg.reader import get_wireguard_state

from konfwg.web.app import sha256_hex, get_expiration_date
from konfwg.config import configuration
from konfwg.initialize import initialize

app = typer.Typer(no_args_is_help=True)

def parse_first_ipv4_cidr(address_field: str) -> ipaddress.IPv4Interface:
    # supports "10.0.0.1/24, fd00::1/64"
    parts = [p.strip() for p in address_field.split(",")]
    for p in parts:
        try:
            iface = ipaddress.ip_interface(p)
        except ValueError:
            continue
        if isinstance(iface, ipaddress.IPv4Interface):
            return iface
    raise ValueError(f"No IPv4 CIDR found in Interface.address='{address_field}'")

def extract_used_host_ips(peers) -> set[ipaddress.IPv4Address]:
    used = set()
    for p in peers:
        # p.address expected like "10.0.0.2/32" or maybe plain "10.0.0.2"
        if not p.address:
            continue
        s = p.address.strip()
        try:
            ip = ipaddress.ip_interface(s).ip
        except ValueError:
            try:
                ip = ipaddress.ip_address(s)
            except ValueError:
                continue
        if isinstance(ip, ipaddress.IPv4Address):
            used.add(ip)
    return used

def allocate_peer_address_ipv4(interface_address_field: str, existing_peers) -> str:
    iface = parse_first_ipv4_cidr(interface_address_field)
    network = iface.network
    server_ip = iface.ip

    used = extract_used_host_ips(existing_peers)
    used.add(server_ip)  # don’t allocate server’s tunnel IP

    # pick first free host
    for host in network.hosts():
        if host not in used:
            return f"{host}/32"

    raise RuntimeError(f"No free IPs left in {network}")

def read_ipv4_cidr_from_wg_conf(ifname: str) -> str | None:
    conf = configuration.WG_DIRECTORY / f"{ifname}.conf"
    if not conf.exists():
        return None
    text = conf.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"(?im)^\s*Address\s*=\s*(.+?)\s*$", text)
    if not m:
        return None
    # could be "10.0.0.1/24, fd00::1/64"
    return m.group(1).strip()

def read_ipv4_cidr_from_ip(ifname: str) -> str | None:
    try:
        out = subprocess.check_output(["ip", "-o", "-4", "addr", "show", "dev", ifname], text=True).strip()
    except subprocess.CalledProcessError:
        return None
    # inet 10.0.0.1/24 ...
    m = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+/\d+)", out)
    return m.group(1) if m else None

def get_interface_address_field(ifname: str) -> str:
    ip_addr = read_ipv4_cidr_from_ip(ifname)
    if ip_addr:
        return ip_addr
    raise typer.BadParameter(
        f"Couldn't read IPv4 address for interface '{ifname}' via `ip addr`. "
        f"Is the interface up? Try: `ip -o -4 addr show dev {ifname}`"
    )

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
        database = SessionLocal()
        try:
            peers = database.query(Peer).all()
            for p in peers:
                print(f"{p.peer_id}: {p.name} iface={p.interface_id} pub={p.public_key[:10]}... allowed={p.allowed_ips}")
        finally:
            database.close()
    else:
        print("ERROR: Argument not found!")
        return

@app.command()
def sync():
    """
    Reads WireGuard live state + config and syncs interfaces and peers into database.
    """
    database = SessionLocal()
    try:
        state = get_wireguard_state()  # your wg/reader.py
        stats = sync_wireguard_state(database, Interface, Peer, state)  # your database/sync.py
        database.commit()
        print("Sync complete:", stats)
    except Exception as e:
        database.rollback()
        raise
    finally:
        database.close()

@app.command()
def add(name: str, interface: str = "wg0"):
    """
    Creates a new peer.
    """
    initialize()
    sync()  # assumes this updates DB with interfaces

    token = secrets.token_urlsafe(24)
    password = secrets.token_urlsafe(12)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=15)

    database = SessionLocal()
    try:
        iface = database.query(Interface).filter(Interface.name == interface).one_or_none()
        if iface is None:
            raise typer.BadParameter(
                f"Interface '{interface}' not found in DB. Run `konfwg sync` first."
            )

        # 1) allocate tunnel address for peer
        existing_peers = database.query(Peer).filter(Peer.interface_id == iface.interface_id).all()
        address_field = iface.address.strip() if iface.address.strip() else get_interface_address_field(interface)
        peer_address = allocate_peer_address_ipv4(address_field, existing_peers)
 

        # 2) generate keys
        private_key = wg_genkey()
        public_key = wg_pubkey(private_key)
        preshared_key = wg_genpsk()  # optional but recommended

        # 3) allowed ips on SERVER side
        allowed_ips = peer_address   # can append more routes later: f"{peer_address}, 192.168.88.0/24"

        # 4) insert peer + site
        peer = Peer(
            interface_id=iface.interface_id,
            name=name,
            address=peer_address,
            public_key=public_key,
            private_key=private_key,       # you plan to remove later; fine for now
            preshared_key=preshared_key,
            allowed_ips=allowed_ips,
            keepalive=25,                  # common for NAT clients; or None
            active=1,
            created_at=now.isoformat(),
            comment=None,
        )
        database.add(peer)
        database.flush()  # assigns peer.peer_id

        site = Site(
            peer_id=peer.peer_id,
            token=token,
            password=sha256_hex(password),
            expires_at=expires_at.isoformat(),
            revoked=0,
            created_at=now.isoformat(),
            last_access_at=None,
        )
        database.add(site)
        database.commit()

    except Exception:
        database.rollback()
        raise
    finally:
        database.close()

    print(f"URL: {configuration.BASE_URL}/conf/{token}")
    print(f"Password: {password}")
    print("Expires in 15 minutes.")

@app.command()
def update(peer: str):
    print(f"Updating peer {peer} not implemented yet!")

@app.command()
def delete(peer: str):
    print(f"Deleting peer {peer} not implemented yet!")