"""
=============================================================================
DARKROOM - DATABASE DENGAN PESAN TERENKRIPSI (KRITERIA 5)
=============================================================================
Kriteria Tugas: Pesan penting dienkripsi pada basisdata yang digunakan.

Metode yang Digunakan:
Field-Level Encryption (FLE) berbasis SQLite.
- Kolom umum (id, judul, nama file) disimpan normal untuk indexing & query cepat.
- Kolom SENSITIF ('secret_intel_note') SELALU DIENKRIPSI menggunakan AES-256
  sebelum dieksekusi dengan perintah INSERT / UPDATE ke basisdata.

Keamanan Terhadap Pencurian Data:
Jika penyerang mencuri file basisdata 'darkroom.db' dan membukanya menggunakan
aplikasi eksternal (seperti DB Browser for SQLite atau teks editor biasa),
pesan-pesan penting jurnalis tidak akan terbaca dan hanya berupa teks acak Base64.
=============================================================================
"""

import os
import sys
import sqlite3
from datetime import datetime

# Path setup agar bisa menggunakan modul kriptografi yang sudah dibuat
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
sys.path.append(PROJECT_ROOT)

from backend.crypto.aes_cipher import aes_encrypt, aes_decrypt

# Lokasi file database SQLite lokal
DB_PATH = os.path.join(PROJECT_ROOT, "storage", "darkroom.db")


def get_connection():
    """Membuka koneksi ke database SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Agar hasil query bisa diakses dengan nama kolom
    return conn


def init_db():
    """
    Membuat tabel-tabel database jika belum ada.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Tabel Katalog Foto & Catatan Intelijen Rahasia
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS photo_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        photo_title TEXT NOT NULL,
        filename TEXT NOT NULL,
        public_caption TEXT,
        secret_intel_note TEXT NOT NULL,  -- KOLOM INI DIENKRIPSI!
        photo_hash TEXT,
        created_at TEXT NOT NULL
    );
    """)
    
    # 2. Tabel Arsip File RAW Vault
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS master_vault_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_name TEXT NOT NULL,
        encrypted_name TEXT NOT NULL,
        algorithm TEXT NOT NULL,
        locked_at TEXT NOT NULL
    );
    """)
    
    conn.commit()
    conn.close()


