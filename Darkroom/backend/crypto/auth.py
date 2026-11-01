"""
=============================================================================
DARKROOM - CRYPTOGRAPHIC AUTHENTICATION CONTROLLER (KRITERIA 2)
=============================================================================
Modul ini bertugas menangani keamanan autentikasi password agen menggunakan
algoritma kriptografi satu arah (One-Way Cryptographic Hash Function).

Algoritma yang Digunakan:
1. SHA-256 (Secure Hash Algorithm 256-bit):
   Mengacu pada Materi 8 (Fungsi Hash). Menghasilkan digest 64 karakter hex
   yang mustahil dibalik (one-way property) dan kebal tabrakan (collision resistant).
   
2. Cryptographic Salt:
   String acak 16-byte unik untuk setiap user. 
   Fungsi: Mencegah serangan kamus (Dictionary Attack) dan Rainbow Table Attack.
   
3. Key Stretching (PBKDF2-HMAC-SHA256):
   Melakukan iterasi hash sebanyak 100.000 putaran agar penyerang tidak bisa
   melakukan brute-force password secara kilat menggunakan GPU.
   
4. Constant-Time Comparison:
   Membandingkan hash menggunakan secrets.compare_digest untuk mencegah
   serangan kebocoran waktu pemrosesan (Timing Attack).
=============================================================================
"""

import os
import json
import secrets
import hashlib

# Lokasi penyimpanan kredensial akun agen
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "storage"))
AUTH_DATA_PATH = os.path.join(STORAGE_DIR, "agent_auth.json")

# Parameter keamanan
SALT_LENGTH = 16          # 16 byte (128-bit) salt acak
HASH_ITERATIONS = 100_000 # 100.000 iterasi PBKDF2


def generate_salt():
    """
    Menghasilkan nilai salt acak yang aman secara kriptografi (CSPRNG).
    """
    return secrets.token_hex(SALT_LENGTH)


def hash_password(password: str, salt: str = None) -> tuple:
    """
    Meng-hash password menggunakan PBKDF2 dengan algoritma SHA-256.
    
    Rumus Matematis:
    Digest = PBKDF2_HMAC_SHA256(Password, Salt, Iterations=100.000)
    
    Return:
        tuple (password_hash: str, salt: str)
    """
    if salt is None:
        salt = generate_salt()
        
    # Menggunakan PBKDF2 bawaan hashlib (Standar Industri RFC 2898 / NIST)
    derived_key = hashlib.pbkdf2_hmac(
        hash_name='sha256',
        password=password.encode('utf-8'),
        salt=salt.encode('utf-8'),
        iterations=HASH_ITERATIONS
    )
    
    password_hash = derived_key.hex()
    return password_hash, salt


def register_user(username: str, password: str) -> tuple:
    """
    Mendaftarkan password agen dan menyimpannya dalam format hash ter-salt.
    """
    os.makedirs(STORAGE_DIR, exist_ok=True)
    
    password_hash, salt = hash_password(password)
    
    user_data = {
        "username": username,
        "password_hash": password_hash,
        "salt": salt,
        "algorithm": "PBKDF2-HMAC-SHA256",
        "iterations": HASH_ITERATIONS
    }
    
    with open(AUTH_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=4)
        
    return True, f"Akun agen '{username}' berhasil didaftarkan secara kriptografis!"


def verify_login(password_input: str) -> tuple:
    """
    Memverifikasi password yang dimasukkan saat login.
    
    Return:
        tuple (is_valid: bool, message: str)
    """
    if not is_user_registered():
        return False, "Belum ada akun agen yang terdaftar di sistem!"
        
    try:
        with open(AUTH_DATA_PATH, "r", encoding="utf-8") as f:
            user_data = json.load(f)
            
        stored_hash = user_data["password_hash"]
        stored_salt = user_data["salt"]
        
        # Hitung hash dari password inputan menggunakan salt yang tersimpan
        computed_hash, _ = hash_password(password_input, salt=stored_salt)
        
        # Bandingkan dengan constant-time comparison (Anti-Timing Attack)
        if secrets.compare_digest(stored_hash, computed_hash):
            return True, f"Login Kriptografis Berhasil! Selamat datang, Agen {user_data['username']}."
        else:
            return False, "Password SALAH! Akses ditolak."
            
    except Exception as e:
        return False, f"Terjadi kesalahan saat verifikasi: {str(e)}"


def is_user_registered() -> bool:
    """
    Mengecek apakah kredensial password agen sudah tersimpan.
    """
    return os.path.exists(AUTH_DATA_PATH)


def get_current_user_info():
    """
    Mengambil data publik agen (tanpa membocorkan password).
    """
    if not is_user_registered():
        return None
    with open(AUTH_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return {
            "username": data["username"],
            "algorithm": data["algorithm"],
            "salt_preview": data["salt"][:8] + "...",
            "hash_preview": data["password_hash"][:16] + "..."
        }


# =============================================================================
# DEMO INTERAKTIF DI TERMINAL
# =============================================================================
if __name__ == "__main__":
    print("\n" + "="*65)
    print("      DARKROOM - PENGUJIAN LOGIN KRIPTOGRAFIS (SHA-256)")
    print("="*65)
    
    if not is_user_registered():
        print("\nStatus: Belum ada akun agen terdaftar.")
        username = input("Masukkan Nama/Kode Agen (contoh: arya): ").strip()
        pwd = input("Masukkan Password Rahasia Agen     : ").strip()
        
        success, msg = register_user(username, pwd)
        print("\n" + msg)
        
        info = get_current_user_info()
        print("\nDetail Keamanan Kriptografi:")
        print(f"  • Algoritma : {info['algorithm']}")
        print(f"  • Salt      : {info['salt_preview']}")
        print(f"  • Hash SHA  : {info['hash_preview']}")
        print("\nPassword mentahmu TIDAK PERNAH disimpan.")
    else:
        info = get_current_user_info()
        print(f"\nStatus: Akun Agen '{info['username']}' terdaftar.")
        print("Pilih aksi:")
        print("1. Uji Login Password (Ketik password untuk verifikasi)")
        print("2. Ubah / Daftarkan Ulang Password")
        choice = input("Pilihan (1/2): ").strip()
        
        if choice == "2":
            username = input("Masukkan Nama/Kode Agen baru: ").strip()
            pwd = input("Masukkan Password baru       : ").strip()
            success, msg = register_user(username, pwd)
            print("\n" + msg)
        else:
            pwd_input = input("\nMasukkan Password Agen: ").strip()
            is_valid, msg = verify_login(pwd_input)
            print("\n" + "="*65)
            print("HASIL VERIFIKASI LOGIN:")
            print(msg)
            print("="*65 + "\n")
