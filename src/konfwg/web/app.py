from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from konfwg.config import configuration

app = FastAPI(title="konfwg")
templates = Jinja2Templates(directory=str(configuration.CODE_PATH))


@app.get("/health")
def health():
    return {"status": "ok"}
