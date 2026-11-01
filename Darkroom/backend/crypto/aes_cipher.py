"""
=============================================================================
DARKROOM 2.0 - KRIPTOGRAFI MODERN: AES-256-GCM (AUTHENTICATED ENCRYPTION)
=============================================================================
Standar      : NIST SP 800-38D (Galois/Counter Mode)
Ukuran Kunci : 256 bit (32 byte) melalui HKDF-SHA256
Ukuran Nonce : 96 bit (12 byte) CSPRNG per enkripsi
Ukuran Tag   : 128 bit (16 byte) Galois MAC
Padding      : Zero-padding overhead (Stream-like behavior dalam GCM)
Autentikasi  : Full AEAD (Mencegah manipulasi bit dan padding oracle)
=============================================================================
"""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.exceptions import InvalidTag

from backend.crypto.kdf import derive_key_hkdf

GCM_MAGIC_V2 = b"GCM2"
SALT_SIZE = 16
NONCE_SIZE = 12
TAG_SIZE = 16
HKDF_INFO_AES = b"darkroom-text-gcm-v2"


def aes_encrypt(plaintext: str, key_phrase: str) -> str:
    """
    Mengenkripsi teks menggunakan AES-256-GCM dengan integritas terotentikasi.
    
    Format Keluaran (Base64):
    Base64( 'GCM2' [4B] + Salt [16B] + Nonce [12B] + Tag [16B] + Ciphertext [NB] )
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key_bytes = derive_key_hkdf(key_phrase, salt=salt, info=HKDF_INFO_AES, length=32)

    cipher = Cipher(algorithms.AES(key_bytes), modes.GCM(nonce))
    encryptor = cipher.encryptor()
    ciphertext_bytes = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()
    tag = encryptor.tag

    combined = GCM_MAGIC_V2 + salt + nonce + tag + ciphertext_bytes
    return base64.b64encode(combined).decode('utf-8')


def aes_decrypt(base64_ciphertext: str, key_phrase: str) -> str:
    """
    Mendekripsi AES-256-GCM dan memvalidasi keaslian tag.
    Mendukung fallback otomatis untuk data lama berformat legacy AES-CBC.
    """
    try:
        combined = base64.b64decode(base64_ciphertext.encode('utf-8'))
    except Exception:
        raise ValueError("Format ciphertext Base64 tidak valid!")

    # 1. Periksa apakah ciphertext merupakan format terotentikasi v2 (GCM)
    if combined.startswith(GCM_MAGIC_V2):
        min_len = len(GCM_MAGIC_V2) + SALT_SIZE + NONCE_SIZE + TAG_SIZE
        if len(combined) < min_len:
            raise ValueError("Ciphertext AES-GCM korup atau terlalu pendek!")

        offset = len(GCM_MAGIC_V2)
        salt = combined[offset : offset + SALT_SIZE]
        offset += SALT_SIZE
        nonce = combined[offset : offset + NONCE_SIZE]
        offset += NONCE_SIZE
        tag = combined[offset : offset + TAG_SIZE]
        offset += TAG_SIZE
        ciphertext_bytes = combined[offset:]

        key_bytes = derive_key_hkdf(key_phrase, salt=salt, info=HKDF_INFO_AES, length=32)

        try:
            cipher = Cipher(algorithms.AES(key_bytes), modes.GCM(nonce, tag))
            decryptor = cipher.decryptor()
            plaintext_bytes = decryptor.update(ciphertext_bytes) + decryptor.finalize()
            return plaintext_bytes.decode('utf-8')
        except InvalidTag:
            raise ValueError("Autentikasi AES-GCM gagal: Kunci salah atau ciphertext telah dimanipulasi!")

    # 2. Backward Compatibility: Fallback ke Legacy AES-256-CBC
    return _legacy_aes_cbc_decrypt(combined, key_phrase)


def _legacy_aes_cbc_decrypt(combined: bytes, key_phrase: str) -> str:
    """Mendekripsi data arsip versi lama yang dienkripsi dengan AES-256-CBC."""
    if len(combined) < 16:
        raise ValueError("Ciphertext tidak valid atau terlalu pendek!")

    legacy_key = hashlib.sha256(key_phrase.encode('utf-8')).digest()
    iv = combined[:16]
    ciphertext_bytes = combined[16:]

    try:
        cipher = Cipher(algorithms.AES(legacy_key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext_bytes) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        plaintext_bytes = unpadder.update(padded_data) + unpadder.finalize()
        return plaintext_bytes.decode('utf-8')
    except Exception:
        raise ValueError("Dekripsi legacy AES-CBC gagal: Kunci salah atau data korup!")
