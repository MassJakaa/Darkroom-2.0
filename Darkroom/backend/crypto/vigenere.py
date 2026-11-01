"""
=============================================================================
DARKROOM - KRIPTOGRAFI KLASIK: VIGENÈRE CIPHER
=============================================================================
Mengacu pada: Materi 4 - Vigenère Chipper
Penemu     : Blaise de Vigenère (Abad ke-16)
Tipe       : Polyalphabetic Substitution Cipher

Rumus Matematis (Sesuai Slide Materi 4):
Enkripsi : C_i = (P_i + K_i) mod 26
Dekripsi : P_i = (C_i - K_i + 26) mod 26

Keterangan:
- P_i = Huruf Plaintext ke-i (A=0, B=1, ..., Z=25)
- C_i = Huruf Ciphertext ke-i
- K_i = Huruf Kunci ke-i (diulang secara periodik sepanjang teks)
- Karakter non-huruf (spasi, angka, tanda baca) dipertahankan agar pesan
  tetap memiliki struktur alami sebelum masuk ke enkripsi modern.
=============================================================================
"""

def clean_key(key: str) -> str:
    """Membersihkan kunci agar hanya berisi huruf alfabet kapital."""
    cleaned = ''.join(c.upper() for c in key if c.isalpha())
    if not cleaned:
        raise ValueError("Kunci Vigenère harus mengandung setidaknya satu huruf alfabet!")
    return cleaned


def vigenere_encrypt(plaintext: str, key: str) -> str:
    """
    Mengenkripsi teks menggunakan Vigenère Cipher (Materi 4).
    """
    key = clean_key(key)
    ciphertext = []
    key_index = 0
    key_len = len(key)
    
    for char in plaintext:
        if char.isalpha():
            # Tentukan offset (65 untuk huruf besar 'A', 97 untuk huruf kecil 'a')
            is_upper = char.isupper()
            base = ord('A') if is_upper else ord('a')
            
            p_val = ord(char) - base
            k_val = ord(key[key_index % key_len]) - ord('A')
            
            # Rumus: C = (P + K) mod 26
            c_val = (p_val + k_val) % 26
            ciphertext.append(chr(c_val + base))
            
            key_index += 1
        else:
            # Karakter non-huruf (spasi, angka, simbol) tidak diubah
            ciphertext.append(char)
            
    return "".join(ciphertext)


def vigenere_decrypt(ciphertext: str, key: str) -> str:
    """
    Mendekripsi teks ciphertext kembali ke plaintext menggunakan Vigenère Cipher.
    """
    key = clean_key(key)
    plaintext = []
    key_index = 0
    key_len = len(key)
    
    for char in ciphertext:
        if char.isalpha():
            is_upper = char.isupper()
            base = ord('A') if is_upper else ord('a')
            
            c_val = ord(char) - base
            k_val = ord(key[key_index % key_len]) - ord('A')
            
            # Rumus: P = (C - K + 26) mod 26
            p_val = (c_val - k_val + 26) % 26
            plaintext.append(chr(p_val + base))
            
            key_index += 1
        else:
            plaintext.append(char)
            
    return "".join(plaintext)


if __name__ == "__main__":
    test_text = "Laporan Intelijen: Target ada di koordinat -6.2088, 106.8456!"
    test_key = "RAHASIA"
    
    enc = vigenere_encrypt(test_text, test_key)
    dec = vigenere_decrypt(enc, test_key)
    
    print("--- UJI COBA VIGENERE CIPHER ---")
    print("Teks Asli   :", test_text)
    print("Kunci       :", test_key)
    print("Terenkripsi :", enc)
    print("Terdekripsi :", dec)
    assert test_text == dec, "Gagal dekripsi Vigenere!"
    print("Hasil       : 100% Cocok & Valid!")
