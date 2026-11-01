"""
=============================================================================
DARKROOM 2.0 - CRYPTOGRAPHIC KEY DERIVATION (HKDF - RFC 5869)
=============================================================================
Menyediakan derivasi kunci terpisah berdasarkan domain (Domain Separation)
menggunakan HKDF (HMAC-based Key Derivation Function) berbasis SHA-256.
=============================================================================
"""

import os
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


def derive_key_hkdf(
    passphrase: str,
    salt: bytes,
    info: bytes,
    length: int = 32
) -> bytes:
    """
    Menurunkan kunci berukuran `length` byte menggunakan HKDF-SHA256.
    
    Argumen:
        passphrase: Kata sandi atau master secret teks
        salt      : Salt kriptografis (minimal 16 byte)
        info      : Konteks domain separation (misal b"darkroom-text-gcm-v2")
        length    : Panjang kunci yang diinginkan (default 32 byte = 256 bit)
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=info,
    )
    return hkdf.derive(passphrase.encode('utf-8'))