def insert_photo_with_encrypted_note(title: str, filename: str, public_caption: str,
                                     secret_note: str, photo_hash: str, passphrase: str) -> int:
    """
    Menyimpan foto baru ke database dengan pesan penting yang DIENKRIPSI menggunakan AES-256.
    """
    init_db()
    
    # ENKRIPSI PESAN PENTING SEBELUM MASUK DATABASE
    encrypted_note = aes_encrypt(secret_note, passphrase)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO photo_catalog 
        (photo_title, filename, public_caption, secret_intel_note, photo_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, filename, public_caption, encrypted_note, photo_hash, timestamp))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_raw_database_records() -> list:
    """
    Mengambil data langsung dari SQLite tanpa didekripsi.
    Ini mensimulasikan bagaimana penyerang melihat isi database.
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, photo_title, filename, public_caption, secret_intel_note, created_at FROM photo_catalog")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_decrypted_database_records(passphrase: str) -> list:
    """
    Mengambil data dari SQLite dan mendekripsi kolom 'secret_intel_note' untuk agen resmi.
    """
    raw_records = get_raw_database_records()
    decrypted_records = []
    
    for rec in raw_records:
        rec_copy = dict(rec)
        try:
            # Dekripsi kolom sensitif menggunakan AES-256
            rec_copy["secret_intel_note"] = aes_decrypt(rec["secret_intel_note"], passphrase)
            rec_copy["decryption_status"] = "DECRYPTED_SUCCESS"
        except Exception:
            rec_copy["secret_intel_note"] = "[GAGAL DEKRIPSI: KUNCI SALAH]"
            rec_copy["decryption_status"] = "DECRYPTED_FAILED"
            
        decrypted_records.append(rec_copy)
        
    return decrypted_records


# =============================================================================
# DEMO INTERAKTIF DI TERMINAL
# =============================================================================
if __name__ == "__main__":
    init_db()
    
    print("\n" + "="*70)
    print("      DARKROOM - DATABASE DENGAN PESAN TERENKRIPSI (SQLITE)")
    print("="*70)
    print("Kriteria 5: Pesan penting dienkripsi pada basisdata yang digunakan.")
    print(f"File Database: {DB_PATH}")
    print("-" * 70)
    
    print("\nPilih Aksi:")
    print("1. Tambah Catatan Foto Rahasia Baru (Otomatis Dienkripsi ke DB)")
    print("2. Intip Database Mentah (Simulasi Penyerang / DB Browser - Ciphertext)")
    print("3. Buka Database Resmi (Dekripsi Pesan sebagai Agen yang Sah)")
    choice = input("Pilihan (1/2/3): ").strip()
    
    if choice == "1":
        print("\n--- TAMBAH FOTO & CATATAN RAHASIA KE DATABASE ---")
        judul = input("Judul Liputan Foto : ").strip()
        if not judul:
            judul = "Pertemuan Diplomat Asing di Cafe Senayan"
            print(f"(Default: '{judul}')")
            
        nama_file = input("Nama File Foto     : ").strip()
        if not nama_file:
            nama_file = "DSC_0812_SENAYAN.JPG"
            print(f"(Default: '{nama_file}')")
            
        keterangan_publik = input("Keterangan Publik (Biasa): ").strip()
        if not keterangan_publik:
            keterangan_publik = "Foto suasana sore hari di Senayan."
            print(f"(Default: '{keterangan_publik}')")
            
        print("\n[PESAN PENTING SENSITIF]")
        pesan_rahasia = input("Ketik Catatan Rahasia Intelijen: ").strip()
        if not pesan_rahasia:
            pesan_rahasia = "Target A menyerahkan flashdisk biru ke Target B pada pukul 17.15 WIB."
            print(f"(Default: '{pesan_rahasia}')")
            
        kunci = input("\nMasukkan Passphrase Kunci Enkripsi DB: ").strip()
        if not kunci:
            kunci = "KunciDatabaseDarkroom2026!"
            print(f"(Default: '{kunci}')")
            
        new_id = insert_photo_with_encrypted_note(
            judul, nama_file, keterangan_publik, pesan_rahasia, "hash_dummy_01", kunci
        )
        
        print("\n" + "="*70)
        print(f"[SUKSES] Data berhasil disimpan ke SQLite dengan ID #{new_id}!")
        print("Pesan sensitif otomatis dienkripsi dengan AES-256 sebelum masuk ke disk.")
        print("="*70 + "\n")
        
    elif choice == "2":
        print("\n" + "="*70)
        print("SIMULASI PENYERANG: MELIHAT DATABASE APA ADANYA (RAW)")
        print("Jika penyerang mencuri file 'darkroom.db', inilah yang mereka lihat:")
        print("="*70)
        
        records = get_raw_database_records()
        if not records:
            print("\nDatabase masih kosong! Jalankan Opsi 1 terlebih dahulu.")
        else:
            for r in records:
                print(f"\n[ID #{r['id']}] {r['photo_title']} ({r['filename']})")
                print(f"  • Waktu Dibuat       : {r['created_at']}")
                print(f"  • Keterangan Publik  : {r['public_caption']}")
                print(f"  • Pesan Sensitif (DB): {r['secret_intel_note']}") # Teks acak terenkripsi!
            print("\n" + "-"*70)
            print("KESIMPULAN: Pesan penting di database 100% AMAN dalam bentuk Ciphertext!")
            print("-" * 70 + "\n")
            
    elif choice == "3":
        print("\n--- BUKA DATABASE RESMI SEBAGAI AGEN ---")
        kunci = input("Masukkan Passphrase Kunci Dekripsi DB: ").strip()
        if not kunci:
            kunci = "KunciDatabaseDarkroom2026!"
            print(f"(Default: '{kunci}')")
            
        decrypted = get_decrypted_database_records(kunci)
        if not decrypted:
            print("\nDatabase masih kosong! Jalankan Opsi 1 terlebih dahulu.")
        else:
            print("\n" + "="*70)
            print("HASIL DEKRIPSI RESMI UNTUK AGEN:")
            print("="*70)
            for r in decrypted:
                print(f"\n[ID #{r['id']}] {r['photo_title']}")
                print(f"  • Keterangan Publik  : {r['public_caption']}")
                print(f"  • Pesan Sensitif Asli: {r['secret_intel_note']}")
                print(f"  • Status Dekripsi    : {r['decryption_status']}")
            print("="*70 + "\n")
