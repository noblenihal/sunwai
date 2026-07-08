from fastapi import APIRouter

from .. import db

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    try:
        db.ping()
        database = "up"
    except Exception as exc:  # pragma: no cover
        database = f"down: {exc.__class__.__name__}"
    return {"service": "sunwai", "status": "ok", "database": database}
