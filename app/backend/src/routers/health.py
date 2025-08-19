from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/healthz")
async def healthz():
    return {"status": "ok"}

@router.get("/")
async def root():
    # redirect to interactive docs
    return RedirectResponse(url="/docs", status_code=302)