"""
=============================================================================
DARKROOM 2.0 - DETERMINISTIC LSB STEGANOGRAPHY ENGINE (RFC/STANDARDS-BASED)
=============================================================================
Arsitektur Framing Biner Deterministik V2:
[4B MAGIC: 'DKRM'] [1B VERSION: 0x02] [1B TYPE: 1=TXT, 2=FILE, 3=IMG]
[2B META_LEN] [JSON METADATA] [4B PAYLOAD_LEN] [ENCRYPTED BINARY PAYLOAD]

Karakteristik & Integritas:
1. Tidak menggunakan string delimiter rentan (seperti :::END:::).
2. Membaca header panjang biner presisi (Payload Length Prefix).
3. Mendukung muatan biner byte-for-byte exact: TEXT, FILE, dan IMAGE.
4. Menolak mutlak muatan yang melebihi kapasitas cover image (Zero Lossy Downsampling).
5. Output lossless PNG wajib; Cover asli dipertahankan tanpa modifikasi.
6. Akselerasi operasi biner matriks NumPy tervektorisasi (& 254 | bit).
7. Mendukung fallback pembongkaran arsip steganografi v1.
=============================================================================
"""

import os
import sys
import json
import io
from typing import Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.crypto.super_encrypt import super_encrypt, super_decrypt
from backend.crypto.aes_cipher import aes_encrypt, aes_decrypt
from backend.crypto.file_cipher import encrypt_file, decrypt_file

# Konstanta Protokol Framing V2
STEGO_MAGIC_V2 = b"DKRM" # 4 Bytes
STEGO_VERSION_V2 = 0x02  # 1 Byte

TYPE_TEXT = 0x01
TYPE_FILE = 0x02
TYPE_IMAGE = 0x03

# Konstanta Protokol Legacy V1 (untuk Backward Compatibility)
LEGACY_HEADER_TEXT = b"DARKROOM_TEXT:"
LEGACY_HEADER_IMAGE = b"DARKROOM_IMG:"
LEGACY_DELIMITER = b":::END_ATOSE:::"


def calculate_image_capacity(cover_image_path: str) -> Dict[str, Any]:
    """
    Menghitung kapasitas muatan biner maksimal dari citra pembawa.
    Hanya menggunakan kanal R, G, B (1 bit per kanal warna = 3 bit per pixel).
    """
    if not os.path.exists(cover_image_path):
        raise FileNotFoundError(f"Foto sumber {cover_image_path} tidak ditemukan!")

    with Image.open(cover_image_path) as img:
        w, h = img.size
        mode = img.mode
        img_format = img.format or os.path.splitext(cover_image_path)[1].replace(".", "").upper()

    total_usable_pixels = w * h
    total_bits = total_usable_pixels * 3
    total_bytes = total_bits // 8

    # Estimasi overhead framing v2 (Magic 4B + Ver 1B + Type 1B + MetaLen 2B + Meta ~150B + PayLen 4B)
    header_overhead_bytes = 170
    net_capacity_bytes = max(0, total_bytes - header_overhead_bytes)

    is_lossless = img_format in ("PNG", "BMP", "TIFF", "TIF", "WEBP")
    suitability_note = "Optimal untuk LSB (Format Lossless)" if is_lossless else "Format Lossy (JPEG): Akan diekspor sebagai Lossless PNG"

    if net_capacity_bytes < 1024:
        cap_fmt = f"{net_capacity_bytes} B"
    elif net_capacity_bytes < 1024 * 1024:
        cap_fmt = f"{round(net_capacity_bytes / 1024, 1)} KB"
    else:
        cap_fmt = f"{round(net_capacity_bytes / (1024 * 1024), 2)} MB"

    return {
        "width": w,
        "height": h,
        "mode": mode,
        "format": img_format,
        "is_suitable": is_lossless,
        "suitability_note": suitability_note,
        "total_pixels": total_usable_pixels,
        "gross_capacity_bytes": total_bytes,
        "net_capacity_bytes": net_capacity_bytes,
        "max_payload_bytes": net_capacity_bytes,
        "max_payload_formatted": cap_fmt,
        "net_capacity_kb": round(net_capacity_bytes / 1024, 2),
        "net_capacity_mb": round(net_capacity_bytes / (1024 * 1024), 2)
    }


