import asyncio
import os
import hashlib
import hmac
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from konfwg.database.engine import SessionLocal
from konfwg.database.models import Site

app = FastAPI(title="konfwg")

BASE_PATH = Path(__file__).resolve().parent
TMP_ROOT = Path("/var/lib/konfwg/tmp")

templates = Jinja2Templates(directory=str(BASE_PATH / "templates"))

def utc_now() -> datetime:
    """
    Returns global time, not tied to the server's or client's local timezone
    """
    return datetime.now(timezone.utc)

def parse_iso(value: str) -> datetime:
    """
    Converts Zulu time to Python's datetime object
    """
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)

def sha256_hex(value: str) -> str:
    """
    Encrypts string text with sha256 stored as HEX
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def verify_password(site: Site, password: str) -> None:
    if not hmac.compare_digest(sha256_hex(password), site.password):
        raise HTTPException(status_code=401, detail="Wrong password")

def get_site(token: str) -> Site:
    database = SessionLocal()
    try:
        site = database.query(Site).filter(Site.token == token).first()
        if not site:
            raise HTTPException(status_code=404, detail="Not found")

        if int(site.revoked) == 1:
            raise HTTPException(status_code=410, detail="Revoked")

        if utc_now() >= parse_iso(site.expires_at):
            site.revoked = 1
            database.commit()
            raise HTTPException(status_code=410, detail="Expired")

        return site
    finally:
        database.close()

@app.get("/conf/{token}")
def login_page(request: Request, token: str):
    get_site(token)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "token": token, "error": None},
    )

@app.post("/conf/{token}/portal")
def portal_page(request: Request, token: str, password: str = Form(...)):
    site = get_site(token)
    try:
        verify_password(site, password)
    except HTTPException:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "token": token, "error": "Wrong password"},
            status_code=401,
        )

    return templates.TemplateResponse(
        "portal.html",
        {
            "request": request,
            "token": token,
            "expires_at": site.expires_at,
            "password": password,  # hidden field approach
        },
    )

@app.post("/conf/{token}/download")
def download(token: str, password: str = Form(...)):
    site = get_site(token)
    verify_password(site, password)

    p = TMP_ROOT / token / "peer.conf"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Config missing")
    return FileResponse(str(p), media_type="text/plain", filename="wg.conf")

@app.post("/conf/{token}/qr")
def qr(token: str, password: str = Form(...)):
    site = get_site(token)
    verify_password(site, password)

    p = TMP_ROOT / token / "peer.png"
    if not p.exists():
        raise HTTPException(status_code=404, detail="QR missing")
    return FileResponse(str(p), media_type="image/png")

@app.get("/health")
def health():
    return {"status": "ok"}