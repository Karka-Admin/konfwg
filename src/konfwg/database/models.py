from __future__ import annotations

from sqlalchemy import Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from konfwg.database.base import Base

class Interface(Base):
    __tablename__ = "interface"
    
    interface_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    port: Mapped[str] = mapped_column(Text, nullable=False)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    private_key: Mapped[str] = mapped_column(Text, nullable=False)
    endpoint: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)

    peers: Mapped[list["Peer"]] = relationship(back_populates="interface")

class Peer(Base):
    __tablename__ = "peer"

    peer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interface_id: Mapped[int] = mapped_column(ForeignKey("interface.interface_id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    private_key: Mapped[str] = mapped_column(Text, nullable=False)
    preshared_key: Mapped[str] = mapped_column(Text, nullable=True)
    allowed_ips: Mapped[str] = mapped_column(Text, nullable=False)
    keepalive: Mapped[int] = mapped_column(Integer, nullable=True)
    active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)

    interface: Mapped["Interface"] = relationship(back_populates="peers")
    sites: Mapped[list["Site"]] = relationship(back_populates="peer")

class Site(Base):
    __tablename__ = "site"

    site_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    peer_id: Mapped[int] = mapped_column(ForeignKey("peer.peer_id"), nullable=False)
    token: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False)  # store HASH later
    expires_at: Mapped[str] = mapped_column(Text, nullable=False)
    revoked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    last_access_at: Mapped[str] = mapped_column(Text, nullable=True)

    peer: Mapped["Peer"] = relationship(back_populates="sites")

class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=True)