def pack_framed_payload_v2(payload_type: int, metadata: dict, payload_bytes: bytes) -> bytes:
    """
    Mengemas data biner ke dalam bingkai protokol V2 deterministik.
    """
    meta_json = json.dumps(metadata, sort_keys=True).encode('utf-8')
    if len(meta_json) > 65535:
        raise ValueError("Ukuran metadata melebihi batas maksimal 64 KB!")

    meta_len_bytes = len(meta_json).to_bytes(2, byteorder='big')
    pay_len_bytes = len(payload_bytes).to_bytes(4, byteorder='big')

    packet = (
        STEGO_MAGIC_V2 +
        bytes([STEGO_VERSION_V2]) +
        bytes([payload_type]) +
        meta_len_bytes +
        meta_json +
        pay_len_bytes +
        payload_bytes
    )
    return packet


def embed_packet_into_cover(cover_image_path: str, packet_bytes: bytes, output_image_path: str) -> dict:
    """
    Menyisipkan paket biner langsung ke dalam bit LSB kanal RGB citra.
    Menjamin cover asli tidak diubah dan hasil disimpan dalam format lossless PNG.
    """
    cap = calculate_image_capacity(cover_image_path)
    total_needed_bits = len(packet_bytes) * 8

    if len(packet_bytes) > cap["gross_capacity_bytes"]:
        raise ValueError(
            f"Ukuran muatan ({len(packet_bytes)} byte) melebihi kapasitas maksimal foto pembawa ({cap['gross_capacity_bytes']} byte)! "
            "Pilihlah foto cover beresolusi lebih tinggi."
        )

    # Buka citra dan konversi ke RGB/RGBA
    with Image.open(cover_image_path) as orig_img:
        has_alpha = orig_img.mode in ("RGBA", "LA") or (orig_img.mode == "P" and "transparency" in orig_img.info)
        img = orig_img.convert("RGBA" if has_alpha else "RGB")

    arr = np.array(img, dtype=np.uint8)
    h, w, channels = arr.shape

    # Kita hanya memodifikasi 3 kanal pertama (R, G, B); kanal Alpha (jika ada) dipertahankan utuh
    rgb_view = arr[:, :, :3]
    flat_rgb = rgb_view.reshape(-1)

    # Ekstrak bit dari paket biner
    bits = np.unpackbits(np.frombuffer(packet_bytes, dtype=np.uint8))
    num_bits = len(bits)

    # Terapkan masking LSB berkecepatan tinggi: (pixel & 254) | bit
    flat_rgb[:num_bits] = (flat_rgb[:num_bits] & np.uint8(254)) | bits

    # Pastikan format output berekstensi .png lossless
    if not output_image_path.lower().endswith(".png"):
        output_image_path += ".png"

    os.makedirs(os.path.dirname(os.path.abspath(output_image_path)), exist_ok=True)
    stego_img = Image.fromarray(arr)
    stego_img.save(output_image_path, format="PNG", optimize=False)

    capacity_used_pct = round((num_bits / len(flat_rgb)) * 100, 3)

    return {
        "status": "SUCCESS",
        "output_path": output_image_path,
        "bytes_embedded": len(packet_bytes),
        "capacity_used_percent": capacity_used_pct,
        "cover_dimensions": f"{w}x{h}"
    }


