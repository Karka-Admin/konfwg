# konfwg

konfwg is a lightweight WireGuard configuration management tool built around Infrastructure-as-Code principles.

It combines:
- a CLI for managing WireGuard interfaces and peers,
- a FastAPI web application for temporary peer configuration delivery,
- and an Ansible deployment stack for provisioning the full environment.

The project is designed to stay simple, reproducible, and usable on low-resource systems.

## What it does

konfwg currently provides:

- WireGuard interface management
- WireGuard peer management
- SQLite-backed metadata storage through SQLAlchemy
- temporary password-protected configuration pages
- QR code generation for mobile WireGuard clients
- server and client configuration rendering from templates
- Ansible-based deployment of system dependencies and service configuration

## Current architecture

The project is split into two main parts:

1. **Application/tooling**
   - CLI built with Typer
   - FastAPI web app
   - SQLAlchemy models and controller
   - WireGuard config rendering logic

2. **Infrastructure**
   - Ansible roles for system setup
   - WireGuard installation/configuration
   - Caddy reverse proxy
   - konfwg service deployment

## Project structure

```text
.
├── ansible
│   ├── ansible.cfg
│   ├── inventories
│   │   ├── group_vars
│   │   │   └── all
│   │   │       ├── caddy.yml
│   │   │       ├── konfwg.yml
│   │   │       └── wireguard.yml
│   │   └── hosts.yml
│   ├── playbooks
│   │   └── site.yml
│   └── roles
│       ├── caddy
│       ├── konfwg
│       ├── system
│       └── wireguard
├── docs
│   └── documentation.md
├── LICENSE
├── pyproject.toml
├── README.md
├── setup.sh
└── src
    ├── cli
    │   └── main.py
    └── konfwg
        ├── config.py
        ├── database
        │   ├── base.py
        │   ├── controller.py
        │   ├── engine.py
        │   └── models.py
        ├── initialize.py
        ├── network.py
        ├── security.py
        ├── web
        │   ├── app.py
        │   └── templates
        │       ├── login.html
        │       └── portal.html
        └── wg
            ├── commands.py
            ├── render.py
            └── templates
                ├── client.conf.j2
                └── server.conf.j2
```

## Main components

### CLI

The CLI is responsible for:
- creating, updating, listing, and deleting database objects,
- generating peer metadata,
- preparing data that later gets applied to WireGuard.

The CLI does **not** automatically apply all WireGuard changes directly in every case, because the project separates lower-privileged application operations from privileged system config writes.

### Web app

The FastAPI app provides:
- password-protected temporary peer access pages,
- signed cookie-based access control,
- QR code and `.conf` download endpoints,
- token expiry and revocation checks.

### Database

The SQLite database stores:
- `Interface`
- `Peer`
- `Site`
- `AuditLog`

Relationships are configured through SQLAlchemy models.

### WireGuard rendering

The rendering layer:
- builds server configuration from interfaces and active peers,
- builds client configuration from peer + interface + site token,
- generates QR codes for client configs.

### Ansible

The Ansible stack provisions:
- base system packages,
- WireGuard,
- Caddy,
- konfwg service files and configuration.

## Requirements

### For local development

- Linux
- Python 3.11+
- virtual environment support
- WireGuard tools available if you want to test full functionality
- sudo access for privileged WireGuard sync operations

### For deployment

- a Linux VPS or server
- Ansible installed on the control machine
- SSH access to the target machine
- sudo privileges on the target host

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/konfwg.git
cd konfwg
```

### 2. Run local setup

```bash
chmod +x setup.sh
./setup.sh
```

This prepares the local Python environment and installs the project.

### 3. Review configuration

Review and adjust the inventory and group variables under:

```text
ansible/inventories/hosts.yml
ansible/inventories/group_vars/all/caddy.yml
ansible/inventories/group_vars/all/konfwg.yml
ansible/inventories/group_vars/all/wireguard.yml
```

You should verify values such as:
- domain / base URL,
- WireGuard interface settings,
- install and runtime paths,
- service-specific configuration.

## Deployment

The full deployment is done with Ansible:

```bash
cd ansible
ansible-playbook -i inventories/hosts.yml playbooks/site.yml -K
```

This applies the configured roles and deploys the system.

## Running the web app locally

For local development, the FastAPI app can be started with:

```bash
uvicorn konfwg.web.app:app --reload
```

## CLI usage

The CLI entrypoint is:

```bash
konfwg <command>
```

## Available CLI commands

### List objects

```bash
konfwg list config
konfwg list peers
konfwg list interfaces
konfwg list sites
```

### Add interface

```bash
konfwg add-interface
```

or with explicit values:

```bash
konfwg add-interface --name wg0 --address 10.8.0.1/24 --port 51820
```

### Update interface

```bash
konfwg update-interface wg0 --endpoint vpn.example.com
```

### Delete interface

```bash
konfwg delete-interface wg0
```

### Add peer

```bash
konfwg add-peer alice --iface wg0
```

This creates:
- a peer in the database,
- a temporary access site,
- a password for the portal,
- and an expiry timestamp.

### Update peer

```bash
konfwg update-peer alice --keepalive 25 --comment "Laptop"
```

### Delete peer

```bash
konfwg delete-peer alice
```

## Applying WireGuard changes

Database changes and privileged WireGuard config writes are intentionally separated.

After peer or interface changes, apply them with:

```bash
sudo konfwg sync-interface --name wg0
```

This command:
- renders the server configuration,
- writes the WireGuard config file,
- restarts the selected WireGuard interface.

## Web interface

Peer configuration is accessed through a temporary URL:

```text
https://<your-domain>/conf/<token>
```

Flow:
1. Open the URL
2. Enter the generated password
3. Access the portal
4. Download the `.conf` file or scan the QR code

## Security model

Current access flow is based on:
- unique token URLs,
- password-protected login,
- signed cookies,
- expiry timestamps,
- revoked/expired link denial.

Expired or revoked pages return `404`.

## Configuration generation

### Server config

Server WireGuard config is generated from database state through the privileged sync command.

### Client config

Client configuration bundles are generated on demand by the web layer. This avoids stale cached client configs after peer/interface updates.

## Database notes

The project currently uses SQLite through SQLAlchemy.

Main entities:
- `Interface`
- `Peer`
- `Site`
- `AuditLog`

## Notes on privileges

The project currently separates operations by privilege level:

- normal application/database operations
- privileged WireGuard config writing and interface restart

Because of that, CRUD commands do not automatically apply live WireGuard config changes.

## Troubleshooting

### Peer/interface changed but WireGuard did not update

Run:

```bash
sudo konfwg sync-interface --name wg0
```

### Portal works but downloaded config is outdated

Client bundles are generated dynamically by the web application. Make sure the latest database state is applied and the web service is running correctly.

### Interface config file still exists after deleting an interface

Deleting an interface from the database does not automatically remove any already-written privileged system config file. Clean that up manually if needed.

## Development notes

This repository currently contains both:
- the Python application/tooling code,
- the Ansible deployment structure.

Typical workflow:
1. change database/application state through CLI,
2. apply WireGuard config with privileged sync,
3. access peer portal through web app.

## License

MIT License