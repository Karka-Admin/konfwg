from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from konfwg.database.engine import SessionLocal
from konfwg.database.models import Interface, Peer, Site

def now_iso():
    return datetime.now(timezone.utc).isoformat()

class DBController:
    """
    Thin wrapper around SQLAlchemy for database CRUD methods
    """
    # GENERAL
    def __init__(self):
        self.database = SessionLocal()
        
    def close(self):
        self.database.close()
    
    def commit(self):
        self.database.commit()
        
    def rollback(self):
        self.database.rollback()
    
    # HELPERS
    def get_next_free_ip(interface: Interface) -> str:
        print("Still working on it.")
        
    # INTERFACE
    ## READ
    def get_interface(self, name: str) -> Optional[Interface]:
        """
        Returns a specific interface based on name
        
        :param name: Interface name
        :type name: str
        :return: Interface
        :rtype: Interface | None
        """
        return self.database.query(Interface).filter(Interface.name == name).one_or_none()
    
    def get_interfaces(self):
        """
        Returns all interfaces
        """
        return self.database.query(Interface).all()
    
    ## CREATE
    def create_interface(
        self,
        *,
        name: str,
        address: str,
        port: int | str,
        private_key: str,
        public_key: str,
        endpoint: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Interface:
        

    
    # PEER
    ## READ
    def get_peer(self, name: str) -> Optional[Peer]:
        """
        Returns a specific peer based on name
        
        :param name: Peer name
        :type name: str
        :return: Peer
        :rtype: Peer | None
        """
        return self.database.query(Peer).filter(Peer.name == name).one_or_none()
    
    def get_peers(self):
        """
        Returns all peers
        """
        return self.database.query(Peer).all()
    
    ## CREATE
    def create_peer(
        self,
        *,
        interface: Interface,
        name: str,
        address: str,
        public_key: str,
        private_key: str,
        preshared_key: Optional[str],
        allowed_ips: str,
        keepalive: Optional[str],
        comment: Optional[str] = None
    ) -> Peer:
        peer = Peer(
            interface_id = interface.interface_id,
            name=name,
            address=address,
            public_key=public_key,
            private_key=private_key,
            preshared_key=preshared_key,
            allowed_ips=allowed_ips,
            keepalive=keepalive,
            active=1,
            created_at=now_iso(),
            comment=comment
        )
        self.database.add(peer)
        self.database.flush()
        return peer

    # SITES
    ## READ
    def get_site(self, token: str) -> Optional[Site]:
        """
        Get a specific site based on its URL token
        
        :param token: URL token
        :type token: str
        :return: Site
        :rtype: Site | None
        """
        return self.database.query(Site).filter(Site.token == token).one_or_none()

    def get_sites(self):
        """
        Returns all sites
        """
        return self.database.query(Site).all()

    ## CREATE
    def create_site(
        self,
        *,
        peer: Peer,
        token: str,
        password: str,
        expires_at: str,
    ) -> Site:
        """
        Creates a site
        
        :param self: Description
        :param peer: Description
        :type peer: Peer
        :param token: Description
        :param str: Description
        :param password: Description
        :type password: str
        :param expires_at: Description
        :type expires_at: str
        :return: Description
        :rtype: Site
        """
        site = Site(
            peer_id=peer.peer_id,
            token=token,
            password=password,
            expires_at=expires_at,
            revoked=0,
            created_at=now_iso(),
            last_access_at=None,
        )
        self.database.add(site)
        return site