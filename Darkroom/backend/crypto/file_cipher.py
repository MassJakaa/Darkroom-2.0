"""
=============================================================================
DARKROOM 2.0 - ENKRIPSI BERKAS DENGAN CHACHA20-POLY1305 AEAD (RFC 8439)
=============================================================================
Kriteria Tugas: Mengenkripsi berkas dengan algoritma yang BERBEDA dari teks.
- Teks menggunakan   : AES-256-GCM (NIST SP 800-38D)
- Berkas menggunakan : ChaCha20-Poly1305 AEAD (RFC 8439)

Keunggulan Ilmiah & Keamanan:
1. Menghadirkan Authenticated Encryption with Associated Data (AEAD) sejati.
2. Tag Poly1305 (16 byte) menjamin berkas foto tidak dapat dimanipulasi 1 bit pun.
3. Metadata berkas (nama asli, ukuran, timestamp) diotentikasi penuh via AAD.
4. Kunci 256-bit diturunkan via HKDF-SHA256 ber-salt 16-byte independen.
5. Mendukung fallback dekripsi legacy untuk berkas terenkripsi versi terdahulu.
=============================================================================
"""

import os
import json
import hashlib
import time
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.exceptions import InvalidTag

from backend.crypto.kdf import derive_key_hkdf

# Format Penanda File V2 (AEAD)
VAULT_MAGIC_V2 = b"DARKROOM_A20" # 12 bytes
LEGACY_MAGIC_V1 = b"DARKROOM_RAW" # 12 bytes
SALT_SIZE = 16
NONCE_SIZE = 12
HKDF_INFO_FILE = b"darkroom-file-chacha20poly1305-v2"


def encrypt_file(input_filepath: str, output_filepath: str, passphrase: str) -> dict:
    """
    Mengenkripsi file biner menggunakan ChaCha20-Poly1305 AEAD dengan autentikasi metadata.
    
    Format File Terenkripsi:
    [12B MAGIC: 'DARKROOM_A20'] + [16B Salt] + [12B Nonce] + [2B Meta Len] + [Meta JSON] + [Ciphertext + 16B Poly1305 Tag]
    """
    if not os.path.exists(input_filepath):
        raise FileNotFoundError(f"File {input_filepath} tidak ditemukan!")

    original_name = os.path.basename(input_filepath)
    original_size = os.path.getsize(input_filepath)

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key_bytes = derive_key_hkdf(passphrase, salt=salt, info=HKDF_INFO_FILE, length=32)

    meta = {
        "original_name": original_name,
        "original_size": original_size,
        "algorithm": "ChaCha20-Poly1305 (RFC 8439)",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    meta_bytes = json.dumps(meta, sort_keys=True).encode('utf-8')
    meta_len_bytes = len(meta_bytes).to_bytes(2, byteorder='big')

    # AAD: Seluruh header sebelum ciphertext diotentikasi oleh Poly1305
    aad = VAULT_MAGIC_V2 + salt + nonce + meta_len_bytes + meta_bytes

    # Baca seluruh isi file biner
    with open(input_filepath, 'rb') as f_in:
        file_data = f_in.read()

    chacha = ChaCha20Poly1305(key_bytes)
    ciphertext_and_tag = chacha.encrypt(nonce, file_data, aad)

    # Tulis berkas aman terenkripsi
    with open(output_filepath, 'wb') as f_out:
        f_out.write(aad)
        f_out.write(ciphertext_and_tag)

    return {
        "status": "LOCKED",
        "algorithm": "ChaCha20-Poly1305 AEAD",
        "input_file": input_filepath,
        "output_file": output_filepath,
        "original_size_bytes": original_size,
        "encrypted_size_bytes": os.path.getsize(output_filepath),
        "metadata": meta
    }


def decrypt_file(encrypted_filepath: str, output_filepath: str, passphrase: str) -> dict:
    """
    Mendekripsi file ChaCha20-Poly1305 AEAD dan memverifikasi integritasnya.
    Mendukung fallback otomatis untuk file legacy Darkroom v1.
    """
    if not os.path.exists(encrypted_filepath):
        raise FileNotFoundError(f"File {encrypted_filepath} tidak ditemukan!")

    with open(encrypted_filepath, 'rb') as f_in:
        magic = f_in.read(12)

        # 1. Format Terotentikasi V2 (ChaCha20-Poly1305 AEAD)
        if magic == VAULT_MAGIC_V2:
            salt = f_in.read(SALT_SIZE)
            nonce = f_in.read(NONCE_SIZE)
            meta_len_raw = f_in.read(2)
            if len(meta_len_raw) < 2:
                raise ValueError("Berkas terenkripsi rusak: Header metadata tidak lengkap!")
            meta_len = int.from_bytes(meta_len_raw, byteorder='big')
            meta_bytes = f_in.read(meta_len)
            meta = json.loads(meta_bytes.decode('utf-8'))

            aad = VAULT_MAGIC_V2 + salt + nonce + meta_len_raw + meta_bytes
            ciphertext_and_tag = f_in.read()

            key_bytes = derive_key_hkdf(passphrase, salt=salt, info=HKDF_INFO_FILE, length=32)
            chacha = ChaCha20Poly1305(key_bytes)

            try:
                plaintext_bytes = chacha.decrypt(nonce, ciphertext_and_tag, aad)
            except InvalidTag:
                raise ValueError("Gagal membuka kunci ChaCha20-Poly1305: Passphrase salah atau berkas telah dimanipulasi!")

            with open(output_filepath, 'wb') as f_out:
                f_out.write(plaintext_bytes)

            return {
                "status": "UNLOCKED",
                "algorithm": "ChaCha20-Poly1305 AEAD",
                "restored_file": output_filepath,
                "metadata": meta
            }

        # 2. Format Legacy V1 (Raw ChaCha20 unauthenticated fallback)
        elif magic == LEGACY_MAGIC_V1:
            nonce = f_in.read(16)
            ciphertext = f_in.read()
            key = hashlib.sha256(passphrase.encode('utf-8')).digest()
            cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
            decryptor = cipher.decryptor()
            plaintext_bytes = decryptor.update(ciphertext)

            with open(output_filepath, 'wb') as f_out:
                f_out.write(plaintext_bytes)

            return {
                "status": "UNLOCKED_LEGACY",
                "algorithm": "ChaCha20 Legacy (Unauthenticated)",
                "restored_file": output_filepath
            }

        else:
            raise ValueError("Berkas bukan merupakan arsip terenkripsi Darkroom Vault yang valid!")
