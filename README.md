# KonfWG

Automated WireGuard VPN deployment and peer management tool for Linux environments.

KonfWG is a lightweight VPN administration system designed to simplify the deployment, configuration, and management of WireGuard VPN servers and clients. The project combines infrastructure automation, configuration generation, and secure client distribution into a single workflow suitable for small-scale server environments, homelabs, and educational use cases.

The system provides:

- Automated WireGuard server deployment using Ansible
- VPN interface and peer management
- Automatic IP allocation
- Secure temporary client configuration portals
- QR code generation for mobile clients
- HTTPS reverse proxy integration with Caddy
- Persistent configuration storage using SQLite

---

# Features

## Infrastructure Automation

- Automated Linux server preparation
- WireGuard installation and configuration
- Automatic Caddy reverse proxy setup
- Automatic HTTPS certificate provisioning using Let's Encrypt
- Systemd service configuration
- IP forwarding and firewall configuration

## VPN Management

- Create and manage WireGuard interfaces
- Add, update, and remove VPN peers
- Automatic key generation
- Automatic IP address assignment
- WireGuard configuration rendering
- Interface synchronization with the operating system

## Secure Configuration Distribution

- Temporary configuration download portals
- Password-protected client access
- Expiring access tokens
- QR code generation for mobile WireGuard clients
- Signed session cookies

## Web Interface

- FastAPI-based lightweight web portal
- Secure configuration delivery
- HTTPS support through Caddy
- Mobile-friendly QR access

---

# Architecture Overview

KonfWG consists of several integrated components:

| Component | Purpose |
|---|---|
| WireGuard | VPN tunneling |
| FastAPI | Web application |
| SQLite | Persistent storage |
| SQLAlchemy | ORM and database access |
| Caddy | Reverse proxy and TLS |
| Ansible | Infrastructure automation |
| Typer | Command-line interface |

The system architecture follows a modular approach:

```text
Administrator
      |
      v
  KonfWG CLI
      |
      v
 SQLite Database
      |
      +------------------+
      |                  |
      v                  v
WireGuard           FastAPI Portal
      |                  |
      v                  v
 VPN Clients      Temporary Config Access
```

---

# Project Structure

```text
konfwg/
├── ansible/
│   ├── inventories/
│   ├── playbooks/
│   └── roles/
├── src/
│   ├── cli/
│   └── konfwg/
│       ├── database/
│       ├── web/
│       ├── wg/
│       └── templates/
├── setup.sh
├── pyproject.toml
└── README.md
```

---

# Requirements

## Supported Operating Systems

- Debian 12+
- Ubuntu 22.04+

## Required Software

The setup process installs all required dependencies automatically, including:

- Python 3
- WireGuard
- Caddy
- SQLite
- iptables
- Ansible

---

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/Karka-Admin/konfwg.git
cd konfwg
```

## 2. Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:

- Install required packages
- Configure Ansible
- Ask for VPN domain name
- Configure Caddy
- Deploy KonfWG
- Start required services

---

# Configuration

Main configuration file:

```text
/etc/konfwg/konfwg.conf
```

Example configuration:

```ini
BASE_URL=https://vpn.example.com

WG_DIRECTORY=/etc/wireguard

DB_PATH=/var/lib/konfwg
TMP_PATH=/tmp/konfwg
LOG_PATH=/var/log/konfwg

DEFAULT_TTL=900
DEFAULT_HITS=1

SECRET=CHANGE_ME
```

---

# Usage

## Check System Status

```bash
konfwg status
```

---

## Create VPN Interface

```bash
konfwg add-interface \
    --name wg0 \
    --address 10.8.0.1/24 \
    --port 51820
```

---

## Add VPN Peer

```bash
konfwg add-peer \
    --iface wg0 \
    --name client1
```

The command automatically:

- Generates keys
- Allocates a free IP address
- Creates WireGuard client configuration
- Generates QR code
- Creates temporary access portal

Example output:

```text
Peer created successfully

Access URL:
https://vpn.example.com/conf/abc123

Temporary password:
X9Kd2LqP
```

---

## Synchronize Interface

Apply generated configuration to WireGuard:

```bash
sudo konfwg sync-interface --name wg0
```

---

## List Existing Objects

### List Interfaces

```bash
konfwg list interfaces
```

### List Peers

```bash
konfwg list peers
```

### List Temporary Sites

```bash
konfwg list sites
```

---

## Remove Peer

```bash
konfwg delete-peer --name client1
```

---

# Client Configuration Portal

KonfWG generates temporary HTTPS portals for secure client delivery.

Portal features:

- Password-protected access
- Temporary availability
- QR code generation
- Direct `.conf` download
- Mobile WireGuard onboarding support

Portal URL format:

```text
https://vpn.example.com/conf/<token>
```

---

# Security Features

## Implemented Security Measures

- Password hashing using bcrypt
- Signed authentication cookies
- HTTPS-only communication
- Secure temporary access tokens
- Expiring configuration portals
- Restricted filesystem permissions
- Limited sudo permissions
- Isolated service account

## Service User

KonfWG runs under a dedicated system user:

```text
konfwg
```

---

# Database Model

The system uses SQLite with SQLAlchemy ORM.

Main entities:

| Entity | Purpose |
|---|---|
| Interface | Stores WireGuard interface configuration |
| Peer | Stores VPN client information |
| Site | Stores temporary portal access information |

---

# Services

## Systemd Service

KonfWG web application runs as:

```text
konfwg.service
```

## WireGuard Service

```text
wg-quick@wg0
```

## Caddy Service

```text
caddy.service
```

---

# Troubleshooting

## Check Service Status

```bash
sudo systemctl status konfwg
sudo systemctl status caddy
sudo systemctl status wg-quick@wg0
```

---

## View Logs

```bash
journalctl -u konfwg -f
```

---

## Restart Services

```bash
sudo systemctl restart konfwg
sudo systemctl restart caddy
sudo systemctl restart wg-quick@wg0
```

---

# Development

## Development Environment

Recommended setup:

- Visual Studio Code
- WSL2
- Debian environment
- Python virtual environment

## Install Development Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -e .
```

---

# Intended Use

KonfWG was developed as a bachelor thesis project focused on simplifying WireGuard VPN administration through automation and infrastructure-as-code principles.

The project demonstrates:

- Linux server automation
- Secure configuration management
- VPN deployment workflows
- Infrastructure provisioning
- Python backend development
- Web-based configuration delivery

---

# License

This project is intended for educational and research purposes.

Please review the repository for licensing information before production use.
