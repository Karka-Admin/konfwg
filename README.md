# konfwg

konfwg is a tool for managing WireGuard VPN configurations and distributing client access through temporary, password-protected web pages.

It combines:

- a CLI for managing peers and interfaces  
- a FastAPI web server for delivering configurations  
- an SQLite database for state  
- Ansible for installation and system configuration  

---

## What it does

- Creates WireGuard peers with generated keys  
- Assigns IP addresses automatically  
- Generates client configurations  
- Provides temporary access links with passwords  
- Expires access after a set time  
- Stores everything in a local database  
- Renders and applies WireGuard server configs  

Example output:

New peer KarkaLast has been created successfully.
Configuration is accessible via: https://com.example.com/conf/<token>
Password: <password>

---

## Project structure

ansible/        system setup and deployment
src/            application source code
setup.sh        installation script
pyproject.toml  Python project config

Main components:

- CLI → src/cli/main.py
- Web server → src/konfwg/web/app.py
- Database → src/konfwg/database
- WireGuard logic → src/konfwg/wg

---

## Installation

Run:

./setup.sh

The script will:

- install required packages (git, python, pip, ansible)
- prompt for your VPN domain
- update configuration values
- run the Ansible playbook

---

## Configuration

Main configuration is handled through Ansible:

- ansible/inventories/group_vars/all/konfwg.yml
- ansible/inventories/group_vars/all/caddy.yml
- ansible/inventories/group_vars/all/wireguard.yml

The domain is set during setup.

---

## Usage

### Important

Do not run the tool as root.

Use:

sudo -u konfwg konfwg <command>

---

### Create a peer

sudo -u konfwg konfwg add-peer <name>

This will:

- generate keys
- create database records
- generate a temporary access page
- print URL and password

---

### Apply WireGuard changes

sudo konfwg sync-interface --name wg0

---

### List objects

konfwg list-objects peers
konfwg list-objects interfaces
konfwg list-objects sites

---

### Update or delete

konfwg update-peer <name>
konfwg delete-peer <name>

---

### Interface management

konfwg add-interface
konfwg delete-interface <name>

---

## Web access

https://<your-domain>/conf/<token>

- protected by password  
- expires automatically  
- limited access  

---

## Notes

- WireGuard changes are not applied automatically  
- You must run sync-interface with elevated privileges  
- Database and temporary files must be owned by the konfwg user  
- Running commands as root will break permissions  

---

## License

See LICENSE file.
