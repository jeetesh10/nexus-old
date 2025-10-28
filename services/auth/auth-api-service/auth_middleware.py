from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import requests
import os
import time

security = HTTPBearer()

KEYCLOAK_URL = os.getenv('KEYCLOAK_URL', 'http://localhost:8180')
REALM = os.getenv('KEYCLOAK_REALM', 'nexus')
JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"
ALGORITHMS = ["RS256"]
_jwks_cache = None
_jwks_cache_time = 0

def get_jwks():
    global _jwks_cache, _jwks_cache_time
    if _jwks_cache and (time.time() - _jwks_cache_time) < 3600:
        return _jwks_cache
    resp = requests.get(JWKS_URL)
    resp.raise_for_status()
    _jwks_cache = resp.json()
    _jwks_cache_time = time.time()
    return _jwks_cache

def decode_jwt(token: str):
    jwks = get_jwks()
    unverified_header = jwt.get_unverified_header(token)
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            try:
                return jwt.decode(token, key, algorithms=ALGORITHMS, audience=os.getenv('KEYCLOAK_CLIENT_ID', 'mongodb-client'))
            except JWTError as e:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Public key not found in JWKS")

def auth_middleware(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return decode_jwt(credentials.credentials)
