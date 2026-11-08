"""
=============================================================================
DARKROOM 2.0 - AUTOMATED TEST SUITE: SESSION & SECURITY FOUNDATION
=============================================================================
Pengujian terotomatisasi untuk State Machine, Session Token, Route Protection,
dan Dead Man's Switch (Emergency Revocation).
=============================================================================
"""

import os
import sys
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import app as app_module
from app import app
from backend.core.session import session_manager, SessionState
from backend.hardware.dongle import set_virtual_dongle, verify_dongle

client = TestClient(app)


class TestSessionFoundation(unittest.TestCase):
    def setUp(self):
        session_manager.reset_to_workspace()
        set_virtual_dongle(False)
        self.biometric_patcher = patch.object(
            app_module, "verify_biometric_image", return_value=(True, 1.0)
        )
        self.biometric_patcher.start()

    def tearDown(self):
        self.biometric_patcher.stop()
        session_manager.reset_to_workspace()
        set_virtual_dongle(False)

    def test_initial_state_is_photography_workspace(self):
        """1. Status awal sistem harus selalu PHOTOGRAPHY_WORKSPACE."""
        res = client.get("/api/session/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["state"], "PHOTOGRAPHY_WORKSPACE")
        self.assertFalse(data["is_authorized"])

    def test_public_photography_endpoints_accessible_without_token(self):
        """2. Endpoint ruang fotografi harus dapat diakses tanpa token apa pun."""
        res = client.get("/api/catalog/photos")
        self.assertEqual(res.status_code, 200)
        self.assertIn("photos", res.json())

        res_dongle = client.get("/api/dongle/status")
        self.assertEqual(res_dongle.status_code, 200)

    def test_private_endpoints_rejected_without_session_token(self):
        """3. Endpoint privat harus menolak request tanpa token dengan HTTP 401."""
        res = client.post("/api/stego/embed-super-text", data={
            "filename": "JAKA0561.JPG",
            "plaintext": "Test secret",
            "vigenere_key": "TEST",
            "aes_key": "TestPass123!"
        })
        self.assertEqual(res.status_code, 401)
        self.assertIn("Akses ditolak", res.json()["detail"])

        res_vault = client.post("/api/vault/lock-photo", data={
            "filename": "JAKA0561.JPG",
            "passphrase": "pass"
        })
        self.assertEqual(res_vault.status_code, 401)

    def test_unlock_session_fails_when_dongle_missing(self):
        """4. Membuka sesi privat harus gagal jika dongle fisik/virtual tidak ada."""
        set_virtual_dongle(False)
        res = client.post("/api/session/unlock", json={
            "password": "admin",
            "is_match": True,
            "image_base64": "test-image"
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("dongle tidak terpasang", res.json()["detail"].lower())

    def test_unlock_session_succeeds_with_dongle_and_password(self):
        """5. Membuka sesi sukses saat dongle terpasang dan kata sandi valid."""
        set_virtual_dongle(True) # Pasang dongle
        res = client.post("/api/session/unlock", json={
            "password": "admin",
            "is_match": True,
            "image_base64": "test-image"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("token", data)
        self.assertEqual(len(data["token"]), 64)
        self.assertEqual(data["state"], "AUTHORIZED_PRIVATE")

        # Status session sekarang harus authorized
        token = data["token"]
        status_res = client.get("/api/session/status", headers={"X-Session-Token": token})
        self.assertEqual(status_res.status_code, 200)
        self.assertTrue(status_res.json()["is_authorized"])

    def test_dead_mans_switch_revokes_session_when_dongle_removed(self):
        """6. DEAD MAN'S SWITCH: Saat dongle dicabut, sesi privat seketika dibatalkan."""
        set_virtual_dongle(True)
        login_res = client.post("/api/session/unlock", json={
            "password": "admin",
            "is_match": True,
            "image_base64": "test-image"
        })
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Verifikasi sesi aktif
        res_pre = client.get("/api/session/status", headers=headers)
        self.assertTrue(res_pre.json()["is_authorized"])

        # PENCABUTAN DONGLE SECARA TIBA-TIBA
        set_virtual_dongle(False)

        # Request endpoint privat harus DITOLAK seketika (HTTP 401 atau 403)
        res_action = client.post("/api/stego/embed-super-text", data={
            "filename": "JAKA0561.JPG",
            "plaintext": "Secret",
            "vigenere_key": "K",
            "aes_key": "Pass"
        }, headers=headers)
        self.assertIn(res_action.status_code, (401, 403))

        # Token sesi di memori harus sudah invalid
        status_post = client.get("/api/session/status", headers=headers)
        self.assertFalse(status_post.json()["is_authorized"])

    def test_manual_panic_lock(self):
        """7. Panic Switch manual seketika memusnahkan sesi."""
        set_virtual_dongle(True)
        login_res = client.post("/api/session/unlock", json={
            "password": "admin",
            "is_match": True,
            "image_base64": "test-image"
        })
        token = login_res.json()["token"]

        res_lock = client.post("/api/session/lock")
        self.assertEqual(res_lock.status_code, 200)
        self.assertEqual(res_lock.json()["state"], "PHOTOGRAPHY_WORKSPACE")

        # Token lama tidak lagi berlaku
        status_res = client.get("/api/session/status", headers={"X-Session-Token": token})
        self.assertFalse(status_res.json()["is_authorized"])


if __name__ == "__main__":
    unittest.main()
