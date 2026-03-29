#!/bin/bash
set -euo pipefail

DOMAIN_DEFAULT="vpn.example.com"

# CHECK BASE PACKAGES
need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

install_bootstrap_packages() {
  local missing=()

  need_cmd git || missing+=("git")
  need_cmd python3 || missing+=("python3")
  need_cmd pip3 || missing+=("python3-pip")
  python3 -m venv --help >/dev/null 2>&1 || missing+=("python3-venv")
  need_cmd ansible-playbook || missing+=("ansible")

  if [ "${#missing[@]}" -gt 0 ]; then
    echo "Installing missing packages: ${missing[*]}"
    sudo apt update
    sudo apt install -y "${missing[@]}"
  else
    echo "All required bootstrap packages are already installed"
  fi
}

install_bootstrap_packages

# CHANGE DEFAULT DOMAIN AND RUN ANSIBLE
read -r -p "Enter VPN server domain [$DOMAIN_DEFAULT]: " DOMAIN
DOMAIN="${DOMAIN:-$DOMAIN_DEFAULT}"
BASE_URL="https://$DOMAIN"

cd "$(dirname "$0")/ansible"

sed -i 's|^konfwg_base_url:.*|konfwg_base_url: "'"$BASE_URL"'"|' inventories/group_vars/all/konfwg.yml
sed -i 's|^konfwg_domain:.*|konfwg_domain: "'"$DOMAIN"'"|' inventories/group_vars/all/caddy.yml

echo "Updated:"
echo "  konfwg_base_url: $BASE_URL"
echo "  konfwg_domain: $DOMAIN"

ansible-playbook -i inventories/hosts.yml playbooks/site.yml -K