def extract_raw_packet(stego_image_path: str) -> Optional[Tuple[int, dict, bytes]]:
    """
    Mengekstrak paket biner V2 deterministik.
    Mengembalikan: (payload_type, metadata_dict, payload_bytes) atau None jika bukan Darkroom stego.
    """
    if not os.path.exists(stego_image_path):
        raise FileNotFoundError(f"Foto {stego_image_path} tidak ditemukan!")

    with Image.open(stego_image_path) as img:
        arr = np.array(img.convert("RGB"), dtype=np.uint8)

    flat_rgb = arr[:, :, :3].reshape(-1)

    # 1. Ekstrak 8 byte pertama (64 bit) untuk memeriksa MAGIC dan VERSION
    if len(flat_rgb) < 64:
        return None

    header_bits = (flat_rgb[:64] & np.uint8(1)).astype(np.uint8)
    header_bytes = np.packbits(header_bits).tobytes()

    magic = header_bytes[:4]
    version = header_bytes[4]

    # Validasi Protokol V2
    if magic == STEGO_MAGIC_V2 and version == STEGO_VERSION_V2:
        payload_type = header_bytes[5]
        meta_len = int.from_bytes(header_bytes[6:8], byteorder='big')

        # Hitung bit offset untuk membaca metadata
        meta_start_bit = 64
        meta_end_bit = meta_start_bit + (meta_len * 8)
        if len(flat_rgb) < meta_end_bit + 32:
            return None

        meta_bits = (flat_rgb[meta_start_bit:meta_end_bit] & np.uint8(1)).astype(np.uint8)
        meta_bytes = np.packbits(meta_bits).tobytes()
        metadata = json.loads(meta_bytes.decode('utf-8'))

        # Baca 4 byte panjang payload (32 bit)
        paylen_start_bit = meta_end_bit
        paylen_end_bit = paylen_start_bit + 32
        paylen_bits = (flat_rgb[paylen_start_bit:paylen_end_bit] & np.uint8(1)).astype(np.uint8)
        pay_len = int.from_bytes(np.packbits(paylen_bits).tobytes(), byteorder='big')

        # Baca persis pay_len byte muatan
        payload_start_bit = paylen_end_bit
        payload_end_bit = payload_start_bit + (pay_len * 8)

        if len(flat_rgb) < payload_end_bit:
            raise ValueError("Citra steganografi terpotong: Ukuran bit LSB lebih kecil dari panjang payload terdaftar!")

        payload_bits = (flat_rgb[payload_start_bit:payload_end_bit] & np.uint8(1)).astype(np.uint8)
        payload_bytes = np.packbits(payload_bits).tobytes()

        return (payload_type, metadata, payload_bytes)

    # 2. Fallback: Ekstraksi Protokol Legacy V1
    return _extract_legacy_v1_packet(flat_rgb)


