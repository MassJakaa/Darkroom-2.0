"""
=============================================================================
DARKROOM - HARDWARE DONGLE CONTROLLER
=============================================================================
Modul ini bertugas mendeteksi keberadaan media penyimpanan eksternal 
(seperti Flashdisk / SD Card melalui Card Reader) di sistem operasi Windows.

Cara Kerja:
1. Menggunakan Windows API (kernel32.dll) untuk mencari drive bertipe REMOVABLE.
2. Memeriksa apakah ada file kunci kriptografis bernama 'darkroom_agent.key'.
3. Memvalidasi isi token di dalam file tersebut menggunakan fungsi Hash SHA-256.
4. Mendukung mekanisme 'Panic Switch': jika drive dicabut, akses langsung dikunci.
=============================================================================
"""

import os
import time
import ctypes
import hashlib
import string

# Nama file kunci yang harus ada di dalam SD Card / Flashdisk
DONGLE_KEY_FILENAME = "darkroom.key"

# Token rahasia yang sah (di dunia nyata, ini adalah tanda tangan digital agen)
EXPECTED_TOKEN_PAYLOAD = "DARKROOM-SECRET-AGENT-KEY-V1"

# Hash SHA-256 dari token rahasia yang sah
EXPECTED_TOKEN_HASH = hashlib.sha256(EXPECTED_TOKEN_PAYLOAD.encode('utf-8')).hexdigest()

# Konstanta tipe drive dari Windows API
# DRIVE_REMOVABLE = 2 (USB Flashdisk, SD Card Reader)
# DRIVE_FIXED     = 3 (Harddisk / SSD internal laptop)
DRIVE_REMOVABLE = 2

# Fallback path untuk pengujian virtual/lab tanpa hardware card reader fisik
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "storage"))
VIRTUAL_DONGLE_DIR = os.path.join(STORAGE_DIR, "virtual_dongle")
VIRTUAL_DONGLE_FILE = os.path.join(VIRTUAL_DONGLE_DIR, DONGLE_KEY_FILENAME)

# Flag kontrol virtual dongle (Default: False agar wajib menggunakan hardware dongle fisik)
_virtual_dongle_enabled = False


def get_removable_drives():
    """
    Mendeteksi semua drive fisik eksternal (SD Card / Flashdisk) yang sedang terhubung ke laptop.
    Memeriksa tipe DRIVE_REMOVABLE dari Windows Kernel32 API serta drive non-sistem yang memiliki file darkroom.key.
    Mengembalikan daftar drive letter unik, contoh: ['E:\\', 'F:\\']
    """
    removable_drives = []
    system_drive = os.environ.get("SystemDrive", "C:").upper()
    if not system_drive.endswith("\\"):
        system_drive += "\\"
        
    try:
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if (bitmask >> (ord(letter) - ord('A'))) & 1:
                drive_path = f"{letter}:\\"
                # Abaikan drive OS utama C:\
                if drive_path.upper() == system_drive:
                    continue
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
                # Removable drive fisik (Flashdisk / SD Card)
                if drive_type == DRIVE_REMOVABLE:
                    removable_drives.append(drive_path)
                # Atau drive non-sistem lain yang memiliki berkas kunci darkroom.key
                elif os.path.exists(os.path.join(drive_path, DONGLE_KEY_FILENAME)):
                    removable_drives.append(drive_path)
    except Exception:
        pass
                
    return list(dict.fromkeys(removable_drives))


