# konfwg

Infrastructure-as-Code driven WireGuard configuration and management toolkit

konfwg is a lightweight automation system designed to simplify deployment, configuration, and lifecycle management of WireGuard VPN servers and peers. It combines Infrastructure-as-Code principles, Ansible automation, and a Python-based API to provide a reproducible, maintainable, and extensible VPN management environment.

---

## Features

* Automated WireGuard server provisioning using Ansible
* Secure key generation and peer configuration management
* Infrastructure-as-Code approach (idempotent, reproducible deployments)
* FastAPI backend for orchestration and control
* SQLite (development) / PostgreSQL (production) support
* QR code generation for mobile client onboarding
* Caddy reverse proxy integration with automatic TLS
* Works locally (WSL2/Linux) and on remote VPS environments

---

## Architecture Overview

konfwg separates concerns into clear layers:

* Automation Layer – Ansible playbooks provision and configure infrastructure
* Application Layer – FastAPI backend manages peers, configs, and orchestration
* Data Layer – SQLite/PostgreSQL stores configuration state and metadata
* Network Layer – WireGuard handles secure encrypted tunnels

The system follows Infrastructure-as-Code principles:

* Declarative configuration
* Idempotent deployments
* Version-controlled infrastructure

---

## Project Structure

```
konfwg/
│
├── backend/            # FastAPI application
│   ├── api/            # Routes/endpoints
│   ├── models/         # Pydantic models
│   ├── services/       # Business logic
│   └── main.py         # Entry point
│
├── ansible/            # Infrastructure automation
│   ├── inventories/
│   │   ├── dev/
│   │   └── prod/
│   ├── playbooks/
│   │   ├── site.yml
│   │   └── wireguard.yml
│   └── roles/
│
├── data/               # Runtime-generated files
│   ├── keys/
│   ├── configs/
│   └── db/
│
├── docs/               # Documentation & diagrams
├── infra/              # Infrastructure definitions
├── scripts/            # Helper/setup scripts
│   └── setup.sh
│
├── konfwg.py           # CLI entry point
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/konfwg.git
cd konfwg
```

### 2. Setup environment

```bash
./scripts/setup.sh
```

This installs:

* Python dependencies
* Ansible
* Required system packages

### 3. Run backend

```bash
uvicorn backend.main:app --reload
```

### 4. Provision WireGuard server

```bash
cd ansible
ansible-playbook -i inventories/dev/hosts playbooks/site.yml
```

---

## Requirements

* Linux (Debian/Ubuntu recommended)
* Python 3.10+
* Ansible
* WireGuard
* Caddy
* qrencode

---

## Core Capabilities

### Server Provisioning

* Installs WireGuard
* Configures network interfaces
* Applies firewall rules
* Sets up secure defaults

### Peer Management

* Generates key pairs
* Creates config files
* Registers peers in database
* Produces QR codes for mobile clients

### Infrastructure Consistency

* Reproducible deployments
* Version-controlled configurations
* Automated updates

---

## Security Principles

* Minimal exposed surface
* Secure key handling
* TLS by default via Caddy
* Configuration isolation between environments
* Role-based automation separation

---

## Development vs Production

| Feature    | Development       | Production         |
| ---------- | ----------------- | ------------------ |
| Database   | SQLite            | PostgreSQL         |
| Deployment | Local/WSL         | Remote VPS         |
| TLS        | Optional          | Enforced           |
| Inventory  | `inventories/dev` | `inventories/prod` |

---

## Roadmap

* Web UI dashboard
* Multi-server orchestration
* Role-based access control
* Peer usage monitoring
* Automatic key rotation
* Containerized deployment

---

## Project Goals

konfwg aims to:

* Reduce manual VPN configuration errors
* Provide reproducible infrastructure deployments
* Enable scalable peer management
* Serve as a practical implementation of Infrastructure-as-Code principles

---

## Use Cases

* Personal VPN infrastructure
* Academic research projects
* Small team secure networking
* Lab environments
* DevOps automation demonstrations

---

## Contributing

Contributions are welcome. Please:

1. Fork the repository
2. Create a feature branch
3. Commit changes with clear messages
4. Open a pull request

---

## License

Choose a license that fits your goals (recommended: MIT or Apache-2.0 for open collaboration).

---

## Author

Karolis Riaubūnas
konfwg – WireGuard automation through Infrastructure-as-Code

---

## Why konfwg?

WireGuard is simple.
Infrastructure-as-Code is powerful.
konfwg combines both into a structured, maintainable system designed for real-world deployment and academic exploration.
