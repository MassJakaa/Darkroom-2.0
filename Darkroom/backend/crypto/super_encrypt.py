"""
=============================================================================
DARKROOM - SUPER ENKRIPSI PESAN TEKS (KRITERIA 3)
=============================================================================
Menggabungkan Kriptografi Klasik dan Kriptografi Modern secara berantai.

Alur Enkripsi (2 Lapis):
Plaintext (Catatan Foto/Intel)
   │
   ▼ [Lapis 1: Kriptografi Klasik - Vigenère Cipher]
Intermediate Ciphertext (Substitusi Polialfabetik)
   │
   ▼ [Lapis 2: Kriptografi Modern - AES-256 CBC Mode]
Final Super Ciphertext (Base64)

Alur Dekripsi (Dibalik):
Final Super Ciphertext (Base64)
   │
   ▼ [Lapis 1: Dekripsi AES-256 CBC]
Intermediate Ciphertext
   │
   ▼ [Lapis 2: Dekripsi Vigenère Cipher]
Plaintext Asli (100% Utuh)

Keunggulan Ilmiah (Untuk Dijelaskan ke Dosen):
1. Memenuhi prinsip Konfusi (Confusion) lewat substitusi Vigenère dan S-Box AES.
2. Memenuhi prinsip Difusi (Diffusion) lewat ShiftRows & MixColumns AES serta
   mode rantai CBC (Cipher Block Chaining).
=============================================================================
"""

import sys
import os

# Tambahkan path agar modul bisa di-import langsung
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.crypto.vigenere import vigenere_encrypt, vigenere_decrypt
from backend.crypto.aes_cipher import aes_encrypt, aes_decrypt


def super_encrypt(plaintext: str, vigenere_key: str, aes_key: str) -> dict:
    """
    Menjalankan proses Super Enkripsi: Vigenère (Klasik) -> AES-256-GCM (Modern AEAD).
    
    Return:
        dict berisi hasil per tahap (berguna saat demo presentasi ke dosen):
        - plaintext
        - vigenere_key
        - intermediate_vigenere (hasil lapis 1)
        - aes_key
        - final_ciphertext (hasil lapis 2 ber-tag GCM)
    """
    # Lapis 1: Enkripsi Klasik (Vigenère)
    stage1_result = vigenere_encrypt(plaintext, vigenere_key)
    
    # Lapis 2: Enkripsi Modern (AES-256-GCM Authenticated Encryption)
    stage2_result = aes_encrypt(stage1_result, aes_key)
    
    return {
        "plaintext": plaintext,
        "vigenere_key": vigenere_key,
        "intermediate_vigenere": stage1_result,
        "aes_key": aes_key,
        "final_ciphertext": stage2_result
    }


def super_decrypt(ciphertext: str, vigenere_key: str, aes_key: str) -> dict:
    """
    Menjalankan proses Dekripsi Super Enkripsi secara terbalik: AES-256-GCM -> Vigenère.
    
    Return:
        dict berisi hasil per tahap:
        - ciphertext
        - intermediate_aes (hasil kupas lapis 1 terautentikasi)
        - final_plaintext (hasil kupas lapis 2 / teks asli)
    """
    # Kupas Lapis 1: Dekripsi Modern (AES-256-GCM dengan validasi tag)
    stage1_result = aes_decrypt(ciphertext, aes_key)
    
    # Kupas Lapis 2: Dekripsi Klasik (Vigenère)
    stage2_result = vigenere_decrypt(stage1_result, vigenere_key)
    
    return {
        "ciphertext": ciphertext,
        "intermediate_aes": stage1_result,
        "final_plaintext": stage2_result
    }


# =============================================================================
# DEMO INTERAKTIF DI TERMINAL
# =============================================================================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("      DARKROOM - PENGUJIAN SUPER ENKRIPSI (VIGENÈRE + AES-256)")
    print("="*70)
    print("Kriteria 3: Penggabungan Kriptografi Klasik dan Modern.")
    print("-" * 70)
    
    print("\nPilih Aksi:")
    print("1. Enkripsi Catatan Foto Baru (Super Enkripsi)")
    print("2. Dekripsi Catatan Rahasia (Kembalikan ke Teks Asli)")
    choice = input("Pilihan (1/2): ").strip()
    
    if choice == "2":
        print("\n--- MODE DEKRIPSI ---")
        ct = input("Masukkan Super Ciphertext (Base64): ").strip()
        k_vig = input("Masukkan Kunci Vigenère (Klasik)  : ").strip()
        k_aes = input("Masukkan Passphrase AES (Modern) : ").strip()
        
        try:
            res = super_decrypt(ct, k_vig, k_aes)
            print("\n" + "="*70)
            print("HASIL DEKRIPSI BERTAHAP:")
            print(f"1. Setelah Dekripsi AES-256 : {res['intermediate_aes']}")
            print(f"2. Setelah Dekripsi Vigenère: {res['final_plaintext']}")
            print("="*70 + "\n")
        except Exception as e:
            print(f"\n[GAGAL DEKRIPSI] Kunci salah atau data rusak: {str(e)}\n")
            
    else:
        print("\n--- MODE SUPER ENKRIPSI ---")
        pesan = input("Masukkan Catatan Intel/Foto : ").strip()
        if not pesan:
            pesan = "Target berada di lobi hotel. Dokumen transaksi diserahkan jam 21.00."
            print(f"(Menggunakan pesan default: '{pesan}')")
            
        k_vig = input("Masukkan Kunci Vigenère (contoh: JURNALIS) : ").strip()
        if not k_vig:
            k_vig = "JURNALIS"
            print(f"(Menggunakan kunci Vigenère default: '{k_vig}')")
            
        k_aes = input("Masukkan Passphrase AES (contoh: OperasiSenyap2026!): ").strip()
        if not k_aes:
            k_aes = "OperasiSenyap2026!"
            print(f"(Menggunakan passphrase AES default: '{k_aes}')")
            
        res = super_encrypt(pesan, k_vig, k_aes)
        
        print("\n" + "="*70)
        print("HASIL SUPER ENKRIPSI BERTAHAP:")
        print(f"• Teks Asli                : {res['plaintext']}")
        print(f"• Lapis 1 (Vigenère Klasik): {res['intermediate_vigenere']}")
        print(f"• Lapis 2 (AES-256 Modern) : {res['final_ciphertext']}")
        print("="*70)
        
        # Otomatis uji dekripsi
        test_dec = super_decrypt(res['final_ciphertext'], k_vig, k_aes)
        print("\n[VERIFIKASI INTEGRITAS OTOMATIS]")
        print(f"Uji Dekripsi Kembali : '{test_dec['final_plaintext']}'")
        assert pesan == test_dec['final_plaintext']
        print("Status               : 100% PERSIS DAN IDENTIK DENGAN ASLI!\n")
