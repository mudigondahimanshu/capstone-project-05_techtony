import os
from fastapi import HTTPException, Header

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

def check_admin(authorization: str = Header(None)):
    if not ADMIN_TOKEN:
        return
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing/invalid auth header")
    if authorization.split(" ",1)[1] != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Bad token")
