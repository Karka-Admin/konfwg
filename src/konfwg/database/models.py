from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from konfwg.database.base import Base

class Interface(Base):
    __tablename__ = "interface"
    
    interface_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    address: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    private_key: Mapped[str] = mapped_column(Text, nullable=False)
    endpoint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    peers: Mapped[list["Peer"]] = relationship(
        back_populates="interface",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __str__(self):
        return f"ID: {self.interface_id}\t| {self.name} {self.address}@{self.port}"

class Peer(Base):
    __tablename__ = "peer"

    peer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interface_id: Mapped[int] = mapped_column(
        ForeignKey("interface.interface_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    address: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    public_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    private_key: Mapped[str] = mapped_column(Text, nullable=False)
    preshared_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allowed_ips: Mapped[str] = mapped_column(Text, nullable=False)
    keepalive: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    interface: Mapped["Interface"] = relationship(back_populates="peers")
    sites: Mapped[list["Site"]] = relationship(
        back_populates="peer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
    def __str__(self):
        return f"ID: {self.peer_id}\t| {self.name} {self.allowed_ips} {self.interface_id}"

class Site(Base):
    __tablename__ = "site"

    site_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    peer_id: Mapped[int] = mapped_column(
        ForeignKey("peer.peer_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_access_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    peer: Mapped["Peer"] = relationship(back_populates="sites")

    def __str__(self):
        return f"ID: {self.site_id}\t| {self.peer_id} {self.token} {self.expires_at} {self.revoked} {self.created_at} {self.last_access_at}"

class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)