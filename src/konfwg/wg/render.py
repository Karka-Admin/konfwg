from __future__ import annotations

from typing import Iterable
from konfwg.database.models import Interface, Peer

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from jinja2 import Environment, PackageLoader, select_autoescape

from konfwg.database.controller import DBController


@dataclass(frozen=True)
class ClientConfigContext:
    token: str
    expires_at: str

    client_private_key: str
    client_address: str
    client_dns: Optional[str]

    server_public_key: str
    server_preshared_key: Optional[str]
    server_endpoint: str

    allowed_ips: str
    persistent_keepalive: int


def jinja_env() -> Environment:
    # Loads templates from: src/konfwg/wg/templates/
    return Environment(
        loader=PackageLoader("konfwg.wg", "templates"),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )

def render_client_config_from_token(*, db: DBController, token: str) -> str:
    """
    Renders WireGuard client config for a given site token.
    Reads everything from DB (and optionally from filesystem if you store private keys outside DB).
    Returns config text.
    """
    # 1) fetch site by token
    site = db.get_site_by_token(token)
    if site is None:
        raise ValueError("site_not_found")

    # 2) validate expiry if you want (or do this in FastAPI)
    # if site.expires_at < now: raise ValueError("expired")

    peer = site.peer  # assumes relationship exists

    # 3) gather server/global settings (adapt to your schema)
    # You probably have config values in DB or config.py
    server_endpoint = db.get_setting("server_endpoint")  # e.g. "vpn.karkasrv.lt:51820"
    server_public_key = db.get_setting("server_public_key")
    allowed_ips = db.get_setting("allowed_ips") or "0.0.0.0/0, ::/0"
    dns = db.get_setting("client_dns")  # optional
    persistent_keepalive = int(db.get_setting("persistent_keepalive") or 25)

    # 4) get client private key + address from peer record
    # If you store private key in filesystem, DB should store path. Adapt accordingly.
    if getattr(peer, "private_key", None):
        client_private_key = peer.private_key
    else:
        # recommended: load from filesystem using controller helper
        client_private_key = db.load_peer_private_key(peer.name)

    client_address = peer.allowed_ips or peer.address  # pick your actual field name

    # Optional: PSK if you use it
    server_preshared_key = getattr(site, "preshared_key", None) or db.get_setting("server_preshared_key")

    ctx = ClientConfigContext(
        token=token,
        expires_at=str(site.expires_at),

        client_private_key=client_private_key,
        client_address=client_address,
        client_dns=dns,

        server_public_key=server_public_key,
        server_preshared_key=server_preshared_key,
        server_endpoint=server_endpoint,

        allowed_ips=allowed_ips,
        persistent_keepalive=persistent_keepalive,
    )

    env = jinja_env()
    template = env.get_template("client.conf.j2")
    return template.render(**ctx.__dict__) + "\n"