from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Optional
from konfwg.config import configuration


@dataclass
class WGPeerSnapshot:
    public_key: str
    preshared_key: Optional[str]
    endpoint: Optional[str]
    allowed_ips: list[str]
    keepalive: Optional[int]
    latest_handshake: Optional[int]  # unix timestamp from wg dump (or 0)
    rx_bytes: Optional[int]
    tx_bytes: Optional[int]


@dataclass
class WGInterfaceSnapshot:
    name: str
    address: list[str]
    listen_port: Optional[int] = None
    public_key: Optional[str] = None
    private_key: Optional[str] = None
    endpoint: Optional[str] = None
    peers: list[WGPeerSnapshot] = None  # filled from live state


def _run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def list_live_interfaces() -> list[str]:
    out = _run(["wg", "show", "interfaces"])
    return [x for x in out.split() if x]


def _parse_conf(path: Path) -> WGInterfaceSnapshot:
    name = path.stem
    text = path.read_text(encoding="utf-8", errors="replace")

    def find_one(key: str) -> Optional[str]:
        m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", text)
        return m.group(1).strip() if m else None

    addresses: list[str] = []
    addr_raw = find_one("Address")
    if addr_raw:
        addresses = [p.strip() for p in addr_raw.split(",") if p.strip()]

    lp = find_one("ListenPort")
    listen_port = int(lp) if lp and lp.isdigit() else None

    return WGInterfaceSnapshot(
        name=name,
        address=addresses,
        listen_port=listen_port,
        private_key=find_one("PrivateKey"),
        peers=[],
    )


def _parse_wg_dump(ifname: str) -> tuple[Optional[int], list[WGPeerSnapshot]]:
    """
    Parse `wg show <ifname> dump`
    Format:
      interface line:
        ifname private_key public_key listen_port fwmark
      peer lines:
        public_key preshared_key endpoint allowed_ips latest_handshake transfer_rx transfer_tx persistent_keepalive
    """
    try:
        dump = _run(["wg", "show", ifname, "dump"]).splitlines()
    except Exception:
        return None, []

    if not dump:
        return None, []

    # interface line
    iface_port: Optional[int] = None
    parts = dump[0].split("\t")
    if len(parts) > 3 and parts[3].isdigit():
        p = int(parts[3])
        iface_port = p if p != 0 else None

    peers: list[WGPeerSnapshot] = []
    for line in dump[1:]:
        cols = line.split("\t")
        if len(cols) < 9:
            continue

        peer_public = cols[0]
        preshared = cols[1] if cols[1] and cols[1] != "(none)" else None
        endpoint = cols[2] if cols[2] and cols[2] != "(none)" else None
        allowed_ips = [x for x in cols[3].split(",") if x]

        latest_hs = int(cols[4]) if cols[4].isdigit() else None
        rx = int(cols[5]) if cols[5].isdigit() else None
        tx = int(cols[6]) if cols[6].isdigit() else None
        keepalive = int(cols[7]) if cols[7].isdigit() else None  # (note: some wg versions shift columns; see note below)

        # Some versions: last column is keepalive (cols[8])
        if keepalive is None and len(cols) >= 9 and cols[8].isdigit():
            keepalive = int(cols[8])

        peers.append(WGPeerSnapshot(
            public_key=peer_public,
            preshared_key=preshared,
            endpoint=endpoint,
            allowed_ips=allowed_ips,
            keepalive=keepalive,
            latest_handshake=latest_hs,
            rx_bytes=rx,
            tx_bytes=tx,
        ))

    return iface_port, peers


def _enrich_live(cfg: WGInterfaceSnapshot) -> WGInterfaceSnapshot:
    # public key
    try:
        cfg.public_key = _run(["wg", "show", cfg.name, "public-key"])
    except Exception:
        pass

    # dump: listen port + peers
    port, peers = _parse_wg_dump(cfg.name)
    if port is not None:
        cfg.listen_port = port
    cfg.peers = peers

    return cfg


def get_wireguard_state() -> list[WGInterfaceSnapshot]:
    """
    Hybrid:
      - read /etc/wireguard/*.conf for interface metadata (Address/PrivateKey/ListenPort)
      - enrich with live wg state (public key, live port, peers)
      - include live-only interfaces too
    """
    by_name: dict[str, WGInterfaceSnapshot] = {}

    if configuration.WG_DIRECTORY.exists():
        for p in sorted(configuration.WG_DIRECTORY.glob("*.conf")):
            cfg = _parse_conf(p)
            by_name[cfg.name] = _enrich_live(cfg)

    for ifname in list_live_interfaces():
        if ifname not in by_name:
            by_name[ifname] = _enrich_live(WGInterfaceSnapshot(name=ifname, address=[], peers=[]))

    return list(by_name.values())
