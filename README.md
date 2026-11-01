# 📸 DARKROOM 2.0 — Dual-Identity Photography & Covert Cryptography Suite

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-YuNet%20%7C%20SFace-green.svg)](https://opencv.org/)
[![Cryptography](https://img.shields.io/badge/Cryptography-AES--256--GCM%20%7C%20ChaCha20--Poly1305-orange.svg)](https://cryptography.io/)
[![Blockchain](https://img.shields.io/badge/Blockchain-Proof--of--Work-yellow.svg)](#)

> **DARKROOM 2.0** adalah aplikasi fotografi profesional beridentitas ganda (*dual-identity*). Identitas publiknya dirancang menyerupai **Adobe Lightroom** untuk *tuning* pencahayaan, warna, dan manajemen katalog foto. Di balik kamuflase tersebut, tersimpan instrumen kriptografi dan steganografi LSB tingkat militer untuk komunikasi klandestin jurnalis/agen investigasi.

---

## ⚡ Panduan Instalasi Cepat (Untuk Pengujian)

Aplikasi ini dapat langsung dijalankan di laptop/PC berbasis **Windows**:

### 1. Prasyarat Sistem
- **Python 3.10** atau versi lebih baru ([Unduh Python](https://www.python.org/downloads/))
  *(Pastikan mencentang opsi **"Add Python to PATH"** saat instalasi)*.
- Webcam bawaan laptop (untuk pengujian biometrik wajah).
- Google Chrome atau Microsoft Edge (untuk jendela antarmuka mandiri).

### 2. Kloning & Pasang Dependensi
Buka Terminal / Command Prompt / PowerShell, lalu jalankan:

```bash
# 1. Kloning repositori ini
git clone https://github.com/MassJakaa/Darkroom-2.0.git
cd Darkroom-2.0

# 2. Pasang dependensi yang dibutuhkan
pip install -r requirements.txt
```

### 3. Menjalankan Aplikasi
Cukup jalankan skrip peluncur:

```bash
python run.py
```
*Atau di Windows Explorer, cukup klik ganda berkas **`run_darkroom.bat`**.*

Aplikasi akan menyalakan server lokal FastAPI (`http://127.0.0.1:8000`) dan otomatis membuka antarmuka mandiri tanpa bilah browser.

---

## 🔑 Kredensial & Nilai Default untuk Pengujian

Semua fitur telah disiapkan dengan profil default agar pengujian langsung lancar:

| Parameter | Nilai Default | Keterangan |
| :--- | :--- | :--- |
| **Password Admin / Sesi** | `admin` | Kata sandi otorisasi sesi privat |
| **Kunci Vigenère (Klasik)** | `JURNALIS` | Lapisan enkripsi substitusi klasik |
| **Passphrase AES-256-GCM** | `OperasiSenyap2026!` | Kunci derivasi HKDF untuk pesan teks |
| **Passphrase File ChaCha20** | `OperasiSenyap2026!` | Kunci proteksi berkas biner & citra rahasia |
| **Passphrase File Lock (.enc)** | `BrankasDarkroom2026!` | Enkripsi disk fisik foto lokal |

---

## 🧭 Navigasi 6 Ruang Kerja (Workspace)

Bilah menu navigasi di sisi kiri tersusun secara berurutan:

```
[ Lr / Dk ]  <- Tombol Pengalih Mode (Lightroom <-> Darkroom)
├── 1. Library           (Katalog Foto, Filter Pencarian & Manajemen Aset)
├── 2. Develop           (Studio Editor: Tone Tuning, Exposure, Warna, Presets)
├── 3. Export            (Ekspor Foto Fotografi: JPEG/PNG/TIFF, Skala & Kualitas)
├── 4. Transfer (Stego)  [Mode Darkroom] (Enkripsi & Sisipkan Payload ke Foto)
├── 5. Dekripsi          [Mode Darkroom] (Ekstraksi & Pembongkaran Muatan Stego)
└── 6. Preferences       [Mode Darkroom] (Dongle, Biometrik Wajah, & Blockchain)
```

---

## 🧪 Skenario Pengujian Fitur Utama

### 1. Beralih Antara Mode Kamuflase & Mode Covert
- Saat pertama dibuka, aplikasi berada dalam **Mode: Lightroom** (Kamuflase Publik). Menu rahasia (*Transfer, Dekripsi, Preferences*) disembunyikan.
- Klik tombol **`Mode: Lightroom`** di kiri atas untuk beralih seketika ke **`Mode: Darkroom`**.
- Badge berubah menjadi **Dk (Covert Studio 2.0)** dan menu rahasia seketika dapat diakses.

### 2. Autentikasi Biometrik Wajah AI (OpenCV YuNet + SFace)
1. Buka menu **Preferences**.
2. Pada kartu **Autentikasi Biometrik Wajah AI**, klik tombol **"Buka Kamera"**.
3. Posisikan wajah Anda di depan webcam, lalu klik **"Daftarkan Wajah"**.
   - Model neural network YuNet mendeteksi koordinat wajah dan SFace mengekstrak vektor fitur 128-dimensi secara lokal (*offline* tanpa kirim data ke cloud).
4. Klik **"Verifikasi Wajah"** untuk menguji kecocokan biometrik menggunakan rumus *Cosine Similarity* (ambang batas: `36.3%`).
5. Jika orang lain mencoba memindai wajahnya, sistem akan menolak dengan status *Wajah Ditolak / Wajah Asing*.

### 3. Pengujian Hardware Dongle (SD Card / USB Flashdisk)
Sistem memiliki pengaman fisik (*Dead Man's Switch*):
- **Opsi Flashdisk Fisik**:
  Colokkan Flashdisk/SD Card ke komputer, lalu jalankan perintah:
  ```bash
  python Darkroom/backend/hardware/dongle.py --make-key E
  ```
  *(Ganti `E` dengan huruf drive flashdisk Anda)*. File `darkroom.key` akan dibuat.
- **Opsi Virtual Dongle (Tanpa Flashdisk)**:
  Di menu **Preferences**, sakelar **"Virtual Dongle"** sudah aktif secara default agar teman Anda dapat langsung menguji tanpa repot mencari flashdisk fisik.
- **Uji Dead Man's Switch**:
  Matikan sakelar Virtual Dongle (atau cabut flashdisk fisik), sistem seketika mematikan sesi privat dan mengunci seluruh instrumen kriptografi.

### 4. Ekspor Foto Modifikasi Steganografi (Transfer)
1. Masuk ke menu **Transfer (Stego)** di bilah kiri.
2. Pilih foto pembawa (*Cover Image*) dari dropdown atau unggah foto baru. Sistem menampilkan meteran kapasitas piksel LSB (1 bpp per kanal RGB).
3. Pilih tipe muatan:
   - **Pesan Teks**: Menggunakan Super-Encryption (Vigenère + AES-256-GCM AEAD).
   - **Berkas Biner**: Mengenkripsi dokumen apa pun (PDF, ZIP, DOCX) via ChaCha20-Poly1305.
   - **Citra Rahasia**: Menyembunyikan foto rahasia di dalam foto decoy tanpa kompresi *lossy*.
4. Klik tombol hijau **"Enkripsi & Sisipkan ke Cover (LSB V2)"**.
5. Foto termodifikasi berformat PNG murni dengan nama `MODIFIED_STEGO_{nama_asli}.png` berhasil dibuat dan otomatis terdaftar ke katalog.
6. Anda dapat langsung mengklik tombol **"Buka di Dekripsi"** pada kartu hasil.

### 5. Pembongkaran & Dekripsi Muatan (Dekripsi)
1. Buka menu **Dekripsi** di bilah kiri (hanya ada di Mode Darkroom).
2. Pada dropdown katalog, pilih foto stego yang baru saja dibuat (berada di bagian atas bertanda bintang ⭐ `MODIFIED_STEGO_...`).
   *Atau Anda juga bisa mengunggah berkas citra PNG stego dari komputer luar.*
3. Masukkan kunci yang sesuai, lalu klik **"Pindai & Bongkar Muatan Rahasia"**.
4. Sistem memverifikasi magic bytes `DKRM\x02`, memeriksa tag otentikasi integritas, mendekripsi muatan, dan menampilkan:
   - Teks pesan rahasia (bisa langsung disalin via tombol Salin).
   - Berkas biner asli yang pulih 100% byte-for-byte (bisa langsung diunduh).
   - Citra rahasia yang terpulihkan secara presisi.

### 6. Audit & Simulasi Serangan Hacker pada Blockchain
1. Di menu **Develop**, Anda bisa mencatat hash foto ke dalam buku besar dengan tombol **"Catat Hash ke Blockchain"**.
2. Buka menu **Preferences** -> Bagian **Buku Besar Rantai Blok Integritas Foto**.
3. Seluruh blok transaksi penambangan (*Proof-of-Work*) ditampilkan lengkap dengan cryptographic hash SHA-256.
4. Klik tombol merah **"Simulasi Serangan Hacker"**:
   - Sistem akan memodifikasi metadata blok secara paksa untuk mensimulasikan pemalsuan data.
   - Algoritma verifikasi blockchain langsung mendeteksi ketidaksesuaian hash dan membunyikan alarm peringatan manipulasi data seketika.
5. Klik **"Audit Rantai"** untuk memulihkan dan memverifikasi integritas kembali.

---

## 🔬 Menjalankan Pengujian Otomatis (Unit Tests)

Seluruh modul kriptografi, state machine, steganografi LSB, dan endpoint API telah dilengkapi test suite lengkap:

```bash
python -m unittest discover -s Darkroom/tests -v
```

Hasil uji: **30/30 Unit Tests PASS (100% Berhasil)** dalam < 1 detik.

---

## 🛠️ Struktur Proyek

```
.
├── run.py                        # Peluncur utama aplikasi mandiri
├── run_darkroom.bat              # Script double-click Windows
├── requirements.txt              # Daftar dependensi Python
├── README.md                     # Panduan komprehensif ini
└── Darkroom/
    ├── app.py                    # Server backend FastAPI
    ├── backend/
    │   ├── blockchain/ledger.py  # Proof-of-Work Blockchain
    │   ├── core/session.py       # Session State Machine & Security Foundation
    │   ├── crypto/               # AES-256-GCM, ChaCha20-Poly1305, Vigenère, HKDF
    │   ├── database/db.py        # SQLite dengan Field-Level Encryption (FLE)
    │   ├── hardware/
    │   │   ├── biometric.py      # Face Recognition (OpenCV YuNet + SFace)
    │   │   ├── dongle.py         # Hardware Removable Drive Detector
    │   │   └── models/           # Bobot neural network ONNX (offline)
    │   └── stego/lsb.py          # LSB Framing V2 Engine bertenaga NumPy
    ├── frontend/                 # UI Lightroom Suite (HTML, CSS, JS murni)
    └── tests/                    # 30 Unit Tests komprehensif
```

---

## 📄 Lisensi & Hak Cipta
Dikembangkan untuk keperluan akademik dan penelitian keamanan informasi / kriptografi terapan.
*Darkroom Engineering Team — 2026.*
