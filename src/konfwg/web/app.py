import asyncio
import os
import hashlib
import hmac
from datetime import datetime, timezone
from pathlib import Path
from typing import Union

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from konfwg.database.engine import SessionLocal
from konfwg.database.models import Site
from konfwg.config import configuration

app = FastAPI(title="konfwg")

BASE_PATH = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_PATH / "templates"))

def get_expiration_date(value: Union[str, datetime]) -> datetime:
    """
    Normalize expires_at to a timezone-aware UTC datetime, using stdlib only.
    Accepts:
      - ISO strings (with +00:00 or Z)
      - datetime (naive or tz-aware)
    """
    if isinstance(value, str):
        # Support Zulu timestamps if they exist in your DB/API
        value = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(value)
    else:
        dt = value

    # Ensure tz-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Normalize to UTC
    return dt.astimezone(timezone.utc)

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

        expires_at = get_expiration_date(site.expires_at)
        now = datetime.now(timezone.utc)
        if now >= expires_at:
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

    p = configuration.TMP_PATH / token / "peer.conf"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Config missing")
    return FileResponse(str(p), media_type="text/plain", filename="wg.conf")

@app.post("/conf/{token}/qr")
def qr(token: str, password: str = Form(...)):
    site = get_site(token)
    verify_password(site, password)

    p = configuration.TMP_PATH / token / "peer.png"
    if not p.exists():
        raise HTTPException(status_code=404, detail="QR missing")
    return FileResponse(str(p), media_type="image/png")

@app.get("/health")
def health():
    return {"status": "ok"}
