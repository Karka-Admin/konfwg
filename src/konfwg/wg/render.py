from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import qrcode
from jinja2 import Environment, FileSystemLoader

from konfwg.database.models import Interface
from konfwg.config import configuration
from konfwg.database.controller import DBController

@dataclass(frozen=True)
class ClientConfigContext:
    client_private_key: str
    client_address: str
    client_dns: Optional[str]

    server_public_key: str
    preshared_key: Optional[str]
    server_endpoint: str

    allowed_ips: str
    persistent_keepalive: int

@dataclass(frozen=True)
class ServerConfigContext:
    interface_address: str
    interface_port: int
    interface_private_key: str
    post_up: Optional[str]
    post_down: Optional[str]
    peers: list[dict]

def template_dir() -> Path:
    return Path(configuration.CODE_PATH) / "src" / "konfwg" / "wg" / "templates"

def jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(template_dir())),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

def get_site_bundle_dir(token: str) -> Path:
    return Path(configuration.TMP_PATH) / "sites" / token

def get_site_conf_path(token: str) -> Path:
    return get_site_bundle_dir(token) / "client.conf"

def get_site_qr_path(token: str) -> Path:
    return get_site_bundle_dir(token) / "client.png"

def _normalize_host_port(host_or_endpoint: str, port: str | int) -> str:
    value = host_or_endpoint.strip()

    # If already includes a port, keep it as-is.
    if ":" in value and not value.startswith("["):
        # crude but sufficient for your current IPv4/domain use case
        parts = value.rsplit(":", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return value

    return f"{value}:{port}"

def derive_server_endpoint(interface: Interface) -> str:
    """
    Picks the best endpoint source for client configs.

    Priority:
    1. interface.endpoint
    2. hostname from BASE_URL
    """
    if getattr(interface, "endpoint", None):
        return _normalize_host_port(str(interface.endpoint), interface.port)

    parsed = urlparse(str(configuration.BASE_URL))
    if not parsed.hostname:
        raise ValueError("Could not derive server endpoint from BASE_URL")

    return f"{parsed.hostname}:{interface.port}"

def normalize_client_address(address: str) -> str:
    """
    Client config [Interface] Address.
    If DB already stores CIDR, keep it.
    Otherwise append /32.
    """
    value = address.strip()
    if "/" in value:
        return value
    return f"{value}/32"

def normalize_server_peer_allowed_ips(address: str) -> str:
    """
    Server config [Peer] AllowedIPs.
    For a single client peer this should usually be that peer IP /32.
    """
    value = address.strip()
    if "/" in value:
        return value
    return f"{value}/32"

def render_client_config_from_token(*, db: DBController, token: str) -> str:
    site = db.get_site_by_token(token)
    if site is None:
        raise ValueError("site_not_found")

    peer = site.peer
    if peer is None:
        raise ValueError("peer_not_found")

    interface = peer.interface
    if interface is None:
        raise ValueError("interface_not_found")

    ctx = ClientConfigContext(
        client_private_key=peer.private_key,
        client_address=normalize_client_address(peer.address),
        client_dns="1.1.1.1",
        server_public_key=interface.public_key,
        preshared_key=peer.preshared_key,
        server_endpoint=derive_server_endpoint(interface),
        allowed_ips="0.0.0.0/0",
        persistent_keepalive=int(peer.keepalive or 25),
    )

    env = jinja_env()
    template = env.get_template("client.conf.j2")
    return template.render(**ctx.__dict__).strip() + "\n"

def render_server_config_from_interface(*, db: DBController, interface_name: str, post_up: Optional[str] = None, post_down: Optional[str] = None) -> str:
    interface = db.get_interface_by_name(interface_name)
    if interface is None:
        raise ValueError("interface_not_found")

    db_peers = db.list_peers_by_interface_id(interface.interface_id)
    active_peers = [peer for peer in db_peers if peer.active]

    peers: list[dict] = []
    for peer in active_peers:
        peers.append(
            {
                "public_key": peer.public_key,
                "preshared_key": peer.preshared_key,
                "allowed_ips": normalize_server_peer_allowed_ips(peer.address),
                "persistent_keepalive": int(peer.keepalive) if peer.keepalive else None,
            }
        )

    ctx = ServerConfigContext(
        interface_address=interface.address,
        interface_port=interface.port,
        interface_private_key=interface.private_key,
        post_up=post_up,
        post_down=post_down,
        peers=peers,
    )

    env = jinja_env()
    template = env.get_template("server.conf.j2")
    return template.render(**ctx.__dict__).strip() + "\n"

def write_client_bundle(*, token: str) -> tuple[Path, Path]:
    db = DBController()
    try:
        config_text = render_client_config_from_token(db=db, token=token)

        bundle_dir = get_site_bundle_dir(token)
        bundle_dir.mkdir(parents=True, exist_ok=True)

        conf_path = get_site_conf_path(token)
        qr_path = get_site_qr_path(token)

        conf_path.write_text(config_text, encoding="utf-8")

        qr = qrcode.QRCode(
            version=None,
            box_size=8,
            border=2,
        )
        qr.add_data(config_text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_path)

        return conf_path, qr_path
    finally:
        db.close()

def ensure_client_bundle(*, token: str) -> tuple[Path, Path]:
    # conf_path = get_site_conf_path(token)
    # qr_path = get_site_qr_path(token)

    # if conf_path.exists() and qr_path.exists():
    #    return conf_path, qr_path
    return write_client_bundle(token=token)

def write_server_config_file(*, interface_name: str, post_up: Optional[str] = None, post_down: Optional[str] = None) -> Path:
    db = DBController()
    try:
        config_text = render_server_config_from_interface(
            db=db,
            interface_name=interface_name,
            post_up=post_up,
            post_down=post_down,
        )

        output_path = Path(configuration.WG_DIRECTORY) / f"{interface_name}.conf"
        output_path.write_text(config_text, encoding="utf-8")
        return output_path
    finally:
        db.close()