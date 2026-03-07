from __future__ import annotations

import secrets

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates

from passlib.context import CryptContext

from konfwg.config import configuration

from konfwg.database import controller
from konfwg.database.models import Site

app = FastAPI(title="konfwg")
templates = Jinja2Templates(directory=str(configuration.CODE_PATH / "src" / "konfwg" / "web" / "templates"))
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto") # STILL NOT USED

# HELPERS
def get_valid_site(token: str) -> Site | None:

# WORK IN PROGRESS
@app.get("/conf/{token}")
async def get_login(request: Request, token: str):



    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "token": token,
        },
    )

@app.get("/health")
def health():
    return {"status": "ok"}
