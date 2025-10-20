# utils/helpers.py
import hashlib
def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode("utf-8")).hexdigest()
