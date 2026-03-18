from __future__ import annotations

from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from konfwg.config import configuration
from konfwg.database.controller import DBController
from konfwg.database.models import Site
from konfwg.wg.render import ensure_client_bundle
from konfwg.security import (
    COOKIE_NAME,
    COOKIE_TTL,
    create_cookie,
    read_cookie,
    verify_password,
)

app = FastAPI(title="konfwg")
templates = Jinja2Templates(directory=str(configuration.CODE_PATH / "src" / "konfwg" / "web" / "templates"))

def check_site_validity(token: str) -> Site:
    db = DBController()
    try:
        site = db.get_site_by_token(token)
        if site is None:
            raise HTTPException(status_code=404, detail="Page not found")
        if site.revoked:
            raise HTTPException(status_code=404, detail="Page not found")

        expires_at = site.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        if expires_at <= now:
            site.revoked = True
            db.commit()
            raise HTTPException(status_code=404, detail="Page not found")
        return site
    finally:
        db.close()

def is_authed(request: Request, site: Site) -> bool:
    cookie_value = request.cookies.get(COOKIE_NAME)
    cookie_data = read_cookie(cookie_value)

    if cookie_data is None:
        return False
    return cookie_data.get("site_id") == site.site_id

@app.get("/conf/{token}/download")
async def download_config(request: Request, token: str):
    site = check_site_validity(token)
    if not is_authed(request, site):
        raise HTTPException(status_code=403, detail="Not authenticated")

    conf_path, qr_path = ensure_client_bundle(token=token)

    return FileResponse(
        path=conf_path,
        media_type="text/plain",
        filename=f"peer-{site.peer_id}.conf",
    )

@app.get("/conf/{token}/qr")
async def get_qr(request: Request, token: str):
    site = check_site_validity(token)
    if not is_authed(request, site):
        raise HTTPException(status_code=403, detail="Not authenticated")

    conf_path, qr_path = ensure_client_bundle(token=token)

    return FileResponse(
        path=qr_path,
        media_type="image/png",
        filename=f"peer-{site.peer_id}.png",
    )

@app.get("/conf/{token}")
async def get_login(request: Request, token: str):
    site = check_site_validity(token)
    if is_authed(request, site):
        db = DBController()
        try:
            db_site = db.get_site_by_token(token)
            db_site.last_access_at = datetime.now(timezone.utc)
            db.commit()
        finally:
            db.close()
        conf_path, qr_path = ensure_client_bundle(token=token)
        config_text = conf_path.read_text(encoding="utf-8")
        return templates.TemplateResponse(
            request=request,
            name="portal.html",
            context={
                "request": request,
                "token": token,
                "site": site,
                "config_text": config_text,
                "qr_url": f"/conf/{token}/qr",
                "download_url": f"/conf/{token}/download",
            }
        )
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "token": token,
            "site": site,
            "error": None,
        },
    )

@app.post("/conf/{token}/login")
async def post_login(request: Request, token: str, password: str = Form(...)):
    site = check_site_validity(token)
    if not verify_password(password, site.password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "token": token,
                "site": site,
                "error": "Wrong password",
            },
            status_code=401,
        )
    response = RedirectResponse(url=f"/conf/{token}", status_code=303)
    response.set_cookie(
        key=COOKIE_NAME,
        value=create_cookie(site.site_id),
        max_age=COOKIE_TTL,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return response

@app.post("/conf/{token}/logout")
async def post_logout(token: str):
    response = RedirectResponse(url=f"/conf/{token}", status_code=303)
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
    )
    return response

@app.get("/health")
def health():
    return {"status": "ok"}
