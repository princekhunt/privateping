"""
Small, dependency-free security helpers shared by the views and consumers:

* rate limiting backed by Django's cache (Redis in production)
* client IP resolution that is safe behind a single trusted proxy
* strict validation of the public keys clients upload
"""
import base64
import binascii
import json
import time

from django.conf import settings
from django.core.cache import cache


# --------------------------------------------------------------------------- #
# Client IP
# --------------------------------------------------------------------------- #
def client_ip(request_or_scope):
    """
    Returns the client IP. When TRUST_X_FORWARDED_FOR is enabled (production,
    behind Heroku's router) the *last* X-Forwarded-For entry is used, because
    that is the one appended by the trusted proxy; earlier entries are
    attacker-controlled.
    """
    if isinstance(request_or_scope, dict):  # ASGI scope (websockets)
        headers = dict(request_or_scope.get("headers") or [])
        xff = headers.get(b"x-forwarded-for", b"").decode("latin-1")
        client = request_or_scope.get("client") or ("", 0)
        remote = client[0] if client else ""
    else:
        xff = request_or_scope.META.get("HTTP_X_FORWARDED_FOR", "")
        remote = request_or_scope.META.get("REMOTE_ADDR", "")

    if getattr(settings, "TRUST_X_FORWARDED_FOR", False) and xff:
        return xff.split(",")[-1].strip() or remote
    return remote or "unknown"


# --------------------------------------------------------------------------- #
# Rate limiting (fixed window)
# --------------------------------------------------------------------------- #
def _key(scope, ident):
    return f"rl:{scope}:{ident}"


def is_rate_limited(scope, ident, limit, window):
    """Returns True if `ident` has already used `limit` hits in the current window."""
    return cache.get(_key(scope, ident), 0) >= limit


def hit(scope, ident, window):
    """Records one hit and returns the new count."""
    key = _key(scope, ident)
    if cache.add(key, 1, timeout=window):
        return 1
    try:
        return cache.incr(key)
    except ValueError:  # key expired between add() and incr()
        cache.set(key, 1, timeout=window)
        return 1


def check_and_hit(scope, ident, limit, window):
    """Records a hit; returns True if the caller is now over the limit."""
    return hit(scope, ident, window) > limit


def reset(scope, ident):
    cache.delete(_key(scope, ident))


class TokenBucket:
    """In-memory per-connection limiter for websocket consumers."""

    def __init__(self, rate, burst):
        self.rate = float(rate)
        self.capacity = float(burst)
        self.tokens = float(burst)
        self.updated = time.monotonic()

    def allow(self):
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


# --------------------------------------------------------------------------- #
# Public key validation
# --------------------------------------------------------------------------- #
class InvalidKey(ValueError):
    pass


_PRIVATE_JWK_FIELDS = {"d", "p", "q", "dp", "dq", "qi", "oth", "k"}
MAX_JWK_LENGTH = 4096


def _b64url_len(value):
    if not isinstance(value, str) or not value:
        raise InvalidKey("missing key material")
    try:
        return len(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))
    except (binascii.Error, ValueError):
        raise InvalidKey("bad base64url")


def _load_jwk(raw):
    if not isinstance(raw, str) or not raw or len(raw) > MAX_JWK_LENGTH:
        raise InvalidKey("key missing or too large")
    try:
        jwk = json.loads(raw)
    except json.JSONDecodeError:
        raise InvalidKey("key is not JSON")
    if not isinstance(jwk, dict):
        raise InvalidKey("key is not a JWK object")
    if _PRIVATE_JWK_FIELDS & set(jwk):
        # Never accept (and therefore never store) private key material.
        raise InvalidKey("private key material is not allowed")
    return jwk


def clean_encryption_jwk(raw):
    """Validates an RSA-OAEP-256 public key and returns a canonical JSON string."""
    jwk = _load_jwk(raw)
    if jwk.get("kty") != "RSA":
        raise InvalidKey("encryption key must be RSA")
    n_len = _b64url_len(jwk.get("n"))
    if n_len < 256:  # 2048 bits
        raise InvalidKey("RSA key must be at least 2048 bits")
    if n_len > 512:  # 4096 bits
        raise InvalidKey("RSA key too large")
    _b64url_len(jwk.get("e"))
    alg = jwk.get("alg", "RSA-OAEP-256")
    if alg != "RSA-OAEP-256":
        raise InvalidKey("encryption key must use RSA-OAEP-256")
    clean = {"kty": "RSA", "n": jwk["n"], "e": jwk["e"], "alg": "RSA-OAEP-256", "ext": True,
             "key_ops": ["encrypt"]}
    return json.dumps(clean, separators=(",", ":"), sort_keys=True)


def clean_signing_jwk(raw):
    """Validates an ECDSA P-256 public key and returns a canonical JSON string."""
    jwk = _load_jwk(raw)
    if jwk.get("kty") != "EC" or jwk.get("crv") != "P-256":
        raise InvalidKey("signing key must be EC P-256")
    if _b64url_len(jwk.get("x")) != 32 or _b64url_len(jwk.get("y")) != 32:
        raise InvalidKey("bad EC point")
    clean = {"kty": "EC", "crv": "P-256", "x": jwk["x"], "y": jwk["y"], "ext": True,
             "key_ops": ["verify"]}
    return json.dumps(clean, separators=(",", ":"), sort_keys=True)