def verify_dongle():
    """
    Memeriksa apakah ada Dongle Fisik (SD Card / Flashdisk) sah yang tercolok.
    Secara default menolak fallback virtual kecuali secara eksplisit diaktifkan.
    
    Return:
        tuple (is_valid: bool, message: str, drive_path: str)
    """
    drives = get_removable_drives()
    
    # 1. Prioritaskan drive removable fisik (Hardware SD Card / Flashdisk USB)
    if drives:
        for drive in drives:
            key_file_path = os.path.join(drive, DONGLE_KEY_FILENAME)
            if os.path.exists(key_file_path):
                try:
                    with open(key_file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
                    if content_hash == EXPECTED_TOKEN_HASH:
                        return True, f"Hardware Dongle Fisik Terdeteksi di {drive}", drive
                    else:
                        return False, f"File kunci ditemukan di {drive}, tetapi token TIDAK VALID / PALSU!", drive
                except Exception as e:
                    return False, f"Gagal membaca file kunci di {drive}: {str(e)}", drive

    # 2. Virtual Dongle HANYA diizinkan jika secara eksplisit diaktifkan (misal pada automated testing)
    global _virtual_dongle_enabled
    if _virtual_dongle_enabled and os.path.exists(VIRTUAL_DONGLE_FILE):
        try:
            with open(VIRTUAL_DONGLE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            if content_hash == EXPECTED_TOKEN_HASH:
                return True, "Virtual Dongle Terdeteksi (Kunci Kriptografis Sah)", VIRTUAL_DONGLE_DIR
        except Exception:
            pass

    if drives:
        return False, f"Media eksternal terdeteksi ({', '.join(drives)}), tetapi file '{DONGLE_KEY_FILENAME}' tidak ditemukan.", None
    return False, "Tidak ada hardware dongle (SD Card / Flashdisk) yang terdeteksi.", None


def set_virtual_dongle(active: bool = True):
    """
    Mengaktifkan atau mencabut virtual dongle (berguna untuk pengujian otomatis unit test).
    """
    global _virtual_dongle_enabled
    _virtual_dongle_enabled = active
    os.makedirs(VIRTUAL_DONGLE_DIR, exist_ok=True)
    if active:
        with open(VIRTUAL_DONGLE_FILE, "w", encoding="utf-8") as f:
            f.write(EXPECTED_TOKEN_PAYLOAD)
        return True
    else:
        if os.path.exists(VIRTUAL_DONGLE_FILE):
            os.remove(VIRTUAL_DONGLE_FILE)
        return False


def create_dongle_key(target_drive_letter):
    """
    Fungsi bantuan untuk mengubah Flashdisk / SD Card apa pun menjadi Dongle resmi Darkroom.
    Contoh penggunaan: create_dongle_key("E")
    """
    clean_drive = target_drive_letter.strip().upper().replace(":", "").replace("\\", "")
    target_path = f"{clean_drive}:\\"
    
    if not os.path.exists(target_path):
        return False, f"Drive {target_path} tidak ditemukan di komputer!"
        
    key_file_path = os.path.join(target_path, DONGLE_KEY_FILENAME)
    
    try:
        with open(key_file_path, "w", encoding="utf-8") as f:
            f.write(EXPECTED_TOKEN_PAYLOAD)
        return True, f"Kunci Dongle resmi berhasil dibuat di: {key_file_path}"
    except Exception as e:
        return False, f"Gagal menulis file kunci ke {target_path}: {str(e)}"


# =============================================================================
# DEMO INTERAKTIF DI TERMINAL
# =============================================================================
if __name__ == "__main__":
    import sys
    
    print("\n" + "="*60)
    print("      DARKROOM - PENGUJIAN HARDWARE DONGLE")
    print("="*60)
    
    # Opsi jika user ingin membuat kunci ke flashdisk
    if len(sys.argv) > 1 and sys.argv[1] == "--make-key":
        if len(sys.argv) < 3:
            print("Penggunaan: python dongle.py --make-key <HURUF_DRIVE>")
            print("Contoh:     python dongle.py --make-key E")
            sys.exit(1)
        target_drive = sys.argv[2]
        success, msg = create_dongle_key(target_drive)
        print("\n" + msg + "\n")
        sys.exit(0)

    print("\nInstruksi:")
    print("1. Colokkan Flashdisk / Card Reader (SD Card) ke laptop.")
    print("2. Jika belum ada file kuncinya, jalankan:")
    print("   python backend/hardware/dongle.py --make-key <HURUF_DRIVE>")
    print("3. Skrip ini akan memantau status colok/cabut secara real-time.")
    print("\nTekan Ctrl+C untuk berhenti.\n")
    print("-" * 60)
    
    last_status = None
    
    try:
        while True:
            is_valid, message, drive = verify_dongle()
            current_status = is_valid
            
            # Hanya cetak jika status berubah (biar terminal tidak banjir tulisan)
            if current_status != last_status:
                if is_valid:
                    print(f"\n[OK - DONGLE TERPASANG] {message}")
                    print(">>> Mode: [DARKROOM - UNLOCKED]")
                    print(">>> Menunggu instruksi kriptografi...\n")
                else:
                    print(f"\n[PERINGATAN / KUNCI DICABUT] {message}")
                    print(">>> PANIC SWITCH AKTIF! Sistem kembali ke: [LIGHTROOM NORMAL MODE]\n")
                
                last_status = current_status
                
            time.sleep(1) # Cek setiap 1 detik
            
    except KeyboardInterrupt:
        print("\nPengujian dongle dihentikan oleh pengguna.")
