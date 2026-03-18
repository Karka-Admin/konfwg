import subprocess

def wg_genkey() -> str:
    """
    Generate a WireGuard private key using `wg genkey`.
    Returns the key as a base64 string.
    """
    result = subprocess.run(
        ["wg", "genkey"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def wg_pubkey(private_key: str) -> str:
    """
    Derive a public key from a private key using `wg pubkey`.
    """
    result = subprocess.run(
        ["wg", "pubkey"],
        input=private_key,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def wg_genpsk() -> str:
    """
    Generate a WireGuard preshared key using `wg genpsk`.
    """
    result = subprocess.run(
        ["wg", "genpsk"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()

def wg_quick_down(interface: str) -> None:
    subprocess.run(["wg-quick", "down", interface])

def wg_quick_up(interface: str) -> None:
    subprocess.run(["wg-quick", "up", interface])

def wg_restart(interface: str) -> None:
    """
    Full restart WireGuard interface.
    """
    try:
        wg_quick_down(interface)
    except subprocess.CalledProcessError:
        pass
    wg_quick_up(interface)