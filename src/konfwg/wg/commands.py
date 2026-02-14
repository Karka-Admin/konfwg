from __future__ import annotations

import subprocess

def wg_genkey() -> str:
    return subprocess.check_output(["wg", "genkey"], text=True).strip()

def wg_pubkey(private_key: str) -> str:
    return subprocess.check_output(["wg", "pubkey"], input=private_key, text=True).strip()

def wg_genpsk() -> str:
    return subprocess.check_output(["wg", "genpsk"], text=True).strip()