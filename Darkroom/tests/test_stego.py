"""
=============================================================================
DARKROOM 2.0 - AUTOMATED TEST SUITE: STEGANOGRAPHY REFACTORING
=============================================================================
Pengujian terotomatisasi untuk LSB Framing V2, Round-Trip Exact Recovery
(TEXT, FILE, IMAGE), Bounds Checking, dan Non-Stego Detection.
=============================================================================
"""

import os
import sys
import unittest
from PIL import Image

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.stego.lsb import (
    calculate_image_capacity,
    embed_super_crypto_text,
    embed_binary_file_payload,
    embed_secret_image_in_decoy,
    extract_and_reveal
)


class TestStegoRefactoring(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(PROJECT_ROOT, "storage", "test_scratch_stego")
        os.makedirs(self.test_dir, exist_ok=True)

        # Buat dummy cover image RGB (800x600 = 480.000 pixel = ~180 KB net capacity)
        self.cover_path = os.path.join(self.test_dir, "test_cover.png")
        img = Image.new("RGB", (800, 600), color=(120, 180, 240))
        img.save(self.cover_path, format="PNG")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            for f in os.listdir(self.test_dir):
                try:
                    os.remove(os.path.join(self.test_dir, f))
                except Exception:
                    pass
            try:
                os.rmdir(self.test_dir)
            except Exception:
                pass

    def test_capacity_calculation(self):
        """1. Penghitungan kapasitas LSB harus sesuai dengan resolusi dan jumlah kanal RGB."""
        cap = calculate_image_capacity(self.cover_path)
        self.assertEqual(cap["width"], 800)
        self.assertEqual(cap["height"], 600)
        self.assertEqual(cap["total_pixels"], 480000)
        expected_bytes = (480000 * 3) // 8
        self.assertEqual(cap["gross_capacity_bytes"], expected_bytes)
        self.assertGreater(cap["net_capacity_bytes"], 0)

    def test_text_payload_roundtrip(self):
        """2. Text Stego: Plaintext -> Super Encrypt -> Embed LSB -> Extract -> Decrypt."""
        out_stego = os.path.join(self.test_dir, "stego_text_out.png")
        pesan_asli = "Laporan Khusus Liputan Intelijen: Pertemuan diplomatik rahasia di Hotel Mulia."
        k_vig = "JURNALIS"
        k_aes = "PassphraseGCMSuperAman2026!"

        res_embed = embed_super_crypto_text(self.cover_path, pesan_asli, k_vig, k_aes, out_stego)
        self.assertEqual(res_embed["status"], "SUCCESS")
        self.assertTrue(os.path.exists(out_stego))

        # Ekstraksi dan dekripsi
        res_reveal = extract_and_reveal(out_stego, vigenere_key=k_vig, aes_key=k_aes)
        self.assertTrue(res_reveal["has_payload"])
        self.assertEqual(res_reveal["type"], "TEXT")
        self.assertTrue(res_reveal["is_decrypted"])
        self.assertEqual(res_reveal["plaintext"], pesan_asli)

    def test_file_payload_exact_binary_roundtrip(self):
        """3. File Stego: Berkas biner sembarang harus dipulihkan persis byte-for-byte."""
        orig_file = os.path.join(self.test_dir, "document_evidence.pdf")
        binary_content = b"%PDF-1.4 Mock Binary PDF Content with Nonce and Chars \x00\x01\x02\xff" * 50
        with open(orig_file, "wb") as f:
            f.write(binary_content)

        out_stego = os.path.join(self.test_dir, "stego_file_out.png")
        passphrase = "FileVaultPassphrase2026!"

        embed_binary_file_payload(self.cover_path, orig_file, passphrase, out_stego)

        # Ekstraksi dan verifikasi integritas biner
        res_reveal = extract_and_reveal(out_stego, passphrase=passphrase, export_dir=self.test_dir)
        self.assertTrue(res_reveal["has_payload"])
        self.assertEqual(res_reveal["type"], "FILE")
        self.assertTrue(res_reveal["is_decrypted"])
        self.assertEqual(res_reveal["original_filename"], "document_evidence.pdf")

        recovered_file = res_reveal["saved_file"]
        with open(recovered_file, "rb") as f:
            recovered_bytes = f.read()

        self.assertEqual(binary_content, recovered_bytes)

    def test_image_decoy_exact_roundtrip(self):
        """4. Image Stego: Foto rahasia di dalam foto decoy harus terpulihkan byte-for-byte tanpa kompresi lossy."""
        secret_img_path = os.path.join(self.test_dir, "secret_snap.png")
        secret_img = Image.new("RGB", (100, 100), color=(255, 0, 128))
        secret_img.save(secret_img_path, format="PNG")

        with open(secret_img_path, "rb") as f:
            secret_orig_bytes = f.read()

        out_stego = os.path.join(self.test_dir, "stego_image_decoy.png")
        passphrase = "SecretImagePassphrase2026!"

        embed_secret_image_in_decoy(self.cover_path, secret_img_path, out_stego, passphrase=passphrase)

        res_reveal = extract_and_reveal(out_stego, passphrase=passphrase, export_dir=self.test_dir)
        self.assertTrue(res_reveal["has_payload"])
        self.assertEqual(res_reveal["type"], "IMAGE")
        self.assertTrue(res_reveal["is_decrypted"])

        with open(res_reveal["saved_file"], "rb") as f:
            recovered_img_bytes = f.read()

        self.assertEqual(secret_orig_bytes, recovered_img_bytes)

    def test_capacity_exceeded_rejected_without_lossy_compression(self):
        """5. Jika payload melebihi kapasitas cover, sistem wajib melempar ValueError (Zero Silent Compression)."""
        # Buat cover kecil (50x50 = 2500 pixel = ~937 byte)
        tiny_cover = os.path.join(self.test_dir, "tiny_cover.png")
        Image.new("RGB", (50, 50)).save(tiny_cover)

        large_file = os.path.join(self.test_dir, "large_file.bin")
        with open(large_file, "wb") as f:
            f.write(os.urandom(50000)) # 50 KB (jauh di atas kapasitas 937 byte)

        out_stego = os.path.join(self.test_dir, "should_fail.png")
        with self.assertRaises(ValueError):
            embed_binary_file_payload(tiny_cover, large_file, "pass", out_stego)

    def test_non_stego_image_returns_no_payload(self):
        """6. Citra normal tanpa stego Darkroom harus dengan cepat dilaporkan has_payload: False."""
        clean_img = os.path.join(self.test_dir, "clean_unmodified.png")
        Image.new("RGB", (400, 400), color=(50, 60, 70)).save(clean_img)

        res = extract_and_reveal(clean_img)
        self.assertFalse(res["has_payload"])
        self.assertIn("Tidak dikenali", res["message"])


if __name__ == "__main__":
    unittest.main()
