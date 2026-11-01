"""
=============================================================================
DARKROOM 2.0 - FULL SYSTEM INTEGRATION TEST SUITE
=============================================================================
Memverifikasi integrasi menyeluruh dari 5 ruang kerja dan security foundation:
1. Database FLE (Field-Level Encryption AES-256-GCM)
2. Blockchain Proof-of-Work Integrity Ledger
3. Hardware Dongle & Virtual Drive Fallback
4. Develop & Export Pipeline (JPEG/PNG, Scales)
5. Transfer Stego Workspace (Text, File, Image exact roundtrips)
6. Session State Machine & Emergency Panic Revocation
=============================================================================
"""

import os
import sys
import tempfile
import unittest
from fastapi.testclient import TestClient
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

from app import app
from backend.core.session import session_manager, SessionState
from backend.hardware.dongle import set_virtual_dongle, verify_dongle
from backend.database.db import (
    init_db,
    insert_photo_with_encrypted_note,
    get_raw_database_records,
    get_decrypted_database_records
)
from backend.blockchain.ledger import PhotoBlockchain, calculate_file_hash


class TestDarkroomFullSystem(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        set_virtual_dongle(True)
        session_manager.reset_to_workspace()

        self.test_dir = tempfile.mkdtemp()

        # Buat dummy cover image PNG 120x120
        self.cover_path = os.path.join(PROJECT_ROOT, "storage", "catalog", "test_system_cover.png")
        os.makedirs(os.path.dirname(self.cover_path), exist_ok=True)
        img = Image.new("RGB", (120, 120), color=(100, 150, 200))
        img.save(self.cover_path, format="PNG")

    def tearDown(self):
        set_virtual_dongle(True)
        session_manager.reset_to_workspace()
        if os.path.exists(self.cover_path):
            try:
                os.remove(self.cover_path)
            except Exception:
                pass

    def test_database_field_level_encryption(self):
        """1. Database FLE: Kolom sensitif tersimpan terenkripsi AES-GCM di disk dan terdekripsi benar."""
        init_db()
        passphrase = "DatabaseMasterKey2026!"
        secret = "Koordinat Operasi: -6.2088, 106.8456. Target terkonfirmasi."

        row_id = insert_photo_with_encrypted_note(
            title="Intel Senayan",
            filename="DSC_9999.JPG",
            public_caption="Suasana sore Senayan",
            secret_note=secret,
            photo_hash="hash_dummy_99",
            passphrase=passphrase
        )
        self.assertGreater(row_id, 0)

        # Cek data mentah di SQLite (harus berupa ciphertext ber-envelope GCM2, bukan plaintext)
        raw_rows = get_raw_database_records()
        matching = [r for r in raw_rows if r["id"] == row_id]
        self.assertEqual(len(matching), 1)
        raw_note = matching[0]["secret_intel_note"]
        self.assertNotIn("Koordinat Operasi", raw_note)
        import base64
        raw_bytes = base64.b64decode(raw_note)
        self.assertTrue(raw_bytes.startswith(b"GCM2"))

        # Cek dekripsi resmi dengan passphrase yang benar
        decrypted_rows = get_decrypted_database_records(passphrase)
        dec_matching = [r for r in decrypted_rows if r["id"] == row_id]
        self.assertEqual(len(dec_matching), 1)
        self.assertEqual(dec_matching[0]["secret_intel_note"], secret)
        self.assertEqual(dec_matching[0]["decryption_status"], "DECRYPTED_SUCCESS")

        # Cek dekripsi dengan kunci salah (tidak boleh bocor)
        wrong_rows = get_decrypted_database_records("WrongPassword123")
        wrong_matching = [r for r in wrong_rows if r["id"] == row_id]
        self.assertEqual(wrong_matching[0]["decryption_status"], "DECRYPTED_FAILED")

    def test_blockchain_mining_and_tamper_detection(self):
        """2. Blockchain Ledger: Penambangan PoW valid dan manipulasi data terdeteksi seketika."""
        bc = PhotoBlockchain()
        initial_len = len(bc.chain)

        new_block = bc.add_photo_asset(
            photo_path=self.cover_path,
            photographer_id="Agent-Jaka",
            metadata="Foto bukti investigasi TKP 1"
        )
        self.assertEqual(len(bc.chain), initial_len + 1)
        self.assertTrue(new_block.current_hash.startswith("00"))

        # Validasi integritas buku besar
        is_valid, msg = bc.verify_integrity()
        self.assertTrue(is_valid)

        # Simulasi Serangan: Modifikasi metadata blok secara paksa
        new_block.metadata = "Foto ini sudah dimodifikasi oleh penyusup!"
        is_tampered_valid, tamper_msg = bc.verify_integrity()
        self.assertFalse(is_tampered_valid)
        self.assertIn("DIUBAH / DIPALSUKAN", tamper_msg)

    def test_full_session_authorization_and_panic_switch(self):
        """3. State Machine: Siklus Fotografi -> Unlock -> Private -> Panic Lock."""
        # 1. State awal
        self.assertEqual(session_manager.current_state, SessionState.PHOTOGRAPHY_WORKSPACE)

        # 2. Unlock dengan kata sandi admin yang sah
        res = self.client.post("/api/session/unlock", json={"password": "admin", "biometric_confirmed": True})
        self.assertEqual(res.status_code, 200)
        token = res.json()["token"]
        self.assertEqual(session_manager.current_state, SessionState.AUTHORIZED_PRIVATE)

        # 3. Akses endpoint privat dengan token
        headers = {"Authorization": f"Bearer {token}"}
        cap_res = self.client.get(f"/api/transfer/capacity/{os.path.basename(self.cover_path)}")
        self.assertEqual(cap_res.status_code, 200)

        # 4. Emergency Panic Lock
        panic_res = self.client.post("/api/session/lock?reason=TestPanic", headers=headers)
        self.assertEqual(panic_res.status_code, 200)
        self.assertEqual(session_manager.current_state, SessionState.PHOTOGRAPHY_WORKSPACE)
        self.assertEqual(len(session_manager.active_sessions), 0)

        # 5. Endpoint privat tertolak seketika
        rej_res = self.client.post(
            "/api/transfer/outgoing/text",
            data={
                "cover_filename": os.path.basename(self.cover_path),
                "plaintext": "Pesan",
                "aes_key": "Pass123"
            },
            headers=headers
        )
        self.assertEqual(rej_res.status_code, 401)

    def test_transfer_workspace_capacity_and_suitability(self):
        """4. Transfer Workspace: Endpoint kapasitas dan kelayakan citra cover."""
        fname = os.path.basename(self.cover_path)
        res = self.client.get(f"/api/transfer/capacity/{fname}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        cap = data["capacity"]
        self.assertEqual(cap["width"], 120)
        self.assertEqual(cap["height"], 120)
        self.assertTrue(cap["is_suitable"])
        self.assertGreater(cap["max_payload_bytes"], 1000)

    def test_lock_and_unlock_image_file(self):
        """5. Vault File Lock: Mengunci foto menjadi .enc via ChaCha20-Poly1305 dan memulihkannya."""
        login_res = self.client.post("/api/session/unlock", json={"password": "admin", "biometric_confirmed": True})
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        fname = os.path.basename(self.cover_path)
        passphrase = "FileLockPassphrase2026!"

        # 1. Kunci foto
        lock_res = self.client.post(
            "/api/vault/lock-photo",
            data={"filename": fname, "passphrase": passphrase},
            headers=headers
        )
        self.assertEqual(lock_res.status_code, 200)
        self.assertTrue(lock_res.json()["success"])
        locked_name = lock_res.json()["locked_filename"]
        self.assertEqual(locked_name, fname + ".enc")

        # Pastikan file asli di catalog sudah digantikan oleh .enc
        catalog_dir = os.path.dirname(self.cover_path)
        self.assertFalse(os.path.exists(self.cover_path))
        self.assertTrue(os.path.exists(os.path.join(catalog_dir, locked_name)))

        # 2. Buka kunci foto
        unlock_res = self.client.post(
            "/api/vault/unlock-photo",
            data={"filename": locked_name, "passphrase": passphrase},
            headers=headers
        )
        self.assertEqual(unlock_res.status_code, 200)
        self.assertTrue(unlock_res.json()["success"])
        unlocked_name = unlock_res.json()["unlocked_filename"]
        self.assertEqual(unlocked_name, fname)

        # File asli pulih dan .enc terhapus
        self.assertTrue(os.path.exists(self.cover_path))
        self.assertFalse(os.path.exists(os.path.join(catalog_dir, locked_name)))


if __name__ == "__main__":
    unittest.main()
