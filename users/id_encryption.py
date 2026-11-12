import base64
import hashlib
import hmac
import struct
from django.conf import settings


# ==============================================================================
# CRYPTOGRAPHIC COMPACT ID CIPHER (FEISTEL + HMAC INTEGRITY)
# ==============================================================================

def _get_derived_keys(salt='pinnacle-id-cipher-v1'):
    """
    Derives 4 round keys for the Feistel network and 1 authentication key
    from Django's SECRET_KEY using HMAC-SHA256.
    """
    master_key = getattr(settings, 'SECRET_KEY', 'default-insecure-key-pinnacle')
    seed = hmac.new(master_key.encode('utf-8'), salt.encode('utf-8'), hashlib.sha256).digest()

    round_keys = [
        hmac.new(seed, f'round_key_{i}'.encode('utf-8'), hashlib.sha256).digest()
        for i in range(4)
    ]
    auth_key = hmac.new(seed, b'authenticator_checksum_key', hashlib.sha256).digest()
    return round_keys, auth_key


def encode_id(num, salt='pinnacle-id-cipher-v1'):
    """
    Encrypts a positive integer into a clean, 16-character URL-safe string.
    Uses a 4-round Feistel permutation over 64 bits and appends a 32-bit HMAC tag.
    """
    if num is None:
        return ''
    if hasattr(num, 'pk'):
        num = num.pk
    elif hasattr(num, 'id'):
        num = num.id

    try:
        val = int(num)
    except (ValueError, TypeError):
        return str(num)

    if val < 0:
        raise ValueError("ID to encrypt must be a positive integer.")

    round_keys, auth_key = _get_derived_keys(salt)

    # Split 64-bit integer into two 32-bit halves (Left, Right)
    L = (val >> 32) & 0xFFFFFFFF
    R = val & 0xFFFFFFFF

    # 4-round Feistel cipher
    for i in range(4):
        f = int.from_bytes(
            hmac.new(round_keys[i], struct.pack('>I', R), hashlib.sha256).digest()[:4],
            'big'
        )
        L, R = R, L ^ f

    scrambled = struct.pack('>II', L, R)
    checksum = hmac.new(auth_key, scrambled, hashlib.sha256).digest()[:4]

    # Combine 8-byte scrambled block + 4-byte checksum = 12 bytes total (16 chars base64url)
    raw = scrambled + checksum
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def decode_id(token, salt='pinnacle-id-cipher-v1'):
    """
    Decodes and cryptographically validates a 16-character encrypted ID token.
    Raises ValueError if:
    - Token is tampered with or checksum does not match
    - Token is malformed or invalid base64
    - Token is an unencrypted integer string (prevents ID guessing/enumeration)
    """
    if not token:
        raise ValueError("Empty ID token.")

    clean_token = str(token).strip()

    # Reject raw unencrypted integer IDs to prevent sequential parameter tampering
    if clean_token.isdigit():
        raise ValueError(f"Unencrypted numeric ID '{clean_token}' is not allowed in secure URLs.")

    pad = (4 - (len(clean_token) % 4)) % 4
    try:
        raw = base64.urlsafe_b64decode(clean_token + '=' * pad)
    except Exception:
        raise ValueError("Invalid characters in ID token.")

    if len(raw) != 12:
        raise ValueError(f"Invalid token length ({len(raw)} bytes instead of 12).")

    scrambled = raw[:8]
    checksum = raw[8:]

    round_keys, auth_key = _get_derived_keys(salt)
    expected_checksum = hmac.new(auth_key, scrambled, hashlib.sha256).digest()[:4]

    # Authenticated checksum validation (constant-time compare)
    if not hmac.compare_digest(checksum, expected_checksum):
        raise ValueError("Tampered or invalid ID token.")

    L, R = struct.unpack('>II', scrambled)

    # Invert 4-round Feistel cipher
    for i in reversed(range(4)):
        f = int.from_bytes(
            hmac.new(round_keys[i], struct.pack('>I', L), hashlib.sha256).digest()[:4],
            'big'
        )
        L, R = R ^ f, L

    original_id = (L << 32) | R
    return original_id


def decode_id_or_none(value, salt='pinnacle-id-cipher-v1'):
    """
    Safe helper for query parameters (e.g. ?unit=...):
    Decodes an encrypted token if provided, or converts an integer string if valid.
    Returns None if invalid.
    """
    if not value:
        return None
    val_str = str(value).strip()
    try:
        return decode_id(val_str, salt=salt)
    except ValueError:
        # Fallback if raw int was supplied in query params
        if val_str.isdigit():
            return int(val_str)
        return None


# ==============================================================================
# DJANGO PATH CONVERTER
# ==============================================================================

class EncryptedIdConverter:
    """
    Custom Django URL path converter.
    Matches 16-character base64url encrypted tokens (<eid:pk>).
    Automatically encodes integer IDs during reverse() and decodes tokens on request.
    """
    regex = r'[A-Za-z0-9_-]{16}'

    def to_python(self, value):
        return decode_id(value)

    def to_url(self, value):
        if hasattr(value, 'pk'):
            value = value.pk
        elif hasattr(value, 'id'):
            value = value.id

        # If it's already a valid 16-character encrypted token, return as-is
        if isinstance(value, str) and len(value) == 16 and not value.isdigit():
            try:
                decode_id(value)
                return value
            except Exception:
                pass

        return encode_id(value)


def register_eid_converter():
    """Safely registers the EncryptedIdConverter only once in Django's converter registry."""
    from django.urls.converters import REGISTERED_CONVERTERS
    from django.urls import register_converter
    if 'eid' not in REGISTERED_CONVERTERS:
        register_converter(EncryptedIdConverter, 'eid')
