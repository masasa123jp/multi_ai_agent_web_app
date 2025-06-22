"""
JWT ユーティリティ（HS256 / exp, sub, scope 対応）
"""
import os
import time
from typing import Dict, Any

from jose import jwt, JWTError

_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME")
_ALG    = "HS256"

def encode(payload: Dict[str, Any], exp_sec: int = 3600) -> str:
    now = int(time.time())
    payload = {**payload, "iat": now, "exp": now + exp_sec}
    return jwt.encode(payload, _SECRET, algorithm=_ALG)

def decode(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, _SECRET, algorithms=[_ALG])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
