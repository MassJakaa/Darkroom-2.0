"""
=============================================================================
DARKROOM 2.0 - LIGHTROOM-INSPIRED COVERT STUDIO SERVER (FASTAPI)
=============================================================================
- Bilah Icon Kanan: Edit Sliders, Stego Teks (Super Crypto), Stego Decoy, File Lock
- Menu Samping Kiri: Studio Editor, Brankas Terkunci (.enc), Blockchain, Dekriptor
- Security Foundation: Otentikasi Berjenjang (Dongle SD + Password PBKDF2 + Biometrik AI SFace)
=============================================================================
"""

import os
import sys
import time
import base64
import shutil
import hashlib
import io
from typing import Any, Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

from backend.core.session import session_manager, require_private_session, extract_token_from_headers, SessionState
from backend.hardware.dongle import verify_dongle
from backend.hardware.biometric import load_models, get_face_feature_from_frame, compare_faces, FACE_DATA_PATH, is_agent_registered
from backend.crypto.auth import verify_login, get_current_user_info
from backend.crypto.file_cipher import encrypt_file, decrypt_file
from backend.stego.lsb import (
    calculate_image_capacity,
    embed_super_crypto_text,
    embed_binary_file_payload,
    embed_secret_image_in_decoy,
    extract_and_reveal
)
from backend.database.db import init_db, get_connection
from backend.blockchain.ledger import PhotoBlockchain

app = FastAPI(title="Darkroom 2.0 Studio")