def _extract_legacy_v1_packet(flat_rgb: np.ndarray) -> Optional[Tuple[int, dict, bytes]]:
    """Membongkar arsip steganografi format legacy v1 yang menggunakan delimiter."""
    chunk_size = 16 * 1024
    collected_bytes = bytearray()

    for i in range(0, min(len(flat_rgb), 30 * 1024 * 1024), chunk_size):
        chunk = flat_rgb[i : i + chunk_size]
        bits = (chunk & 1).astype(np.uint8)
        valid_len = (len(bits) // 8) * 8
        if valid_len > 0:
            collected_bytes.extend(np.packbits(bits[:valid_len]).tobytes())
            if LEGACY_DELIMITER in collected_bytes:
                idx = collected_bytes.index(LEGACY_DELIMITER)
                raw_data = bytes(collected_bytes[:idx])

                if raw_data.startswith(LEGACY_HEADER_TEXT):
                    ct = raw_data[len(LEGACY_HEADER_TEXT):]
                    return (TYPE_TEXT, {"legacy": True, "format": "v1_text"}, ct)
                elif raw_data.startswith(LEGACY_HEADER_IMAGE):
                    body = raw_data[len(LEGACY_HEADER_IMAGE):]
                    colon_idx = body.index(b":")
                    ext = body[:colon_idx].decode('utf-8', errors='ignore')
                    img_bytes = body[colon_idx + 1:]
                    return (TYPE_IMAGE, {"legacy": True, "format": "v1_image", "ext": ext}, img_bytes)
                break
    return None


# =============================================================================
# OPERASI TINGKAT TINGGI: EMBED TEXT, FILE, IMAGE
# =============================================================================

def embed_super_crypto_text(
    cover_path: str,
    plaintext: str,
    vigenere_key: str,
    aes_key: str,
    output_path: str
) -> dict:
    """
    Mengenkripsi teks secara berlapis (Vigenère + AES-256-GCM) lalu menyisipkannya
    ke dalam foto pembawa dengan framing biner V2.
    """
    crypto_res = super_encrypt(plaintext, vigenere_key, aes_key)
    ciphertext_str = crypto_res["final_ciphertext"]
    payload_bytes = ciphertext_str.encode('utf-8')

    metadata = {
        "payload_type": "TEXT",
        "cipher": "Vigenere+AES-256-GCM",
        "length_chars": len(plaintext),
        "vigenere_used": bool(vigenere_key)
    }

    packet = pack_framed_payload_v2(TYPE_TEXT, metadata, payload_bytes)
    res = embed_packet_into_cover(cover_path, packet, output_path)

    res["intermediate_vigenere"] = crypto_res["intermediate_vigenere"]
    res["final_ciphertext"] = ciphertext_str
    return res


def embed_binary_file_payload(
    cover_path: str,
    file_path: str,
    passphrase: str,
    output_path: str
) -> dict:
    """
    Mengenkripsi file biner menggunakan ChaCha20-Poly1305 AEAD lalu menyisipkannya
    ke dalam foto pembawa secara byte-for-byte exact.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File payload {file_path} tidak ditemukan!")

    temp_enc_file = output_path + ".tmp.enc"
    try:
        enc_info = encrypt_file(file_path, temp_enc_file, passphrase)
        with open(temp_enc_file, "rb") as f:
            encrypted_file_bytes = f.read()
    finally:
        if os.path.exists(temp_enc_file):
            os.remove(temp_enc_file)

    orig_name = os.path.basename(file_path)
    metadata = {
        "payload_type": "FILE",
        "filename": orig_name,
        "extension": os.path.splitext(orig_name)[1].lower(),
        "cipher": "ChaCha20-Poly1305 AEAD",
        "original_size": os.path.getsize(file_path)
    }

    packet = pack_framed_payload_v2(TYPE_FILE, metadata, encrypted_file_bytes)
    res = embed_packet_into_cover(cover_path, packet, output_path)
    res["original_filename"] = orig_name
    return res


def embed_secret_image_in_decoy(
    decoy_cover_path: str,
    secret_image_path: str,
    output_path: str,
    passphrase: str = "DarkroomDecoyKey2026!",
    original_filename: str = ""
) -> dict:
    """
    Menyembunyikan file citra rahasia ke dalam citra decoy pembawa.
    File citra rahasia dienkripsi biner via ChaCha20-Poly1305 AEAD dan dijaga
    keasliannya tanpa kompresi lossy JPEG.
    """
    if not os.path.exists(secret_image_path):
        raise FileNotFoundError(f"File gambar rahasia {secret_image_path} tidak ditemukan!")

    temp_enc = output_path + ".img.tmp.enc"
    try:
        encrypt_file(secret_image_path, temp_enc, passphrase)
        with open(temp_enc, "rb") as f:
            enc_img_bytes = f.read()
    finally:
        if os.path.exists(temp_enc):
            os.remove(temp_enc)

    orig_name = os.path.basename(original_filename or secret_image_path)
    with Image.open(secret_image_path) as s_img:
        res_str = f"{s_img.width}x{s_img.height}"
        fmt_str = s_img.format or "PNG"

    metadata = {
        "payload_type": "IMAGE",
        "filename": orig_name,
        "resolution": res_str,
        "format": fmt_str,
        "cipher": "ChaCha20-Poly1305 AEAD",
        "original_size": os.path.getsize(secret_image_path)
    }

    packet = pack_framed_payload_v2(TYPE_IMAGE, metadata, enc_img_bytes)
    res = embed_packet_into_cover(decoy_cover_path, packet, output_path)
    res["secret_dimensions"] = res_str
    return res


# =============================================================================
# OPERASI EKSTRAKSI & BONGKAR DATA (INCOMING PIPELINE)
# =============================================================================

def extract_and_reveal(
    stego_image_path: str,
    vigenere_key: str = "",
    aes_key: str = "",
    passphrase: str = "",
    export_dir: str = ""
) -> dict:
    """
    Membongkar dan mengekstrak data dari citra steganografi.
    Mengidentifikasi tipe konten (TEXT, FILE, IMAGE) secara otomatis.
    """
    parsed = extract_raw_packet(stego_image_path)
    if not parsed:
        return {
            "has_payload": False,
            "message": "Tidak dikenali payload steganografi Darkroom yang sah pada citra ini."
        }

    payload_type, metadata, payload_bytes = parsed
    if not export_dir:
        export_dir = os.path.dirname(os.path.abspath(stego_image_path))
    os.makedirs(export_dir, exist_ok=True)

    # 1. Tipe Konten: TEXT
    if payload_type == TYPE_TEXT:
        ct_str = payload_bytes.decode('utf-8', errors='ignore')
        # Coba dekripsi jika kunci diberikan
        active_key = aes_key or passphrase
        if vigenere_key and active_key:
            try:
                dec = super_decrypt(ct_str, vigenere_key, active_key)
                return {
                    "has_payload": True,
                    "type": "TEXT",
                    "is_decrypted": True,
                    "plaintext": dec["final_plaintext"],
                    "intermediate_aes": dec["intermediate_aes"],
                    "raw_ciphertext": ct_str,
                    "metadata": metadata
                }
            except Exception as e:
                return {
                    "has_payload": True,
                    "type": "TEXT",
                    "is_decrypted": False,
                    "raw_ciphertext": ct_str,
                    "metadata": metadata,
                    "error": f"Gagal mendekripsi teks: {str(e)}"
                }
        return {
            "has_payload": True,
            "type": "TEXT",
            "is_decrypted": False,
            "raw_ciphertext": ct_str,
            "metadata": metadata
        }

    # 2. Tipe Konten: FILE
    elif payload_type == TYPE_FILE:
        target_name = metadata.get("filename", "recovered_document.bin")
        out_path = os.path.join(export_dir, f"RECOVERED_{target_name}")

        active_passphrase = passphrase or aes_key
        if not active_passphrase:
            return {
                "has_payload": True,
                "type": "FILE",
                "is_decrypted": False,
                "filename": target_name,
                "metadata": metadata,
                "message": "Masukkan passphrase untuk membuka berkas biner terenkripsi."
            }

        # Simpan sementara biner terenkripsi
        tmp_enc = out_path + ".tmp.enc"
        try:
            with open(tmp_enc, "wb") as f:
                f.write(payload_bytes)
            dec_res = decrypt_file(tmp_enc, out_path, active_passphrase)
            return {
                "has_payload": True,
                "type": "FILE",
                "is_decrypted": True,
                "saved_file": out_path,
                "filename": os.path.basename(out_path),
                "original_filename": target_name,
                "metadata": metadata
            }
        except Exception as e:
            return {
                "has_payload": True,
                "type": "FILE",
                "is_decrypted": False,
                "filename": target_name,
                "metadata": metadata,
                "error": f"Gagal mendekripsi berkas: {str(e)}"
            }
        finally:
            if os.path.exists(tmp_enc):
                os.remove(tmp_enc)

    # 3. Tipe Konten: IMAGE
    elif payload_type == TYPE_IMAGE:
        # Periksa apakah ini arsip legacy v1 (unencrypted image bytes)
        if metadata.get("legacy"):
            ext = metadata.get("ext", ".jpg")
            out_filename = f"REVEALED_SECRET_IMAGE{ext}"
            out_path = os.path.join(export_dir, out_filename)
            with open(out_path, "wb") as f:
                f.write(payload_bytes)
            return {
                "has_payload": True,
                "type": "IMAGE",
                "is_decrypted": True,
                "saved_file": out_path,
                "filename": out_filename,
                "metadata": metadata
            }

        target_name = metadata.get("filename", "secret_photo.png")
        out_path = os.path.join(export_dir, f"REVEALED_{target_name}")
        active_passphrase = passphrase or aes_key or "DarkroomDecoyKey2026!"

        tmp_enc = out_path + ".img.tmp.enc"
        try:
            with open(tmp_enc, "wb") as f:
                f.write(payload_bytes)
            decrypt_file(tmp_enc, out_path, active_passphrase)
            return {
                "has_payload": True,
                "type": "IMAGE",
                "is_decrypted": True,
                "saved_file": out_path,
                "filename": os.path.basename(out_path),
                "metadata": metadata
            }
        except Exception as e:
            return {
                "has_payload": True,
                "type": "IMAGE",
                "is_decrypted": False,
                "filename": target_name,
                "metadata": metadata,
                "error": f"Gagal mendekripsi foto rahasia: {str(e)}"
            }
        finally:
            if os.path.exists(tmp_enc):
                os.remove(tmp_enc)

    return {
        "has_payload": False,
        "message": "Format payload tidak dikenali."
    }
