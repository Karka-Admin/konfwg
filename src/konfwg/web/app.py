from __future__ import annotations

from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from konfwg.config import configuration
from konfwg.database.controller import DBController
from konfwg.database.models import Site

app = FastAPI(title="konfwg")
templates = Jinja2Templates(directory=str(configuration.CODE_PATH / "src" / "konfwg" / "web" / "templates"))

def check_site_validity(token: str) -> Site:
    db = DBController()
    try:
        site = db.get_site(token)
        if site is None:
            raise HTTPException(status_code=404, detail="Page not found")
        if site.revoked:
            raise HTTPException(status_code=404, detail="Page not found")

        expires_at = datetime.fromisoformat(site.expires_at)
        now = datetime.now(timezone.utc)
        if expires_at <= now:
            site.revoked = True
            db.commit()
            raise HTTPException(status_code=404, detail="Page not found")
        return site
    finally:
        db.close()

@app.get("/conf/{token}")
async def get_login(request: Request, token: str):
    site = check_site_validity()

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "token": token,
            "site": site,
        },
    )

@app.get("/health")
def health():
    return {"status": "ok"}
