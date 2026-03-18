from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from konfwg.database.engine import SessionLocal
from konfwg.database.models import Interface, Peer, Site

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

class DBController:
    """
    Thin wrapper around SQLAlchemy for database CRUD methods
    """
    #################
    #### GENERAL ####
    #################
    def __init__(self) -> None:
        self.database = SessionLocal()
        
    def close(self) -> None:
        self.database.close()
    
    def commit(self) -> None:
        self.database.commit()
        
    def rollback(self) -> None:
        self.database.rollback()
    
    ###################
    #### INTERFACE ####
    ###################
    def create_interface(self, *, name: str, address: str, port: int, private_key: str, public_key: str, endpoint: Optional[str] = None, comment: Optional[str] = None) -> Interface:
        name = name.strip()
        address = address.strip()
        port = port
        private_key = private_key.strip()
        public_key = public_key.strip()
        endpoint = endpoint.strip() if endpoint else None
        comment = comment.strip() if comment else None

        if not name:
            raise ValueError("Interface name cannot be empty.")
        if not address:
            raise ValueError("Interface address cannot be empty.")
        if port <= 0:
            raise ValueError("Interface port must be a positive integer.")
        if not private_key:
            raise ValueError("Interface private key cannot be empty.")
        if not public_key:
            raise ValueError("Interface public key cannot be empty.")

        if self.get_interface_by_name(name):
            raise ValueError(f"Interface '{name}' already exists.")

        existing_addr = (self.database.query(Interface).filter(Interface.address == address).one_or_none())
        if existing_addr:
            raise ValueError(f"Interface address '{address}' already exists (interface '{existing_addr.name}').")

        interface = Interface(
            name=name,
            address=address,
            port=port,
            public_key=public_key,
            private_key=private_key,
            endpoint=endpoint,
            created_at=now_utc(),
            updated_at=None,
            comment=comment,
        )
        self.database.add(interface)
        self.database.flush()
        return interface

    def get_interface_by_name(self, name: str) -> Optional[Interface]:
        """
        Returns a specific interface based on name
        """
        return self.database.query(Interface).filter(Interface.name == name.strip()).one_or_none()
    
    def get_interface_by_id(self, interface_id: int) -> Optional[Interface]:
        """
        Returns a specific interface based on id
        """
        return self.database.query(Interface).filter(Interface.interface_id == interface_id).one_or_none()

    def get_interface_by_ip(self, address: str) -> Optional[Interface]:
        """
        Returns a specific interface by ip
        """
        return self.database.query(Interface).filter(Interface.address == address.strip()).one_or_none()
    
    def list_interfaces(self) -> list[Interface]:
        """
        Returns all interfaces
        """
        return self.database.query(Interface).all()
    
    def update_interface(self, interface_id: int, *, name: str | None = None, address: str | None = None, port: int | None = None, private_key: str | None = None, public_key: str | None = None, endpoint: str | None = None, comment: str | None = None) -> Interface:
        interface = self.get_interface_by_id(interface_id)
        if interface is None:
            raise ValueError(f"Interface with id '{interface_id}' not found.")

        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Interface name cannot be empty.")
            existing = self.get_interface_by_name(name)
            if existing and existing.interface_id != interface_id:
                raise ValueError(f"Interface '{name}' already exists.")
            interface.name = name

        if address is not None:
            address = address.strip()
            if not address:
                raise ValueError("Interface address cannot be empty.")
            existing = self.get_interface_by_ip(address)
            if existing and existing.interface_id != interface_id:
                raise ValueError(
                    f"Interface address '{address}' already exists (interface '{existing.name}')."
                )
            interface.address = address

        if port is not None:
            port = int(port)
            if port <= 0:
                raise ValueError("Interface port must be a positive integer.")
            interface.port = port

        if private_key is not None:
            private_key = private_key.strip()
            if not private_key:
                raise ValueError("Interface private key cannot be empty.")
            interface.private_key = private_key

        if public_key is not None:
            public_key = public_key.strip()
            if not public_key:
                raise ValueError("Interface public key cannot be empty.")
            interface.public_key = public_key

        if endpoint is not None:
            endpoint = endpoint.strip()
            interface.endpoint = endpoint if endpoint else None

        if comment is not None:
            comment = comment.strip()
            interface.comment = comment if comment else None

        interface.updated_at = now_utc()
        self.database.flush()
        return interface
    
    def delete_interface_by_id(self, interface_id: int) -> None:
        interface = self.get_interface_by_id(interface_id)
        if interface is None:
            raise ValueError(f"Interface with id '{interface_id}' not found.")

        self.database.delete(interface)
        self.database.flush()
    
    def delete_interface_by_name(self, name: str) -> None:
        interface = self.get_interface_by_name(name)
        if interface is None:
            raise ValueError(f"Interface '{name}' not found.")

        self.database.delete(interface)
        self.database.flush()

    ##############
    #### PEER ####
    ##############
    def create_peer(self, *, interface: Interface, name: str, address: str, public_key: str, private_key: str, preshared_key: Optional[str], allowed_ips: str, keepalive: Optional[int], comment: Optional[str] = None) -> Peer:
        """
        Inserts a new peer into database.
        """
        if interface.interface_id is None:
            raise ValueError("Interface must be persisted before creating a peer.")

        name = name.strip()
        address = address.strip()
        public_key = public_key.strip()
        private_key = private_key.strip()
        preshared_key = preshared_key.strip() if preshared_key else None
        allowed_ips = allowed_ips.strip()
        comment = comment.strip() if comment else None

        if not name:
            raise ValueError("Peer name cannot be empty.")
        if not address:
            raise ValueError("Peer address cannot be empty.")
        if not public_key:
            raise ValueError("Peer public key cannot be empty.")
        if not private_key:
            raise ValueError("Peer private key cannot be empty.")
        if not allowed_ips:
            raise ValueError("Peer allowed_ips cannot be empty.")

        existing_name = (self.database.query(Peer).filter(Peer.interface_id == interface.interface_id, Peer.name == name).one_or_none())
        if existing_name:
            raise ValueError(f"Peer '{name}' already exists on this interface.")
        
        existing_address = (self.database.query(Peer).filter(Peer.interface_id == interface.interface_id, Peer.address == address).one_or_none())
        if existing_address:
            raise ValueError(f"Peer address '{address}' already exists on this interface.")

        peer = Peer(
            interface_id=interface.interface_id,
            name=name,
            address=address,
            public_key=public_key,
            private_key=private_key,
            preshared_key=preshared_key,
            allowed_ips=allowed_ips,
            keepalive=keepalive,
            active=True,
            created_at=now_utc(),
            updated_at=None,
            comment=comment,
        )
        self.database.add(peer)
        self.database.flush()
        return peer
        
    def get_peer_by_id(self, peer_id: int) -> Optional[Peer]:
        """
        Returns a specific peer based on id
        """
        return self.database.query(Peer).filter(Peer.peer_id == peer_id).one_or_none()

    def get_peer_by_name(self, name: str) -> Optional[Peer]:
        """
        Returns a specific peer based on name
        """
        return self.database.query(Peer).filter(Peer.name == name.strip()).one_or_none()
    
    def get_first_peer_by_interface_id(self, interface_id: int) -> Optional[Peer]:
        """
        Returns the first peer matchig interface id
        """
        return self.database.query(Peer).filter(Peer.interface_id == interface_id).first()
    
    def list_peers_by_interface_id(self, interface_id: int) -> list[Peer]:
        """
        Returns all peers based on interface id
        """
        return self.database.query(Peer).filter(Peer.interface_id == interface_id).all()

    def list_peers(self) -> list[Peer]:
        """
        Returns all peers
        """
        return self.database.query(Peer).all()
    
    def update_peer(self, peer_id: int, *, name: str | None = None, address: str | None = None, public_key: str | None = None, private_key: str | None = None, preshared_key: Optional[str] = None, allowed_ips: str | None = None, keepalive: Optional[int] = None, active: bool | None = None, comment: str | None = None) -> Peer:
        peer = self.get_peer_by_id(peer_id)
        if peer is None:
            raise ValueError(f"Peer with id '{peer_id}' not found.")

        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Peer name cannot be empty.")
            existing = (self.database.query(Peer).filter(Peer.interface_id == peer.interface_id, Peer.name == name).one_or_none())
            if existing and existing.peer_id != peer_id:
                raise ValueError(f"Peer '{name}' already exists on this interface.")
            peer.name = name

        if address is not None:
            address = address.strip()
            if not address:
                raise ValueError("Peer address cannot be empty.")
            existing = (self.database.query(Peer).filter(Peer.interface_id == peer.interface_id, Peer.address == address).one_or_none())
            if existing and existing.peer_id != peer_id:
                raise ValueError(f"Peer address '{address}' already exists on this interface.")
            peer.address = address

        if public_key is not None:
            public_key = public_key.strip()
            if not public_key:
                raise ValueError("Peer public key cannot be empty.")
            peer.public_key = public_key

        if private_key is not None:
            private_key = private_key.strip()
            if not private_key:
                raise ValueError("Peer private key cannot be empty.")
            peer.private_key = private_key

        if preshared_key is not None:
            preshared_key = preshared_key.strip() if preshared_key else None
            peer.preshared_key = preshared_key

        if allowed_ips is not None:
            allowed_ips = allowed_ips.strip()
            if not allowed_ips:
                raise ValueError("Peer allowed_ips cannot be empty.")
            peer.allowed_ips = allowed_ips

        if keepalive is not None:
            peer.keepalive = keepalive

        if active is not None:
            peer.active = active

        if comment is not None:
            comment = comment.strip()
            peer.comment = comment if comment else None

        peer.updated_at = now_utc()
        self.database.flush()
        return peer
    
    def delete_peer_by_id(self, peer_id: int) -> None:
        peer = self.get_peer_by_id(peer_id)
        if peer is None:
            raise ValueError(f"Peer with id '{peer_id}' not found.")
        self.database.delete(peer)
        self.database.flush()

    def delete_peer_by_name(self, name: str) -> None:
        peer = self.get_peer_by_name(name)
        if peer is None:
            raise ValueError(f"Peer '{name}' not found.")
        self.database.delete(peer)
        self.database.flush()

    ##############
    #### SITE ####
    ##############
    def create_site(self, *, peer: Peer, token: str, password: str, expires_at: datetime) -> Site:
        """
        Creates a site.
        """
        token = token.strip()
        password = password.strip()

        if peer.peer_id is None:
            raise ValueError("Peer must be persisted before creating a site.")
        if not token:
            raise ValueError("Site token cannot be empty.")
        if not password:
            raise ValueError("Site password cannot be empty.")
        if expires_at.tzinfo is None:
            raise ValueError("Site expires_at must be timezone-aware.")

        existing_site = self.get_site_by_token(token)
        if existing_site:
            raise ValueError(f"Site token '{token}' already exists.")

        site = Site(
            peer_id=peer.peer_id,
            token=token,
            password=password,
            expires_at=expires_at,
            revoked=False,
            created_at=now_utc(),
            last_access_at=None,
        )
        self.database.add(site)
        self.database.flush()
        return site

    def get_site_by_id(self, site_id: int) -> Optional[Site]:
        """
        Returns a specific site based on id.
        """
        return self.database.query(Site).filter(Site.site_id == site_id).one_or_none()

    def get_site_by_token(self, token: str) -> Optional[Site]:
        """
        Returns a specific site based on token.
        """
        return self.database.query(Site).filter(Site.token == token.strip()).one_or_none()

    def get_site_by_peer_id(self, peer_id: int) -> Optional[Site]:
        """
        Returns the first site for a specific peer.
        """
        return self.database.query(Site).filter(Site.peer_id == peer_id).first()

    def list_sites_by_peer_id(self, peer_id: int) -> list[Site]:
        """
        Returns all sites for a specific peer.
        """
        return self.database.query(Site).filter(Site.peer_id == peer_id).all()

    def list_sites(self) -> list[Site]:
        """
        Returns all sites.
        """
        return self.database.query(Site).all()

    def update_site(self, site_id: int, *, token: str | None = None, password: str | None = None, expires_at: datetime | None = None, revoked: bool | None = None, last_access_at: datetime | None = None) -> Site:
        """
        Updates a site.
        """
        site = self.get_site_by_id(site_id)
        if site is None:
            raise ValueError(f"Site with id '{site_id}' not found.")

        if token is not None:
            token = token.strip()
            if not token:
                raise ValueError("Site token cannot be empty.")
            existing = self.get_site_by_token(token)
            if existing and existing.site_id != site_id:
                raise ValueError(f"Site token '{token}' already exists.")
            site.token = token

        if password is not None:
            password = password.strip()
            if not password:
                raise ValueError("Site password cannot be empty.")
            site.password = password

        if expires_at is not None:
            if expires_at.tzinfo is None:
                raise ValueError("Site expires_at must be timezone-aware.")
            site.expires_at = expires_at

        if revoked is not None:
            site.revoked = revoked

        if last_access_at is not None:
            if last_access_at.tzinfo is None:
                raise ValueError("Site last_access_at must be timezone-aware.")
            site.last_access_at = last_access_at

        self.database.flush()
        return site

    def delete_site_by_id(self, site_id: int) -> None:
        """
        Deletes a site by id.
        """
        site = self.get_site_by_id(site_id)
        if site is None:
            raise ValueError(f"Site with id '{site_id}' not found.")
        self.database.delete(site)
        self.database.flush()

    def delete_site_by_token(self, token: str) -> None:
        """
        Deletes a site by token.
        """
        site = self.get_site_by_token(token)
        if site is None:
            raise ValueError(f"Site with token '{token}' not found.")
        self.database.delete(site)
        self.database.flush()

    def revoke_site_by_token(self, token: str) -> Site:
        site = self.get_site_by_token(token)
        if site is None:
            raise ValueError(f"Site with token '{token}' not found.")
        site.revoked = True
        self.database.flush()
        return site