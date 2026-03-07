import ipaddress
from konfwg.database.models import Interface, Peer

def get_free_ip(interface: Interface, peers: list[Peer]) -> str:
    """
    Return the next free peer address in the interface subnet, as /32.
    Example:
        interface.address = 10.8.0.1/24
        first peer -> 10.8.0.2/32
    """
    interface_ip = ipaddress.ip_interface(interface.address)
    network = interface_ip.network
    server_ip = interface_ip.ip
    used_ips = {server_ip}

    for peer in peers:
        try:
            peer_ip = ipaddress.ip_interface(peer.address).ip
            used_ips.add(peer_ip)
        except ValueError:
            continue
    for host in network.hosts():
        if host not in used_ips:
            return f"{host}/32"
    
    raise RuntimeError(f"No free IP addresses left in netowrk {network}")

def validate_ip(address: str) -> str:
    """
    Validate CIDR address like 10.8.0.1/24. Returns the normalized string if valid.
    """
    try:
        iface = ipaddress.ip_interface(address.strip())
    except ValueError as ex:
        raise ValueError(f"Invalid address '{address}': {ex}") from ex
    
    return str(iface)