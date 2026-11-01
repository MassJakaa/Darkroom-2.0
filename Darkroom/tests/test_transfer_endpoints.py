"""
=============================================================================
DARKROOM 2.0 - AUTOMATED TEST SUITE: TRANSFER & DEVELOP ENDPOINTS
=============================================================================
Pengujian terintegrasi untuk endpoint Transfer (Capacity, Outgoing Text/File/Image,
Incoming Extract) dan endpoint Develop Export.
=============================================================================
"""

import os
import sys
import unittest
import io
from PIL import Image
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app, CATALOG_DIR, EXPORTS_DIR
from backend.core.session import session_manager
from backend.hardware.dongle import set_virtual_dongle

client = TestClient(app)


class TestTransferAndDevelopEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        set_virtual_dongle(True)
        login_res = client.post("/api/session/unlock", json={"password": "admin"})
        cls.token = login_res.json()["token"]
        cls.auth_headers = {"Authorization": f"Bearer {cls.token}"}

        # Pastikan ada foto cover uji di katalog (RGB PNG)
        cls.test_cover_name = "test_transfer_cover.png"
        cls.test_cover_path = os.path.join(CATALOG_DIR, cls.test_cover_name)
        img = Image.new("RGB", (600, 400), color=(100, 150, 200))
        img.save(cls.test_cover_path, format="PNG")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_cover_path):
            os.remove(cls.test_cover_path)
        set_virtual_dongle(False)
        session_manager.reset_to_workspace()

    def test_transfer_capacity_endpoint(self):
        """1. GET /api/transfer/capacity/{filename} mengembalikan data kapasitas cover."""
        res = client.get(f"/api/transfer/capacity/{self.test_cover_name}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["capacity"]["width"], 600)
        self.assertEqual(data["capacity"]["height"], 400)
        self.assertGreater(data["capacity"]["net_capacity_bytes"], 0)

    def test_transfer_outgoing_text_and_incoming_extract(self):
        """2. Outgoing Text -> Incoming Extract round-trip via HTTP endpoints."""
        plaintext = "Informasi Rahasia Intelijen: Target A terkonfirmasi di Terminal 3."
        vig_key = "KODE"
        aes_key = "KunciAESGCMTransfer2026!"

        res_out = client.post("/api/transfer/outgoing/text", data={
            "cover_filename": self.test_cover_name,
            "plaintext": plaintext,
            "vigenere_key": vig_key,
            "aes_key": aes_key
        }, headers=self.auth_headers)

        self.assertEqual(res_out.status_code, 200)
        out_data = res_out.json()
        self.assertTrue(out_data["success"])
        stego_filename = out_data["output_filename"]

        # Unduh stego file untuk di-upload kembali ke incoming extract
        stego_path = os.path.join(EXPORTS_DIR, stego_filename)
        self.assertTrue(os.path.exists(stego_path))

        with open(stego_path, "rb") as f:
            file_bytes = f.read()

        res_in = client.post("/api/transfer/incoming/extract", files={
            "stego_file": (stego_filename, file_bytes, "image/png")
        }, data={
            "vigenere_key": vig_key,
            "aes_key": aes_key
        }, headers=self.auth_headers)

        self.assertEqual(res_in.status_code, 200)
        in_data = res_in.json()
        self.assertTrue(in_data["has_payload"])
        self.assertEqual(in_data["type"], "TEXT")
        self.assertTrue(in_data["is_decrypted"])
        self.assertEqual(in_data["plaintext"], plaintext)

    def test_transfer_outgoing_file_and_incoming_extract(self):
        """3. Outgoing File -> Incoming Extract round-trip via HTTP endpoints."""
        doc_content = b"Binary Confidential Report 2026. Document Signature \xde\xad\xbe\xef" * 10
        passphrase = "FileTransferKey2026!"

        res_out = client.post("/api/transfer/outgoing/file", files={
            "payload_file": ("secret_report.pdf", doc_content, "application/pdf")
        }, data={
            "cover_filename": self.test_cover_name,
            "passphrase": passphrase
        }, headers=self.auth_headers)

        self.assertEqual(res_out.status_code, 200)
        out_data = res_out.json()
        self.assertTrue(out_data["success"])
        stego_filename = out_data["output_filename"]

        stego_path = os.path.join(EXPORTS_DIR, stego_filename)
        with open(stego_path, "rb") as f:
            file_bytes = f.read()

        res_in = client.post("/api/transfer/incoming/extract", files={
            "stego_file": (stego_filename, file_bytes, "image/png")
        }, data={
            "passphrase": passphrase
        }, headers=self.auth_headers)

        self.assertEqual(res_in.status_code, 200)
        in_data = res_in.json()
        self.assertTrue(in_data["has_payload"])
        self.assertEqual(in_data["type"], "FILE")
        self.assertTrue(in_data["is_decrypted"])

        # Verifikasi konten biner yang dipulihkan
        recovered_path = os.path.join(EXPORTS_DIR, in_data["filename"])
        with open(recovered_path, "rb") as f:
            recovered_bytes = f.read()
        self.assertEqual(doc_content, recovered_bytes)

    def test_develop_export_endpoint(self):
        """4. POST /api/develop/export mengekspor foto dengan format dan resolusi yang diminta."""
        res = client.post("/api/develop/export", json={
            "filename": self.test_cover_name,
            "export_format": "JPEG",
            "quality": 85,
            "scale_percent": 50
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["dimensions"], "300x200") # 50% scale dari 600x400
        out_p = os.path.join(EXPORTS_DIR, data["filename"])
        self.assertTrue(os.path.exists(out_p))

    def test_transfer_extract_by_catalog_filename(self):
        """5. Ekstraksi langsung menggunakan nama berkas katalog stego hasil ekspor (tanpa upload berkas fisik)."""
        secret_msg = "Pesan Rahasia Terbaca Langsung dari Katalog"
        res_out = client.post("/api/transfer/outgoing/text", data={
            "cover_filename": self.test_cover_name,
            "plaintext": secret_msg,
            "vigenere_key": "KUNCI",
            "aes_key": "SandiAES123!"
        }, headers=self.auth_headers)

        self.assertEqual(res_out.status_code, 200)
        stego_name = res_out.json()["output_filename"]
        self.assertTrue(stego_name.startswith("MODIFIED_STEGO_"))
        self.assertTrue(os.path.exists(os.path.join(CATALOG_DIR, stego_name)))

        # Panggil incoming extract hanya dengan parameter filename (dari katalog)
        res_in = client.post("/api/transfer/incoming/extract", data={
            "filename": stego_name,
            "vigenere_key": "KUNCI",
            "aes_key": "SandiAES123!"
        }, headers=self.auth_headers)

        self.assertEqual(res_in.status_code, 200)
        in_data = res_in.json()
        self.assertTrue(in_data["has_payload"])
        self.assertEqual(in_data["plaintext"], secret_msg)


if __name__ == "__main__":
    unittest.main()