def virtual_dongle_allowed() -> bool:
    """Allow the virtual dongle only when explicitly enabled for testing."""
    return os.getenv("DARKROOM_ALLOW_VIRTUAL_DONGLE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STORAGE_DIR = os.path.join(PROJECT_ROOT, "storage")
CATALOG_DIR = os.path.join(STORAGE_DIR, "catalog")
EXPORTS_DIR = os.path.join(STORAGE_DIR, "exports")
os.makedirs(CATALOG_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

init_db()
blockchain = PhotoBlockchain()


# =============================================================================
# 0. SESSION STATE MACHINE & SECURITY FOUNDATION (PHASE 2)
# =============================================================================
class SessionUnlockRequest(BaseModel):
    password: str
    is_match: bool = False
    image_base64: str = ""


# FIX: integrasi biometrik wajib
def verify_biometric_image(image_base64: str) -> tuple[bool, float]:
    """Verifikasi ulang citra wajah di backend; jangan mempercayai boolean klien saja."""
    if not is_agent_registered():
        raise HTTPException(status_code=403, detail="Belum ada wajah agen terdaftar; sesi privat ditolak.")
    if not image_base64:
        raise HTTPException(status_code=401, detail="Pemindaian wajah wajib sebelum membuka sesi privat.")

    try:
        import numpy as np
        import cv2

        img_bytes = base64.b64decode(image_base64.split(",", 1)[-1], validate=True)
        frame = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(status_code=400, detail="Format citra kamera tidak valid.")

        detector, recognizer = load_models()
        feature, _ = get_face_feature_from_frame(frame, detector, recognizer)
        if feature is None:
            return False, 0.0

        registered_feature = np.load(FACE_DATA_PATH)
        return compare_faces(feature, registered_feature)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Verifikasi biometrik gagal: {str(e)}")


@app.get("/api/session/status")
def get_session_status(token: str = Depends(extract_token_from_headers)):
    """
    Memeriksa status state machine terkini dan ketersediaan hardware dongle.
    """
    dongle_valid, msg, drive = verify_dongle()
    if not dongle_valid and session_manager.current_state == SessionState.AUTHORIZED_PRIVATE:
        # Emergency Panic: Dongle dicabut saat status private -> seketika cabut sesi!
        session_manager.revoke_all(reason="Dongle fisik dicabut terdeteksi saat polling status.")

    status_data = session_manager.get_status(token)
    return {
        **status_data,
        "dongle_valid": dongle_valid,
        "dongle_message": msg,
        "dongle_drive": drive
    }


@app.post("/api/session/unlock")
def unlock_session(req: SessionUnlockRequest):
    """
    Otentikasi backend-enforced untuk membuka sesi rahasia (AUTHORIZED_PRIVATE).
    Memeriksa dongle, password, flag hasil scan, dan kecocokan wajah di backend sebelum menerbitkan token.
    """
    dongle_valid, msg, drive = verify_dongle()
    if not dongle_valid:
        raise HTTPException(
            status_code=403,
            detail=f"Otorisasi gagal: Hardware dongle tidak terpasang ({msg})"
        )

    is_valid, auth_msg = verify_login(req.password)
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail=f"Autentikasi gagal: {auth_msg}"
        )

    # FIX: integrasi biometrik wajib
    if req.is_match is not True:
        raise HTTPException(status_code=401, detail="Verifikasi wajah wajib berhasil untuk membuka sesi privat.")
    face_matches, bio_score = verify_biometric_image(req.image_base64)
    if not face_matches:
        raise HTTPException(status_code=401, detail="Wajah tidak cocok; sesi privat ditolak.")

    user_info = get_current_user_info()
    username = user_info["username"] if user_info else "Agent"
    token = session_manager.authorize(username=username, drive=drive, bio_score=bio_score)

    return {
        "success": True,
        "token": token,
        "state": session_manager.current_state.value,
        "username": username,
        "message": "Sesi privat terotorisasi (AUTHORIZED_PRIVATE)."
    }


@app.post("/api/session/lock")
def lock_session():
    """
    Dead Man's Switch / Panic Switch:
    Segera memusnahkan sesi terotorisasi di memori dan mengembalikan ke PHOTOGRAPHY_WORKSPACE.
    """
    session_manager.revoke_all(reason="Kunci darurat manual dipicu")
    session_manager.reset_to_workspace()
    return {
        "success": True,
        "state": session_manager.current_state.value,
        "message": "Sesi rahasia dimusnahkan. Kembali ke mode Photography Workspace."
    }


# =============================================================================
# 1. HARDWARE DONGLE & AUTH
# =============================================================================
@app.get("/api/dongle/status")
def get_dongle_status():
    is_valid, msg, drive = verify_dongle()
    return {"is_valid": is_valid, "drive": drive, "message": msg}


@app.post("/api/dongle/virtual")
def toggle_virtual_dongle(active: bool = True):
    if not virtual_dongle_allowed():
        raise HTTPException(
            status_code=403,
            detail="Virtual dongle hanya tersedia dalam mode development/testing.",
        )
    from backend.hardware.dongle import set_virtual_dongle, verify_dongle
    set_virtual_dongle(active)
    is_valid, msg, drive = verify_dongle()
    return {"virtual_dongle": active, "is_valid": is_valid, "message": msg, "drive": drive}


@app.post("/api/dongle/make-key")
def create_key_file(drive_letter: str = Form(...)):
    from backend.hardware.dongle import create_dongle_key
    success, msg = create_dongle_key(drive_letter)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


class BiometricRequest(BaseModel):
    image_base64: str


@app.get("/api/auth/biometric/status")
def get_biometric_status():
    return {
        "is_registered": is_agent_registered(),
        "face_data_path": FACE_DATA_PATH if is_agent_registered() else None
    }


@app.post("/api/auth/biometric/register")
def register_face(req: BiometricRequest):
    try:
        img_bytes = base64.b64decode(req.image_base64.split(",")[-1])
        import numpy as np
        import cv2
        from backend.hardware.biometric import register_agent_face
        frame = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(status_code=400, detail="Format citra kamera tidak valid!")
        detector, recognizer = load_models()
        feature, box = get_face_feature_from_frame(frame, detector, recognizer)
        if feature is None:
            raise HTTPException(status_code=400, detail="Wajah tidak terdeteksi! Posisikan wajah di depan webcam dengan pencahayaan cukup.")
        register_agent_face(feature)
        return {"success": True, "message": "Wajah agen resmi berhasil didaftarkan!"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal mendaftarkan wajah: {str(e)}")


@app.post("/api/auth/biometric/verify")
@app.post("/api/auth/biometric")
def verify_face(req: BiometricRequest):
    try:
        # FIX: integrasi biometrik wajib
        is_match, score = verify_biometric_image(req.image_base64)
        return {
            "is_match": is_match,
            "score": round(score, 3),
            "threshold": 0.363,
            "is_registered": True,
            "message": f"Wajah Cocok ({round(score * 100, 1)}%)" if is_match else f"Wajah Ditolak (Kemiripan {round(score * 100, 1)}% < Ambang Batas 36.3%)"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Verifikasi biometrik gagal: {str(e)}")


@app.post("/api/auth/biometric/reset")
def reset_registered_face():
    if os.path.exists(FACE_DATA_PATH):
        try:
            os.remove(FACE_DATA_PATH)
        except Exception:
            pass
    return {"success": True, "message": "Data biometrik wajah berhasil direset."}


class LoginRequest(BaseModel):
    password: str
    is_match: Any
    image_base64: str

@app.post("/api/auth/login")
def login_password(req: LoginRequest):
    is_valid, msg = verify_login(req.password)
    if not is_valid:
        raise HTTPException(status_code=401, detail=msg)

    dongle_valid, dongle_msg, drive = verify_dongle()
    if not dongle_valid:
        raise HTTPException(status_code=403, detail=f"Otorisasi gagal: Hardware dongle tidak terpasang ({dongle_msg})")

    if not isinstance(req.image_base64, str) or not req.image_base64.strip():
        raise HTTPException(status_code=401, detail="Gambar biometrik wajib berasal dari kamera.")

    # FIX: integrasi biometrik wajib
    if req.is_match is not True:
        raise HTTPException(status_code=401, detail="Verifikasi wajah wajib berhasil untuk login.")
    face_matches, bio_score = verify_biometric_image(req.image_base64)
    if not face_matches:
        raise HTTPException(status_code=401, detail="Wajah tidak cocok; login ditolak.")

    user_info = get_current_user_info()
    username = user_info["username"] if user_info else "Agent"
    session_token = session_manager.authorize(username=username, drive=drive, bio_score=bio_score)

    return {
        "success": True,
        "message": msg,
        "username": username,
        "session_token": session_token,
        "state": session_manager.current_state.value
    }


# =============================================================================
# 2. KATALOG FOTO & FILMSTRIP
# =============================================================================
@app.get("/api/catalog/photos")
def list_catalog_photos():
    files = []
    for f in os.listdir(CATALOG_DIR):
        p = os.path.join(CATALOG_DIR, f)
        if os.path.isfile(p):
            is_enc = f.endswith(".enc")
            files.append({
                "filename": f,
                "is_locked": is_enc,
                "size_mb": round(os.path.getsize(p) / (1024 * 1024), 2),
                "url": f"/api/catalog/file/{f}" if not is_enc else ""
            })
    return {"photos": files}


@app.post("/api/catalog/import")
async def import_photos(files: list[UploadFile] = File(...)):
    saved = []
    for file in files:
        clean_name = os.path.basename(file.filename)
        target = os.path.join(CATALOG_DIR, clean_name)
        with open(target, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved.append(clean_name)
    return {"success": True, "imported": saved}


@app.post("/api/catalog/rename")
def rename_catalog_photo(old_filename: str = Form(...), new_filename: str = Form(...)):
    """Mengubah nama file di katalog (baik file biasa maupun file .enc)."""
    old_p = os.path.join(CATALOG_DIR, os.path.basename(old_filename))
    if not os.path.exists(old_p):
        raise HTTPException(status_code=404, detail="File lama tidak ditemukan!")

    old_base, old_ext = os.path.splitext(old_filename)
    new_clean = os.path.basename(new_filename).strip()
    
    if old_filename.endswith(".enc") and not new_clean.endswith(".enc"):
        new_clean += ".enc"
    elif not old_filename.endswith(".enc") and not os.path.splitext(new_clean)[1]:
        new_clean += old_ext

    new_p = os.path.join(CATALOG_DIR, new_clean)
    if os.path.exists(new_p) and new_p.lower() != old_p.lower():
        raise HTTPException(status_code=400, detail="Nama file baru sudah digunakan!")

    os.rename(old_p, new_p)
    return {"success": True, "old_filename": old_filename, "new_filename": new_clean}


@app.post("/api/catalog/delete")
def delete_catalog_photo(filename: str = Form(...)):
    """Menghapus foto dari katalog disk (termasuk file .enc jika ada)."""
    clean_name = os.path.basename(filename).strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Nama file tidak valid!")

    deleted = False
    # 1. Cek file langsung
    p = os.path.join(CATALOG_DIR, clean_name)
    if os.path.exists(p):
        os.remove(p)
        deleted = True

    # 2. Cek apakah ada versi .enc
    enc_p = p + ".enc"
    if os.path.exists(enc_p):
        os.remove(enc_p)
        deleted = True

    # 3. Jika file yang di-request berakhiran .enc, cek versi aslinya
    if clean_name.endswith(".enc"):
        base_p = os.path.join(CATALOG_DIR, clean_name[:-4])
        if os.path.exists(base_p):
            os.remove(base_p)
            deleted = True

    if not deleted:
        raise HTTPException(status_code=404, detail="File foto tidak ditemukan untuk dihapus!")

    return {"success": True, "deleted_filename": clean_name}


@app.get("/api/catalog/file/{filename}")
def serve_catalog_file(filename: str):
    clean_name = os.path.basename(filename)
    p = os.path.join(CATALOG_DIR, clean_name)
    if not os.path.exists(p):
        raise HTTPException(status_code=404, detail="File foto tidak ditemukan!")
    return FileResponse(p)


# =============================================================================
# 3. ICON 2: STEGANOGRAFI TEKS (SUPER ENKRIPSI + LSB + AUTO DB)
# =============================================================================
@app.post("/api/stego/embed-super-text")
def api_embed_super_text(
    filename: str = Form(...),
    plaintext: str = Form(...),
    vigenere_key: str = Form(...),
    aes_key: str = Form(...),
    session = Depends(require_private_session)
):
    cover_path = os.path.join(CATALOG_DIR, filename)
    if not os.path.exists(cover_path):
        raise HTTPException(status_code=404, detail="Foto cover tidak ditemukan!")
        
    out_filename = f"STEGO_TEXT_{os.path.splitext(filename)[0]}.png"
    out_path = os.path.join(EXPORTS_DIR, out_filename)
    
    try:
        res = embed_super_crypto_text(cover_path, plaintext, vigenere_key, aes_key, out_path)
        
        # Simpan ke Database SQLite otomatis
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO photo_catalog 
            (photo_title, filename, public_caption, secret_intel_note, photo_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"Stego Liputan {filename}",
            filename,
            "Foto Bersteganografi Teks Ter-Super Enkripsi",
            res["final_ciphertext"],
            "hash_placeholder",
            time.strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "output_filename": out_filename,
            "download_url": f"/api/exports/download/{out_filename}",
            "intermediate_vigenere": res["intermediate_vigenere"],
            "final_ciphertext": res["final_ciphertext"],
            "capacity_used": f"{res['capacity_used_percent']}%"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 4. ICON 3: STEGANOGRAFI GAMBAR / TIMPA FOTO DECOY (DUA ARAH)
# =============================================================================
@app.post("/api/stego/embed-decoy-image")
async def api_embed_decoy_image(
    canvas_filename: str = Form(...),
    uploaded_file: UploadFile = File(...),
    direction: str = Form("canvas_as_cover"),
    session = Depends(require_private_session)
):
    canvas_path = os.path.join(CATALOG_DIR, canvas_filename)
    if not os.path.exists(canvas_path):
        raise HTTPException(status_code=404, detail="Foto kanvas tidak ditemukan!")

    temp_uploaded = os.path.join(EXPORTS_DIR, f"temp_{uploaded_file.filename}")
    with open(temp_uploaded, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)

    if direction == "canvas_as_secret":
        cover_path = temp_uploaded
        secret_path = canvas_path
        out_filename = f"DECOY_{os.path.splitext(uploaded_file.filename)[0]}.png"
    else:
        cover_path = canvas_path
        secret_path = temp_uploaded
        out_filename = f"DECOY_{os.path.splitext(canvas_filename)[0]}.png"

    out_path = os.path.join(EXPORTS_DIR, out_filename)

    try:
        res = embed_secret_image_in_decoy(cover_path, secret_path, out_path)
        if os.path.exists(temp_uploaded):
            os.remove(temp_uploaded)
        return {
            "success": True,
            "output_filename": out_filename,
            "download_url": f"/api/exports/download/{out_filename}",
            "capacity_used": f"{res['capacity_used_percent']}%",
            "direction": direction
        }
    except Exception as e:
        if os.path.exists(temp_uploaded):
            os.remove(temp_uploaded)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 5. TRANSFER WORKSPACE: CAPACITY, OUTGOING & INCOMING PIPELINES
# =============================================================================
@app.get("/api/transfer/capacity/{filename}")
def get_cover_capacity(filename: str):
    """Menghitung kapasitas biner maksimal citra pembawa untuk transfer workspace."""
    clean_name = os.path.basename(filename)
    p = os.path.join(CATALOG_DIR, clean_name)
    if not os.path.exists(p):
        raise HTTPException(status_code=404, detail="Foto cover tidak ditemukan!")
    try:
        cap = calculate_image_capacity(p)
        return {"success": True, "filename": clean_name, "capacity": cap}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transfer/outgoing/text")
def api_transfer_outgoing_text(
    cover_filename: str = Form(...),
    plaintext: str = Form(...),
    vigenere_key: str = Form(""),
    aes_key: str = Form(...),
    session = Depends(require_private_session)
):
    """Outgoing Pipeline 1: Mengenkripsi teks dan menyisipkannya ke cover image."""
    cover_path = os.path.join(CATALOG_DIR, os.path.basename(cover_filename))
    if not os.path.exists(cover_path):
        raise HTTPException(status_code=404, detail="Foto cover tidak ditemukan!")

    out_name = f"MODIFIED_STEGO_{os.path.splitext(os.path.basename(cover_filename))[0]}.png"
    out_path = os.path.join(EXPORTS_DIR, out_name)

    try:
        res = embed_super_crypto_text(cover_path, plaintext, vigenere_key, aes_key, out_path)
        # Salin ke katalog agar foto yang sudah dimodifikasi langsung muncul di Library & Filmstrip
        shutil.copy2(out_path, os.path.join(CATALOG_DIR, out_name))
        return {
            "success": True,
            "type": "TEXT",
            "output_filename": out_name,
            "download_url": f"/api/exports/download/{out_name}",
            "capacity_used": f"{res['capacity_used_percent']}%",
            "bytes_embedded": res["bytes_embedded"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/transfer/outgoing/file")
async def api_transfer_outgoing_file(
    cover_filename: str = Form(...),
    payload_file: UploadFile = File(...),
    passphrase: str = Form(...),
    session = Depends(require_private_session)
):
    """Outgoing Pipeline 2: Mengenkripsi file biner (ChaCha20-Poly1305) dan menyisipkan ke cover."""
    cover_path = os.path.join(CATALOG_DIR, os.path.basename(cover_filename))
    if not os.path.exists(cover_path):
        raise HTTPException(status_code=404, detail="Foto cover tidak ditemukan!")

    clean_payload_name = os.path.basename(payload_file.filename)
    temp_payload_path = os.path.join(EXPORTS_DIR, f"temp_{clean_payload_name}")
    with open(temp_payload_path, "wb") as buffer:
        shutil.copyfileobj(payload_file.file, buffer)

    out_name = f"MODIFIED_STEGO_{os.path.splitext(os.path.basename(cover_filename))[0]}.png"
    out_path = os.path.join(EXPORTS_DIR, out_name)

    try:
        res = embed_binary_file_payload(cover_path, temp_payload_path, passphrase, out_path)
        # Salin ke katalog agar foto yang sudah dimodifikasi langsung muncul di Library & Filmstrip
        shutil.copy2(out_path, os.path.join(CATALOG_DIR, out_name))
        return {
            "success": True,
            "type": "FILE",
            "output_filename": out_name,
            "download_url": f"/api/exports/download/{out_name}",
            "original_filename": clean_payload_name,
            "capacity_used": f"{res['capacity_used_percent']}%",
            "bytes_embedded": res["bytes_embedded"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(temp_payload_path):
            os.remove(temp_payload_path)


@app.post("/api/transfer/outgoing/image")
async def api_transfer_outgoing_image(
    cover_filename: str = Form(...),
    secret_image: UploadFile = File(...),
    passphrase: str = Form(...),
    session = Depends(require_private_session)
):
    """Outgoing Pipeline 3: Menyembunyikan citra rahasia ke citra decoy cover."""
    cover_path = os.path.join(CATALOG_DIR, os.path.basename(cover_filename))
    if not os.path.exists(cover_path):
        raise HTTPException(status_code=404, detail="Foto cover tidak ditemukan!")

    clean_img_name = os.path.basename(secret_image.filename)
    temp_sec_path = os.path.join(EXPORTS_DIR, f"temp_{clean_img_name}")
    with open(temp_sec_path, "wb") as buffer:
        shutil.copyfileobj(secret_image.file, buffer)

    out_name = f"MODIFIED_STEGO_{os.path.splitext(os.path.basename(cover_filename))[0]}.png"
    out_path = os.path.join(EXPORTS_DIR, out_name)

    try:
        res = embed_secret_image_in_decoy(cover_path, temp_sec_path, out_path, passphrase=passphrase)
        # Salin ke katalog agar foto yang sudah dimodifikasi langsung muncul di Library & Filmstrip
        shutil.copy2(out_path, os.path.join(CATALOG_DIR, out_name))
        return {
            "success": True,
            "type": "IMAGE",
            "output_filename": out_name,
            "download_url": f"/api/exports/download/{out_name}",
            "capacity_used": f"{res['capacity_used_percent']}%",
            "bytes_embedded": res["bytes_embedded"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(temp_sec_path):
            os.remove(temp_sec_path)


@app.post("/api/transfer/incoming/extract")
async def api_transfer_incoming_extract(
    stego_file: Optional[UploadFile] = File(None),
    filename: Optional[str] = Form(""),
    vigenere_key: str = Form(""),
    aes_key: str = Form(""),
    passphrase: str = Form(""),
    session = Depends(require_private_session)
):
    """Incoming Pipeline: Ekstraksi dan pengungkapan otomatis muatan stego."""
    temp_created = False
    temp_path = ""

    if stego_file and stego_file.filename:
        clean_name = os.path.basename(stego_file.filename)
        temp_path = os.path.join(EXPORTS_DIR, f"incoming_{clean_name}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(stego_file.file, buffer)
        temp_created = True
    elif filename:
        clean_name = os.path.basename(filename)
        candidate1 = os.path.join(CATALOG_DIR, clean_name)
        candidate2 = os.path.join(EXPORTS_DIR, clean_name)
        if os.path.exists(candidate1):
            temp_path = candidate1
        elif os.path.exists(candidate2):
            temp_path = candidate2
        else:
            raise HTTPException(status_code=404, detail="File foto stego tidak ditemukan di katalog!")
    else:
        raise HTTPException(status_code=400, detail="Unggah file stego atau pilih nama berkas katalog!")

    try:
        active_pass = passphrase or aes_key
        res = extract_and_reveal(
            temp_path,
            vigenere_key=vigenere_key,
            aes_key=active_pass,
            passphrase=active_pass,
            export_dir=EXPORTS_DIR
        )
        if res.get("saved_file"):
            res["download_url"] = f"/api/exports/download/{os.path.basename(res['saved_file'])}"
        return res
    finally:
        if temp_created and os.path.exists(temp_path):
            os.remove(temp_path)


# =============================================================================
# 6. DEVELOP & EXPORT WORKSPACE ENDPOINTS
# =============================================================================
class DevelopExportRequest(BaseModel):
    filename: str
    export_format: str = "JPEG"
    quality: int = 90
    scale_percent: int = 100
    image_base64: Optional[str] = None

@app.post("/api/develop/export")
def api_develop_export(req: DevelopExportRequest):
    """Mengekspor foto hasil Develop dengan format, resolusi, dan kompresi yang dipilih."""
    clean_name = os.path.basename(req.filename)
    src_path = os.path.join(CATALOG_DIR, clean_name)

    # FIX: penyesuaian payload & state
    base_title = os.path.splitext(clean_name)[0]
    while base_title.upper().startswith("EXPORT_"):
        base_title = base_title[len("EXPORT_"):]
    ext = req.export_format.lower()
    if ext == "jpeg":
        ext = "jpg"
    out_name = f"EXPORT_{base_title}.{ext}"
    out_path = os.path.join(EXPORTS_DIR, out_name)

    try:
        from PIL import Image
        if req.image_base64:
            img_bytes = base64.b64decode(req.image_base64.split(",")[-1])
            img = Image.open(io.BytesIO(img_bytes))
        else:
            if not os.path.exists(src_path):
                raise HTTPException(status_code=404, detail="File foto asli tidak ditemukan!")
            img = Image.open(src_path)

        # Skala resolusi jika diubah
        if req.scale_percent != 100 and req.scale_percent > 0:
            new_w = max(1, int(img.width * (req.scale_percent / 100.0)))
            new_h = max(1, int(img.height * (req.scale_percent / 100.0)))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        fmt = req.export_format.upper()
        if fmt in ("JPEG", "JPG"):
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(out_path, format="JPEG", quality=max(10, min(100, req.quality)), optimize=True)
        elif fmt == "PNG":
            img.save(out_path, format="PNG")
        elif fmt == "TIFF":
            img.save(out_path, format="TIFF")
        else:
            img.save(out_path)

        return {
            "success": True,
            "filename": out_name,
            # FIX: penyesuaian payload & state
            "format": fmt,
            "download_url": f"/api/exports/download/{out_name}",
            "size_mb": round(os.path.getsize(out_path) / (1024 * 1024), 2),
            "dimensions": f"{img.width}x{img.height}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 7. MENU LUAR: DEKRIPSI & EKSTRAKTOR (COMPATIBILITY)
# =============================================================================
@app.post("/api/stego/reveal-file")
async def api_reveal_file(
    file: UploadFile = File(...),
    vigenere_key: str = Form(""),
    aes_key: str = Form(""),
    session = Depends(require_private_session)
):
    temp_path = os.path.join(EXPORTS_DIR, f"scan_{os.path.basename(file.filename)}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    res = extract_and_reveal(temp_path, vigenere_key, aes_key, EXPORTS_DIR)
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    if res.get("type") == "IMAGE":
        res["download_url"] = f"/api/exports/download/{res['filename']}"
        
    return res


@app.get("/api/exports/download/{filename}")
def download_export_file(filename: str):
    clean_name = os.path.basename(filename)
    p = os.path.join(EXPORTS_DIR, clean_name)
    if not os.path.exists(p):
        raise HTTPException(status_code=404, detail="File tidak ditemukan!")
    return FileResponse(p, filename=clean_name)


# =============================================================================
# 6. MENU LUAR: BRANKAS FOTO TERKUNCI (CHACHA20)
# =============================================================================
@app.get("/api/vault/locked-photos")
def list_locked_photos():
    """Mengambil daftar foto yang sedang berstatus terkunci (.enc) di dalam katalog."""
    locked = []
    for f in os.listdir(CATALOG_DIR):
        if f.endswith(".enc"):
            p = os.path.join(CATALOG_DIR, f)
            locked.append({
                "filename": f,
                "original_name": f[:-4],
                "size_mb": round(os.path.getsize(p) / (1024 * 1024), 2),
                "modified": time.ctime(os.path.getmtime(p))
            })
    return {"locked_photos": locked}


@app.post("/api/vault/lock-photo")
def lock_active_photo(
    filename: str = Form(...),
    passphrase: str = Form(...),
    session = Depends(require_private_session)
):
    clean_name = os.path.basename(filename)
    p = os.path.join(CATALOG_DIR, clean_name)
    if not os.path.exists(p):
        raise HTTPException(status_code=404, detail="Foto tidak ditemukan!")
    out_p = p + ".enc"
    encrypt_file(p, out_p, passphrase)
    os.remove(p) # Hapus file asli dari disk
    return {"success": True, "locked_filename": clean_name + ".enc"}


@app.post("/api/vault/unlock-photo")
def unlock_photo(
    filename: str = Form(...),
    passphrase: str = Form(...),
    session = Depends(require_private_session)
):
    clean_name = os.path.basename(filename)
    p = os.path.join(CATALOG_DIR, clean_name)
    if not os.path.exists(p):
        raise HTTPException(status_code=404, detail="File terkunci tidak ditemukan!")
    out_name = clean_name[:-4] if clean_name.endswith(".enc") else clean_name
    out_p = os.path.join(CATALOG_DIR, out_name)
    try:
        decrypt_file(p, out_p, passphrase)
        os.remove(p) # Hapus .enc
        return {"success": True, "unlocked_filename": out_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membuka kunci: {str(e)}")


# =============================================================================
# 7. MENU LUAR: AUDIT BLOCKCHAIN
# =============================================================================
@app.post("/api/blockchain/seal")
def seal_active_photo_blockchain(
    filename: str = Form(...),
    agent_id: str = Form(...),
    notes: str = Form(...),
    session = Depends(require_private_session)
):
    clean_name = os.path.basename(filename)
    photo_path = os.path.join(CATALOG_DIR, clean_name)
    if not os.path.exists(photo_path):
        raise HTTPException(status_code=404, detail="Foto tidak ditemukan!")
    block = blockchain.add_photo_asset(photo_path, agent_id, notes)
    return {"success": True, "block": block.to_dict()}


@app.get("/api/blockchain/status")
def get_blockchain_status():
    # FIX: audit memakai validasi aktual terhadap rantai yang tersimpan.
    blockchain.load_chain()
    is_valid, msg = blockchain.verify_integrity()
    return {
        "success": True,
        "is_valid": bool(is_valid),
        "message": msg,
        "blocks_checked": len(blockchain.chain),
        "chain": [b.to_dict() for b in blockchain.chain]
    }


@app.post("/api/blockchain/simulate-tamper")
def simulate_blockchain_tamper(session = Depends(require_private_session)):
    # FIX: simulasi memverifikasi perubahan hash aktual lalu memulihkan ledger tersimpan.
    blockchain.load_chain()
    if len(blockchain.chain) <= 1:
        raise HTTPException(status_code=400, detail="Mint foto ke blockchain terlebih dahulu!")
    try:
        blockchain.chain[1].metadata = "PALSU! Bukti foto telah dimanipulasi oknum!"
        is_valid, msg = blockchain.verify_integrity()
        return {
            "success": True,
            "tamper_detected": not is_valid,
            "is_valid": bool(is_valid),
            "message": msg
        }
    finally:
        blockchain.load_chain()


FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
