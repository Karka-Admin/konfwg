from __future__ import annotations
from datetime import datetime, timezone

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def derive_peer_address_from_allowed_ips(allowed_ips: list[str]) -> str | None:
    # Heuristic: pick first IPv4 /32 or /128 entry if present, else first entry.
    if not allowed_ips:
        return None
    for ip in allowed_ips:
        if ip.endswith("/32") or ip.endswith("/128"):
            return ip
    return allowed_ips[0]

def sync_wireguard_state(db, Interface, Peer, state) -> dict[str, int]:
    """
    Upserts Interface by Interface.name.
    Upserts Peer by (interface_id, public_key) logically.
    With your current schema constraints, fills placeholders for peer.name/address/private_key.
    """
    now = now_iso()
    stats = {"inserted_interfaces": 0, "updated_interfaces": 0, "inserted_peers": 0, "updated_peers": 0}

    for iface in state:
        # ---- Interface upsert ----
        addr = ", ".join(iface.address) if iface.address else ""
        port = str(iface.listen_port) if iface.listen_port is not None else ""
        public_key = iface.public_key or ""
        private_key = iface.private_key or ""  # required by your schema

        irow = db.query(Interface).filter(Interface.name == iface.name).one_or_none()

        if irow is None:
            # If you allow live-only interfaces with missing keys, you may want to SKIP instead of inserting blanks.
            irow = Interface(
                name=iface.name,
                address=addr,
                port=port,
                public_key=public_key,
                private_key=private_key,
                endpoint=iface.endpoint,
                created_at=now,
                updated_at=now,
                comment="Imported from host",
            )
            db.add(irow)
            db.flush()  # to get interface_id
            stats["inserted_interfaces"] += 1
        else:
            updates = False
            if irow.address != addr:
                irow.address = addr; updates = True
            if irow.port != port:
                irow.port = port; updates = True
            if irow.public_key != public_key:
                irow.public_key = public_key; updates = True
            # only overwrite private_key if we actually have one (prevents wiping)
            if iface.private_key and irow.private_key != iface.private_key:
                irow.private_key = iface.private_key; updates = True
            if irow.endpoint != iface.endpoint:
                irow.endpoint = iface.endpoint; updates = True

            if updates:
                irow.updated_at = now
                stats["updated_interfaces"] += 1

        iface_id = irow.interface_id

        # ---- Peer upsert ----
        for p in (iface.peers or []):
            allowed_ips_str = ", ".join(p.allowed_ips) if p.allowed_ips else ""
            derived_addr = derive_peer_address_from_allowed_ips(p.allowed_ips) or ""

            prow = (
                db.query(Peer)
                .filter(Peer.interface_id == iface_id, Peer.public_key == p.public_key)
                .one_or_none()
            )

            if prow is None:
                # because Peer.name is globally unique in your schema, include iface in name
                default_name = f"{iface.name}-{p.public_key[:8]}"
                prow = Peer(
                    interface_id=iface_id,
                    name=default_name,
                    address=derived_addr,          # heuristic from allowed_ips
                    public_key=p.public_key,
                    private_key="",                # required, but WG won’t provide it
                    preshared_key=p.preshared_key,
                    allowed_ips=allowed_ips_str,
                    keepalive=p.keepalive,
                    active=1,
                    created_at=now,
                    comment="Imported from wg state",
                )
                db.add(prow)
                stats["inserted_peers"] += 1
            else:
                # DO NOT overwrite prow.name/comment (user-owned fields)
                updates = False
                if prow.preshared_key != p.preshared_key:
                    prow.preshared_key = p.preshared_key; updates = True
                if prow.allowed_ips != allowed_ips_str:
                    prow.allowed_ips = allowed_ips_str; updates = True
                if prow.keepalive != p.keepalive:
                    prow.keepalive = p.keepalive; updates = True

                # keep prow.address in sync with derived address ONLY if it was empty
                if (not prow.address) and derived_addr:
                    prow.address = derived_addr; updates = True

                if updates:
                    stats["updated_peers"] += 1

    return stats