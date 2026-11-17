"""
Privacy-friendly bot check: self-hosted proof-of-work (the approach used by
ALTCHA, Friendly Captcha and mCaptcha) instead of a third-party CAPTCHA.

1. The server issues a challenge: a random salt + a difficulty, signed with
   SECRET_KEY and valid for a few minutes. Nothing is stored server side.
2. The browser searches for a nonce such that SHA-256("<challenge>:<nonce>")
   starts with `bits` zero bits. That takes ~1 s on a normal device, runs in a
   background Web Worker and needs no interaction.
3. The server checks the signature, expiry and hash (microseconds), and burns the
   challenge so it can only be used once.

No cookies, no fingerprinting, no third party ever sees the visitor. A bot that
wants many accounts must pay CPU time for every single one, and the difficulty
goes up automatically when an IP (or the whole site) is creating accounts fast.
"""
import hashlib
import hmac
import secrets

from django.core import signing
from django.core.cache import cache

SALT = "privateping.pow.v1"
TTL = 5 * 60          # seconds a challenge stays valid
BASE_BITS = 18
MAX_BITS = 23


class InvalidSolution(Exception):
    pass


def _recent(key):
    return cache.get(key, 0)


def difficulty(ip):
    """More work for IPs (and moments) with lots of sign-ups."""
    bits = BASE_BITS
    bits += min(4, _recent(f"pow:ip:{ip}") // 2)      # +1 bit (2x work) per 2 recent accounts
    if _recent("pow:global") > 200:                   # site-wide surge
        bits += 2
    return min(bits, MAX_BITS)


def record_success(ip):
    for key in (f"pow:ip:{ip}", "pow:global"):
        if not cache.add(key, 1, timeout=3600):
            try:
                cache.incr(key)
            except ValueError:
                cache.set(key, 1, timeout=3600)


def issue(ip):
    """Returns a signed challenge for the browser to solve."""
    bits = difficulty(ip)
    token = signing.dumps({"n": secrets.token_hex(16), "b": bits}, salt=SALT, compress=False)
    return {"challenge": token, "bits": bits}


def leading_zero_bits(digest):
    count = 0
    for byte in digest:
        if byte == 0:
            count += 8
            continue
        count += 8 - byte.bit_length()
        break
    return count


def verify(token, nonce):
    """Raises InvalidSolution unless `nonce` solves the (unused, unexpired) `token`."""
    if not isinstance(token, str) or not isinstance(nonce, str) or len(token) > 512 or not nonce.isdigit() \
            or len(nonce) > 12:
        raise InvalidSolution("malformed")
    try:
        data = signing.loads(token, salt=SALT, max_age=TTL)
    except signing.SignatureExpired:
        raise InvalidSolution("expired")
    except signing.BadSignature:
        raise InvalidSolution("bad signature")

    digest = hashlib.sha256(f"{token}:{nonce}".encode()).digest()
    if leading_zero_bits(digest) < int(data["b"]):
        raise InvalidSolution("wrong answer")

    # One use only.
    burn_key = "pow:used:" + hmac.new(b"pow", token.encode(), hashlib.sha256).hexdigest()
    if not cache.add(burn_key, 1, timeout=TTL + 60):
        raise InvalidSolution("already used")
