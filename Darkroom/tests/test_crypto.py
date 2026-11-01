"""
=============================================================================
DARKROOM 2.0 - AUTOMATED TEST SUITE: CRYPTOGRAPHIC CORRECTION
=============================================================================
Pengujian terotomatisasi untuk AES-256-GCM, ChaCha20-Poly1305 AEAD,
Super-Enkripsi, HKDF Key Derivation, dan Tamper Rejection.
=============================================================================
"""

import os
import sys
import unittest
import base64

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.crypto.kdf import derive_key_hkdf
from backend.crypto.aes_cipher import aes_encrypt, aes_decrypt
from backend.crypto.vigenere import vigenere_encrypt, vigenere_decrypt
from backend.crypto.super_encrypt import super_encrypt, super_decrypt
from backend.crypto.file_cipher import encrypt_file, decrypt_file


class TestCryptoCorrection(unittest.TestCase):

    def test_hkdf_domain_separation(self):
        """1. Passphrase yang sama harus menghasilkan kunci berbeda untuk tiap domain."""
        passphrase = "RahasiaBersama2026!"
        salt = b"1234567890abcdef"

        key_text = derive_key_hkdf(passphrase, salt, info=b"darkroom-text-gcm-v2")
        key_file = derive_key_hkdf(passphrase, salt, info=b"darkroom-file-chacha20poly1305-v2")
        key_db = derive_key_hkdf(passphrase, salt, info=b"darkroom-db-fle-v2")

        self.assertEqual(len(key_text), 32)
        self.assertEqual(len(key_file), 32)
        self.assertEqual(len(key_db), 32)
        self.assertNotEqual(key_text, key_file)
        self.assertNotEqual(key_text, key_db)
        self.assertNotEqual(key_file, key_db)

    def test_aes_gcm_roundtrip(self):
        """2. Enkripsi dan dekripsi AES-256-GCM harus mengembalikan plaintext persis."""
        pesan = "Memo Intelijen: Lokasi pertemuan rahasia di Koordinat -6.2088, 106.8456. Pukul 23:00."
        kunci = "KunciGCMSuperKuat2026!"

        ct = aes_encrypt(pesan, kunci)
        pt = aes_decrypt(ct, kunci)
        self.assertEqual(pesan, pt)

    def test_aes_gcm_wrong_key_rejected(self):
        """3. Dekripsi AES-GCM dengan kunci salah harus ditolak (ValueError)."""
        pesan = "Data Sensitif."
        ct = aes_encrypt(pesan, "KunciBenar123")
        with self.assertRaises(ValueError):
            aes_decrypt(ct, "KunciSalah456")

    def test_aes_gcm_tampered_ciphertext_rejected(self):
        """4. Manipulasi 1 bit pada ciphertext AES-GCM harus ditolak seketika oleh tag."""
        pesan = "Transfer aset rahasia senilai 1.000.000 USD."
        kunci = "KunciGCMIntegritas!"
        ct_b64 = aes_encrypt(pesan, kunci)

        # Modifikasi 1 byte di dalam payload ciphertext
        ct_raw = bytearray(base64.b64decode(ct_b64))
        ct_raw[-1] ^= 0x01 # Flip bit terakhir
        tampered_b64 = base64.b64encode(ct_raw).decode('utf-8')

        with self.assertRaises(ValueError):
            aes_decrypt(tampered_b64, kunci)

    def test_super_encryption_roundtrip(self):
        """5. Super Enkripsi (Vigenère + AES-GCM) harus bekerja 100% bolak-balik."""
        pesan = "Laporan Khusus Jurnalis Lapangan: Target bergerak ke pelabuhan."
        k_vig = "JURNALIS"
        k_aes = "PassphraseModernGCM2026!"

        res_enc = super_encrypt(pesan, k_vig, k_aes)
        ct = res_enc["final_ciphertext"]
        self.assertIn("intermediate_vigenere", res_enc)

        res_dec = super_decrypt(ct, k_vig, k_aes)
        self.assertEqual(pesan, res_dec["final_plaintext"])

    def test_chacha20_poly1305_file_roundtrip(self):
        """6. Enkripsi berkas ChaCha20-Poly1305 harus menghasilkan biner identik byte-for-byte."""
        test_dir = os.path.join(PROJECT_ROOT, "storage", "test_scratch")
        os.makedirs(test_dir, exist_ok=True)
        orig_file = os.path.join(test_dir, "evidence_test.raw")
        enc_file = os.path.join(test_dir, "evidence_test.raw.enc")
        restored_file = os.path.join(test_dir, "evidence_test_restored.raw")

        # Buat dummy data berkas biner
        dummy_data = os.urandom(128 * 1024) # 128 KB data biner acak
        with open(orig_file, "wb") as f:
            f.write(dummy_data)

        passphrase = "KunciBrankasFotoRaw2026!"
        res_enc = encrypt_file(orig_file, enc_file, passphrase)
        self.assertEqual(res_enc["status"], "LOCKED")
        self.assertEqual(res_enc["algorithm"], "ChaCha20-Poly1305 AEAD")

        res_dec = decrypt_file(enc_file, restored_file, passphrase)
        self.assertEqual(res_dec["status"], "UNLOCKED")

        with open(restored_file, "rb") as f:
            recovered_data = f.read()

        self.assertEqual(dummy_data, recovered_data)

        # Cleanup test files
        for p in [orig_file, enc_file, restored_file]:
            if os.path.exists(p):
                os.remove(p)

    def test_chacha20_poly1305_tampered_file_rejected(self):
        """7. Manipulasi 1 byte pada file ChaCha20-Poly1305 harus ditolak oleh tag autentikasi."""
        test_dir = os.path.join(PROJECT_ROOT, "storage", "test_scratch")
        os.makedirs(test_dir, exist_ok=True)
        orig_file = os.path.join(test_dir, "tamper_test.raw")
        enc_file = os.path.join(test_dir, "tamper_test.raw.enc")
        restored_file = os.path.join(test_dir, "tamper_test_restored.raw")

        with open(orig_file, "wb") as f:
            f.write(b"Data Sensitif Tidak Boleh Diubah Sedikitpun!")

        passphrase = "KunciAntiManipulasi2026!"
        encrypt_file(orig_file, enc_file, passphrase)

        # Modifikasi 1 byte di dalam file terenkripsi
        with open(enc_file, "rb") as f:
            enc_data = bytearray(f.read())
        enc_data[-1] ^= 0x55 # Flip byte
        with open(enc_file, "wb") as f:
            f.write(enc_data)

        # Harus gagal dengan ValueError
        with self.assertRaises(ValueError):
            decrypt_file(enc_file, restored_file, passphrase)

        # Cleanup
        for p in [orig_file, enc_file, restored_file]:
            if os.path.exists(p):
                os.remove(p)


if __name__ == "__main__":
    unittest.main()
