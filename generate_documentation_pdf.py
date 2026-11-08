# -*- coding: utf-8 -*-
"""
Script Generator Dokumen PDF Resmi Tugas Akhir Kriptografi: DARKROOM 2.0
Mengonversi format HTML kaya grafis & tipografi ilmiah menjadi file PDF beresolusi tinggi menggunakan Headless Chrome.
"""

import os
import subprocess
import sys

HTML_OUTPUT_PATH = os.path.abspath(r"Dokumentasi_Lengkap_Darkroom_Kriptografi.html")
PDF_OUTPUT_PATH = os.path.abspath(r"Dokumentasi_Lengkap_Darkroom_Kriptografi.pdf")

html_content = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>Dokumentasi Teknis Lengkap - Darkroom 2.0</title>
<style>
    @page {
        size: A4;
        margin: 20mm 15mm 20mm 15mm;
        @bottom-right {
            content: "Halaman " counter(page);
            font-size: 8pt;
            font-family: 'Segoe UI', Tahoma, sans-serif;
            color: #64748b;
        }
        @top-right {
            content: "Darkroom 2.0 - Tugas Akhir Kriptografi";
            font-size: 8pt;
            font-family: 'Segoe UI', Tahoma, sans-serif;
            color: #94a3b8;
        }
    }

    body {
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.6;
        color: #1e293b;
        background-color: #ffffff;
        margin: 0;
        padding: 0;
    }

    /* PAGE BREAK HELPERS */
    .page-break {
        page-break-before: always;
    }
    .avoid-break {
        page-break-inside: avoid;
    }

    /* COVER PAGE */
    .cover-page {
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 40px 20px;
        box-sizing: border-box;
        text-align: center;
        page-break-after: always;
        background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
        border: 2px solid #0f172a;
        border-radius: 8px;
    }
    .cover-top {
        margin-top: 40px;
    }
    .institution {
        font-size: 13pt;
        font-weight: 700;
        color: #334155;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .course-title {
        font-size: 11pt;
        color: #64748b;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .cover-middle {
        margin: 60px 0;
    }
    .main-badge {
        display: inline-block;
        background-color: #0284c7;
        color: #ffffff;
        font-size: 11pt;
        font-weight: 700;
        padding: 6px 18px;
        border-radius: 20px;
        margin-bottom: 20px;
        letter-spacing: 1px;
    }
    .doc-title {
        font-size: 26pt;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.25;
        margin: 0 0 16px 0;
    }
    .doc-subtitle {
        font-size: 12pt;
        color: #475569;
        max-width: 650px;
        margin: 0 auto;
        line-height: 1.5;
    }
    .cover-divider {
        width: 80px;
        height: 4px;
        background-color: #0284c7;
        margin: 30px auto;
        border-radius: 2px;
    }
    .author-box {
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 16px 24px;
        display: inline-block;
        text-align: left;
        margin: 0 auto;
    }
    .author-row {
        display: flex;
        justify-content: space-between;
        gap: 30px;
        font-size: 10pt;
        margin: 4px 0;
    }
    .author-label {
        font-weight: 600;
        color: #475569;
    }
    .author-value {
        font-weight: 700;
        color: #0f172a;
    }
    .cover-bottom {
        margin-bottom: 30px;
        font-size: 9.5pt;
        color: #64748b;
    }

    /* HEADINGS */
    h1 {
        font-size: 18pt;
        font-weight: 800;
        color: #0f172a;
        border-bottom: 2px solid #0284c7;
        padding-bottom: 6px;
        margin-top: 24px;
        margin-bottom: 16px;
        letter-spacing: -0.5px;
    }
    h2 {
        font-size: 13pt;
        font-weight: 700;
        color: #1e293b;
        margin-top: 20px;
        margin-bottom: 10px;
        border-left: 4px solid #0284c7;
        padding-left: 10px;
    }
    h3 {
        font-size: 11pt;
        font-weight: 700;
        color: #334155;
        margin-top: 14px;
        margin-bottom: 8px;
    }
    p {
        margin-top: 0;
        margin-bottom: 10px;
        text-align: justify;
    }

    /* TABLES */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 14px 0 20px 0;
        font-size: 8.5pt;
    }
    th, td {
        border: 1px solid #cbd5e1;
        padding: 8px 10px;
        text-align: left;
        vertical-align: top;
    }
    th {
        background-color: #0f172a;
        color: #ffffff;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 8pt;
        letter-spacing: 0.5px;
    }
    tr:nth-child(even) td {
        background-color: #f8fafc;
    }
    .badge {
        display: inline-block;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 7.5pt;
        font-weight: 700;
    }
    .badge-green { background-color: #dcfce7; color: #166534; border: 1px solid #86efac; }
    .badge-blue { background-color: #e0f2fe; color: #075985; border: 1px solid #7dd3fc; }
    .badge-purple { background-color: #f3e8ff; color: #6b21a8; border: 1px solid #d8b4fe; }
    .badge-amber { background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a; }

    /* CODE BLOCKS */
    pre {
        background-color: #0f172a;
        color: #f8fafc;
        padding: 12px 14px;
        border-radius: 6px;
        font-family: 'Consolas', 'Fira Code', 'Courier New', monospace;
        font-size: 8pt;
        line-height: 1.45;
        overflow-x: hidden;
        white-space: pre-wrap;
        word-wrap: break-word;
        margin: 10px 0 16px 0;
        border: 1px solid #334155;
    }
    code {
        font-family: 'Consolas', 'Fira Code', 'Courier New', monospace;
        font-size: 8.5pt;
        background-color: #f1f5f9;
        color: #0369a1;
        padding: 1px 4px;
        border-radius: 3px;
    }
    pre code {
        background-color: transparent;
        color: inherit;
        padding: 0;
    }

    /* CALLOUT BOXES */
    .callout {
        border-left: 4px solid #0284c7;
        background-color: #f0f9ff;
        padding: 12px 16px;
        margin: 14px 0;
        border-radius: 0 6px 6px 0;
    }
    .callout-title {
        font-weight: 700;
        color: #0369a1;
        font-size: 9.5pt;
        margin-bottom: 4px;
    }
    .callout-warning {
        border-left-color: #f59e0b;
        background-color: #fffbeb;
    }
    .callout-warning .callout-title {
        color: #b45309;
    }
    .callout-success {
        border-left-color: #10b981;
        background-color: #ecfdf5;
    }
    .callout-success .callout-title {
        color: #047857;
    }

    /* FORMULA DISPLAY */
    .formula-box {
        background-color: #f8fafc;
        border: 1px dashed #94a3b8;
        border-radius: 6px;
        padding: 10px 16px;
        margin: 10px 0;
        font-family: 'Consolas', monospace;
        font-size: 9pt;
        color: #0f172a;
        text-align: center;
    }

    /* TABLE OF CONTENTS */
    .toc-item {
        display: flex;
        justify-content: space-between;
        border-bottom: 1px dotted #cbd5e1;
        padding: 5px 0;
        font-size: 9.5pt;
    }
    .toc-title {
        color: #1e293b;
        font-weight: 600;
    }
    .toc-page {
        color: #64748b;
        font-weight: 700;
    }

    ul, ol {
        margin-top: 0;
        margin-bottom: 12px;
        padding-left: 20px;
    }
    li {
        margin-bottom: 4px;
        text-align: justify;
    }
</style>
</head>
<body>

<!-- ========================================================================= -->
<!-- 1. COVER PAGE                                                             -->
<!-- ========================================================================= -->
<div class="cover-page">
    <div class="cover-top">
        <div class="institution">Universitas Pembangunan Nasional "Veteran" Yogyakarta</div>
        <div class="course-title">Fakultas Teknik Industri &bull; Jurusan Informatika &bull; Tugas Akhir Kriptografi (IF-E)</div>
    </div>

    <div class="cover-middle">
        <div class="main-badge">LAPORAN DOKUMENTASI TEKNIS & ARSITEKTUR KODE</div>
        <h1 class="doc-title" style="border:none; margin:0 0 10px 0; padding:0;">DARKROOM 2.0</h1>
        <div class="doc-subtitle">
            <strong>Steganographic & Cryptographic Studio Suite for Covert Photojournalism</strong><br>
            Aplikasi Studio Foto Kamuflase (*Plausible Deniability*) Terintegrasi Biometrik, Hardware Dongle SD Card, Super-Enkripsi, ChaCha20-Poly1305 AEAD, Field-Level SQLite, LSB Steganography, dan Proof-of-Work Blockchain
        </div>
        <div class="cover-divider"></div>

        <div class="author-box">
            <div class="author-row">
                <span class="author-label">Nama Pengembang :</span>
                <span class="author-value">Rafi Dzaka Pratama Putra</span>
            </div>
            <div class="author-row">
                <span class="author-label">Nomor Induk Mahasiswa :</span>
                <span class="author-value">123240104</span>
            </div>
            <div class="author-row">
                <span class="author-label">Mata Kuliah / Kelas :</span>
                <span class="author-value">Kriptografi / IF-E (Semester 5)</span>
            </div>
            <div class="author-row">
                <span class="author-label">Mode Pengerjaan :</span>
                <span class="author-value">Solo Player (Mandiri Penuh)</span>
            </div>
            <div class="author-row">
                <span class="author-label">Dasar Penugasan :</span>
                <span class="author-value">Materi 8 Slide 46 (7 Kriteria Wajib)</span>
            </div>
        </div>
    </div>

    <div class="cover-bottom">
        <div>Tahun Akademik 2026/2027 &bull; Yogyakarta, Indonesia</div>
        <div style="font-size: 8pt; margin-top: 4px; color: #94a3b8;">Dibuat secara komprehensif untuk pengujian akademis, sidang presentasi, dan audit kode sumber.</div>
    </div>
</div>


<!-- ========================================================================= -->
<!-- 2. DAFTAR ISI & RINGKASAN EKSEKUTIF                                        -->
<!-- ========================================================================= -->
<div class="page-break"></div>
<h1>Daftar Isi & Ringkasan Eksekutif</h1>

<div style="margin: 20px 0;">
    <div class="toc-item"><span class="toc-title">BAB I: PENDAHULUAN & LATAR BELAKANG SISTEM</span><span class="toc-page">Halaman 3</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">1.1 Urgensi Keamanan Informasi & Jurnalisme Investigasi</span><span class="toc-page">Halaman 3</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">1.2 Konsep Kamuflase Plausible Deniability & Parodi Adobe Lightroom</span><span class="toc-page">Halaman 3</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">1.3 Pemetaan 7 Kriteria Wajib Tugas Akhir Kriptografi (Slide 46)</span><span class="toc-page">Halaman 4</span></div>
    
    <div class="toc-item"><span class="toc-title">BAB II: ARSITEKTUR PERANGKAT LUNAK & ALUR OPERASIONAL</span><span class="toc-page">Halaman 5</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">2.1 Arsitektur Sistem Berbasis FastAPI & Client-Side Engine</span><span class="toc-page">Halaman 5</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">2.2 Alur Kerja Pengguna (User Flow) & Dead Man's Switch</span><span class="toc-page">Halaman 6</span></div>

    <div class="toc-item"><span class="toc-title">BAB III: LANDASAN TEORI & FORMULASI MATEMATIS KRIPTOGRAFI</span><span class="toc-page">Halaman 7</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">3.1 Kriptografi Klasik: Vigenère Cipher (Substitusi Polialfabetik)</span><span class="toc-page">Halaman 7</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">3.2 Kriptografi Modern: AES-256 Rijndael (Block Cipher SPN)</span><span class="toc-page">Halaman 8</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">3.3 Kriptografi File: ChaCha20-Poly1305 AEAD</span><span class="toc-page">Halaman 9</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">3.4 Fungsi Hash SHA-256 & Key Stretching PBKDF2</span><span class="toc-page">Halaman 10</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">3.5 Steganografi Citra Spasial LSB (Least Significant Bit)</span><span class="toc-page">Halaman 11</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">3.6 Buku Besar Terdistribusi: Blockchain Proof-of-Work</span><span class="toc-page">Halaman 12</span></div>

    <div class="toc-item"><span class="toc-title">BAB IV: BEDAH KODE PROGRAM LENGKAP (SOURCE CODE WALKTHROUGH)</span><span class="toc-page">Halaman 13</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">4.1 Modul Hardware Dongle (backend/hardware/dongle.py)</span><span class="toc-page">Halaman 13</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">4.2 Modul Biometrik Wajah (backend/hardware/biometric.py)</span><span class="toc-page">Halaman 14</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">4.3 Modul Otentikasi Sandi (backend/crypto/auth.py)</span><span class="toc-page">Halaman 15</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">4.4 Modul Super Enkripsi Teks (backend/crypto/super_encrypt.py)</span><span class="toc-page">Halaman 16</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">4.5 Modul Enkripsi Berkas ChaCha20 (backend/crypto/file_cipher.py)</span><span class="toc-page">Halaman 17</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">4.6 Modul Steganografi LSB Hibrida (backend/stego/lsb.py)</span><span class="toc-page">Halaman 18</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">4.7 Modul Database SQLite Terenkripsi (backend/database/db.py)</span><span class="toc-page">Halaman 19</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">4.8 Modul Integritas Blockchain (backend/blockchain/ledger.py)</span><span class="toc-page">Halaman 20</span></div>
    <div class="toc-item" style="padding-left: 20px;"><span class="toc-title">4.9 API Server FastAPI & Frontend UI (Darkroom/app.py)</span><span class="toc-page">Halaman 21</span></div>

    <div class="toc-item"><span class="toc-title">BAB V: PANDUAN MENGHADAPI TANYA-JAWAB SIDANG (15 CHEAT SHEET)</span><span class="toc-page">Halaman 22</span></div>
    <div class="toc-item"><span class="toc-title">BAB VI: KESIMPULAN & PENUTUP</span><span class="toc-page">Halaman 25</span></div>
</div>

<div class="callout callout-success avoid-break">
    <div class="callout-title">Ringkasan Eksekutif (Executive Summary)</div>
    <p>
        Proyek <strong>Darkroom 2.0</strong> adalah sistem perangkat lunak keamanan informasi multimedia yang dirancang untuk mengatasi kerentanan data pada aktivitas intelijen dan jurnalisme investigasi. Berbeda dengan aplikasi kriptografi akademik konvensional yang menyajikan tombol kriptografi secara telanjang, Darkroom menyamarkan seluruh fungsi pertahanan di balik antarmuka studio penyunting foto profesional bertema gelap (*dark-mode*) yang meniru Adobe Lightroom.
    </p>
    <p>
        Aplikasi ini berhasil mengintegrasikan seluruh <strong>7 kriteria teknis wajib</strong> dari Slide 46 Materi 8 Kuliah Kriptografi: autentikasi biometrik wajah (YuNet + SFace), verifikasi perangkat fisik (*hardware dongle* berbasis SD Card via Windows Kernel32), otentikasi kata sandi berkekuatan tinggi (PBKDF2-HMAC-SHA256), *super-encryption* pesan teks (Vigenère + AES-256-GCM AEAD), enkripsi berkas biner mandiri (ChaCha20-Poly1305 AEAD), proteksi basis data lokal (*Field-Level Encryption* pada SQLite), steganografi spasial (LSB Insertion berakselerasi NumPy), serta audit integritas bukti visual (*Proof-of-Work Blockchain Ledger*). Sistem dilengkapi mekanisme darurat *Dead Man's Switch* yang secara otomatis mengunci seluruh modul rahasia seketika saat media SD Card dilepas dari komputer.
    </p>
</div>


<!-- ========================================================================= -->
<!-- 3. BAB I: PENDAHULUAN & LATAR BELAKANG                                      -->
<!-- ========================================================================= -->
<div class="page-break"></div>
<h1>BAB I: Pendahuluan & Latar Belakang Sistem</h1>

<h2>1.1 Urgensi Keamanan Informasi & Jurnalisme Investigasi di Era Digital</h2>
<p>
    Di era modern, jurnalisme investigasi dan operasi intelijen lapangan menghadapi ancaman pengawasan siber (*mass surveillance*), penyadapan jaringan nirkabel, hingga penyitaan perangkat secara paksa oleh entitas berwenang atau pihak yang merasa terancam oleh publikasi bukti pelanggaran hukum. Seorang jurnalis yang meliput kasus spionase korporasi, korupsi pejabat, atau pelanggaran HAM di wilayah rawan memiliki risiko fisik yang nyata apabila catatan lapangan (*field notes*), rekaman bukti foto beresolusi tinggi (*RAW negative*), atau koordinat saksi kunci berhasil diekstraksi dari perangkat laptop mereka.
</p>
<p>
    Sebagian besar solusi perangkat lunak pengamanan komersial seperti BitLocker atau VeraCrypt memiliki kelemahan mendasar: <em>keberadaan perangkat lunak tersebut secara eksplisit menunjukkan bahwa pengguna sedang menyembunyikan sesuatu</em>. Di banyak yurisdiksi, aparat memiliki kewenangan hukum untuk memaksa pengguna membuka enkripsi partisi (*rubber-hose cryptanalysis*). Oleh karena itu, paradigma keamanan informasi tingkat lanjut memerlukan konsep <strong>Plausible Deniability</strong> (kemampuan penyangkalan beralasan), di mana aplikasi yang terpasang di komputer tampak 100% seperti utilitas kerja biasa yang legal dan tidak mencurigakan.
</p>

<h2>1.2 Konsep Kamuflase Plausible Deniability & Parodi Adobe Lightroom</h2>
<p>
    Berdasarkan pertimbangan di atas, sistem ini dinamakan <strong>Darkroom 2.0</strong>, sebuah plesetan (*parody*) elegan dari perangkat lunak standar industri fotografer internasional: <strong>Adobe Lightroom</strong>.
</p>
<p>
    Secara kasat mata, siapapun yang melihat layar laptop jurnalis—termasuk orang yang melirik dari belakang di ruang pers konferensi (*press room*) atau warung kopi—hanya akan melihat antarmuka studio fotografi profesional lengkap dengan bilah filmstrip thumbnail di bagian bawah, kanvas pratinjau gambar di tengah, dan deretan slider penyunting nada (*Exposure, Contrast, Saturation, Warmth*) di panel sebelah kanan.
</p>
<p>
    Namun, di balik kanvas visual tersebut, Darkroom menyembunyikan fasilitas kriptografi tingkat militer. Dongle fisik yang digunakan bukan USB token berlabel keamanan, melainkan <strong>SD Card Reader kamera biasa</strong>. Orang luar akan menganggap jurnalis hanya sedang mentransfer foto hasil liputan dari kamera ke laptop. Namun sistem Darkroom secara aktif memindai keberadaan tanda tangan kriptografi di sektor kartu memori tersebut. Jika kartu dicabut secara tiba-tiba (*Panic Switch / Dead Man's Switch*), aplikasi seketika memusnahkan seluruh *state* sesi rahasia di RAM dan mengembalikan antarmuka ke mode editor foto biasa.
</p>

<h2>1.3 Pemetaan 7 Kriteria Wajib Tugas Akhir Kriptografi (Slide 46)</h2>
<p>
    Pengembangan Darkroom 2.0 secara ketat mengacu dan memenuhi seluruh instruksi penugasan akhir mata kuliah Kriptografi Semester 5 (Slide 46 Materi 8 - Algoritma Fungsi Hash). Berikut adalah tabel pemetaan rinci antara tuntutan akademis dengan implementasi teknis di dalam sistem:
</p>

<table class="avoid-break">
    <thead>
        <tr>
            <th style="width: 5%;">No</th>
            <th style="width: 25%;">Kriteria Tugas (Slide 46)</th>
            <th style="width: 38%;">Implementasi Teknis di Darkroom 2.0</th>
            <th style="width: 17%;">Algoritma Digunakan</th>
            <th style="width: 15%;">Modul Kode</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>1</strong></td>
            <td><strong>Login Biometrik & Hardware Dongle</strong></td>
            <td>
                • <strong>Biometrik</strong>: Verifikasi wajah real-time via Webcam laptop menggunakan OpenCV YuNet (detektor) dan SFace (ekstraktor vektor 128-D) dengan perbandingan Cosine Similarity.<br>
                • <strong>Dongle</strong>: Membaca status fisik removable drive via Windows API Kernel32 (`GetDriveTypeW`), memvalidasi token SHA-256 pada file `darkroom.key` di SD Card.
            </td>
            <td><span class="badge badge-blue">YuNet + SFace</span><br><span class="badge badge-purple">SHA-256 Dongle</span></td>
            <td><code>backend/hardware/ biometric.py</code><br><code>backend/hardware/ dongle.py</code></td>
        </tr>
        <tr>
            <td><strong>2</strong></td>
            <td><strong>Login Algoritma Kriptografi</strong></td>
            <td>
                Autentikasi akun agen menggunakan derivasi kunci satu arah (*One-Way Hash*). Dilengkapi salt acak kriptografis 16-byte unik per pengguna dan key-stretching 100.000 iterasi untuk mencegah serangan Rainbow Table dan brute force GPU.
            </td>
            <td><span class="badge badge-purple">PBKDF2-HMAC-SHA256</span><br><span class="badge badge-blue">Salt 128-bit</span></td>
            <td><code>backend/crypto/ auth.py</code></td>
        </tr>
        <tr>
            <td><strong>3</strong></td>
            <td><strong>Super Enkripsi Pesan Teks</strong></td>
            <td>
                Mengamankan catatan lapangan (*Photo Intel & GPS Field Notes*) secara berlapis ganda berantai (*chained*): Tahap 1 menggunakan algoritma klasik (Vigenère Cipher), dilanjutkan Tahap 2 menggunakan algoritma modern (AES-256-GCM AEAD).
            </td>
            <td><span class="badge badge-amber">Vigenère Cipher</span><br>+<br><span class="badge badge-green">AES-256-GCM AEAD</span></td>
            <td><code>backend/crypto/ super_encrypt.py</code></td>
        </tr>
        <tr>
            <td><strong>4</strong></td>
            <td><strong>Enkripsi File (Beda dari Teks)</strong></td>
            <td>
                Mengamankan berkas foto mentah menggunakan ChaCha20-Poly1305 AEAD, algoritma yang berbeda arsitekturnya dari enkripsi teks. Format ini menambahkan header metadata dan tag autentikasi Poly1305 untuk mendeteksi perubahan berkas.
            </td>
            <td><span class="badge badge-green">ChaCha20-Poly1305 AEAD</span><br>(256-bit key)</td>
            <td><code>backend/crypto/ file_cipher.py</code></td>
        </tr>
        <tr>
            <td><strong>5</strong></td>
            <td><strong>Pesan Penting Terenkripsi di Database</strong></td>
            <td>
                Penerapan <em>Field-Level Encryption (FLE)</em> pada basis data SQLite (`darkroom.db`). Kolom metadata umum (judul, nama file) disimpan plain untuk keperluan query, sedangkan kolom sensitif (`secret_intel_note`) dienkripsi dengan AES sebelum dieksekusi `INSERT`.
            </td>
            <td><span class="badge badge-green">AES-256-GCM</span><br>(Field-Level FLE)</td>
            <td><code>backend/database/ db.py</code></td>
        </tr>
        <tr>
            <td><strong>6</strong></td>
            <td><strong>Pesan Gambar dengan Steganografi</strong></td>
            <td>
                Menyisipkan pesan rahasia ke dalam citra digital melalui modifikasi bit paling tidak berpengaruh (LSB / Least Significant Bit) pada kanal pixel RGB. Mengakomodasi 2 skenario: teks ter-super enkripsi dan gambar decoy dua arah (*secret image inside decoy cover*). Diakselerasi via manipulasi matriks biner NumPy.
            </td>
            <td><span class="badge badge-blue">LSB 1-Bit RGB</span><br>(NumPy Vectorized)</td>
            <td><code>backend/stego/ lsb.py</code></td>
        </tr>
        <tr>
            <td><strong>7</strong></td>
            <td><strong>Blockchain Sederhana untuk Aset Penting</strong></td>
            <td>
                Buku besar rantai blok (*Digital Asset Provenance & Chain of Custody*). Setiap foto dihitung hash SHA-256-nya, dikaitkan dengan blok sebelumnya (*previous hash*), dan ditambang menggunakan konsensus *Proof-of-Work (PoW)*. Dilengkapi fitur audit deteksi manipulasi (*tamper detection*).
            </td>
            <td><span class="badge badge-purple">SHA-256 Chaining</span><br><span class="badge badge-amber">Proof-of-Work (PoW)</span></td>
            <td><code>backend/blockchain/ ledger.py</code></td>
        </tr>
    </tbody>
</table>


<!-- ========================================================================= -->
<!-- 4. BAB II: ARSITEKTUR PERANGKAT LUNAK & ALUR OPERASIONAL                   -->
<!-- ========================================================================= -->
<div class="page-break"></div>
<h1>BAB II: Arsitektur Perangkat Lunak & Alur Operasional</h1>

<h2>2.1 Arsitektur Sistem Berbasis FastAPI & Client-Side Engine</h2>
<p>
    Darkroom 2.0 dibangun menggunakan pola arsitektur modern <strong>Decoupled Micro-Service Architecture</strong>. Sistem memisahkan secara tegas antara lapisan antarmuka visual (Frontend Presentation Layer), lapisan gerbang pertahanan & orkestrasi (API Gateway Server), lapisan komputasi kriptografi murni (Core Crypto Engine), serta lapisan persistensi data fisik (Storage & Database Layer).
</p>

<div class="avoid-break" style="margin: 14px 0; text-align: center;">
    <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px; text-align: left; font-family: 'Consolas', monospace; font-size: 8pt; line-height: 1.4;">
        +---------------------------------------------------------------------------------------------------------+<br>
        |                                       FRONTEND CLIENT (HTML5 / CSS3 / ES6)                              |<br>
        |  [Studio Editor (Canvas + Sliders)]  [Filmstrip Bar]  [Blockchain 5-Grid View]  [Stego Extraction Tool] |<br>
        +---------------------------------------------------------------------------------------------------------+<br>
                                                              | (RESTful JSON / Form-Data over HTTP)<br>
                                                              v<br>
        +---------------------------------------------------------------------------------------------------------+<br>
        |                                        FASTAPI BACKEND SERVER (Darkroom/app.py)                         |<br>
        |   /api/dongle/*   |   /api/auth/*   |   /api/catalog/*   |   /api/stego/*   |   /api/blockchain/*       |<br>
        +---------------------------------------------------------------------------------------------------------+<br>
                                                              |<br>
                       +--------------------------------------+--------------------------------------+<br>
                       |                                                                             |<br>
                       v                                                                             v<br>
        +------------------------------+                                              +------------------------------+<br>
        |      CORE CRYPTO ENGINES     |                                              |      PHYSICAL STORAGE        |<br>
        |  • super_encrypt (Vig + AES) |                                              |  • storage/catalog/ (Images) |<br>
        |  • file_cipher (ChaCha20)    |                                              |  • storage/exports/ (Stego)  |<br>
        |  • lsb.py (NumPy Vectorized) |                                              |  • storage/darkroom.db (SQL) |<br>
        |  • ledger.py (PoW Block)     |                                              |  • storage/photo_blockchain  |<br>
        |  • biometric.py (YuNet+SF)   |                                              |  • SD Card: darkroom.key     |<br>
        +------------------------------+                                              +------------------------------+
    </div>
</div>

<p>
    <strong>Keunggulan Desain:</strong>
</p>
<ul>
    <li><strong>Zero Black-Box Cryptography:</strong> Seluruh modul inti (Vigenère, LSB, ChaCha20-Poly1305 AEAD, Blockchain PoW) dirancang transparan dengan pustaka standar industri, memudahkan pembuktian matematis saat presentasi di hadapan dewan penguji.</li>
    <li><strong>Client-Side High-Performance Canvas:</strong> Manipulasi filter pencahayaan (*Exposure, Contrast, Saturation*) diproses langsung pada kartu grafis peramban menggunakan elemen HTML5 Canvas dan WebGL, sehingga antarmuka berjalan 60 FPS tanpa membebani server lokal.</li>
    <li><strong>Cross-Platform Compatibility:</strong> Meskipun deteksi perangkat keras (*Dongle*) memanfaatkan Windows Kernel32 API, seluruh modul kriptografi dan steganografi ditulis dalam Python murni yang kompatibel lintas sistem operasi (Windows, Linux, macOS).</li>
</ul>

<h2>2.2 Alur Kerja Pengguna (User Flow) & Dead Man's Switch</h2>
<p>
    Operasional sistem mengikuti alur kerja taktis terencana yang menggambarkan misi jurnalis intelijen di lapangan:
</p>

<ol>
    <li>
        <strong>Fase 1: Deteksi Kunci Fisik (SD Card Dongle)</strong><br>
        Aplikasi dijalankan dalam kondisi normal. Background poller di JavaScript mengecek rute `/api/dongle/status` setiap 2 detik. Jika kartu memori kamera dengan file `darkroom.key` yang berisi hash SHA-256 sah terpasang di Card Reader, indikator status di pojok kiri bawah berubah menjadi hijau (*SD Reader Connected*).
    </li>
    <li>
        <strong>Fase 2: Otentikasi Ganda (Biometrik Wajah + Kriptografis)</strong><br>
        Pengguna menekan tombol otentikasi. Kamera webcam menyala, memindai wajah pengguna melalui OpenCV YuNet, mengekstrak 128-D feature vector melalui SFace, dan membandingkannya dengan embedding resmi via Cosine Similarity (threshold &ge; 0.363). Setelah wajah cocok, pengguna memasukkan kata sandi yang divalidasi menggunakan PBKDF2-HMAC-SHA256.
    </li>
    <li>
        <strong>Fase 3: Masuk ke Ruang Studio Editor</strong><br>
        Setelah otentikasi lolos, seluruh kemampuan rahasia terbuka. Jurnalis dapat memilih foto dari filmstrip katalog, mengatur tone warna, melakukan penggantian nama (*Rename*), atau menghapus berkas (*Delete*).
    </li>
    <li>
        <strong>Fase 4: Penyisipan Catatan Intelijen (Super-Enkripsi + LSB Stego)</strong><br>
        Jurnalis memasukkan memo rahasia pada panel *Stego Teks*. Pesan dienkripsi berlapis: Vigenère Cipher &rarr; AES-256-GCM AEAD. Ciphertext kemudian disisipkan ke pixel foto penutup (*cover image*) melalui LSB 1-bit, dan salinan catatan terenkripsi otomatis disimpan ke basis data SQLite `darkroom.db`.
    </li>
    <li>
        <strong>Fase 5: Penguncian Berkas Mentah di Harddisk (ChaCha20 File Lock)</strong><br>
        File foto beresolusi penuh dikunci menjadi file `.enc` menggunakan ChaCha20-Poly1305 AEAD. File asli dihapus dari harddisk sehingga jika laptop disita, berkas mentah tidak dapat dibuka oleh software pembaca foto biasa.
    </li>
    <li>
        <strong>Fase 6: Pencatatan ke Buku Besar Blockchain</strong><br>
        Sebelum diekspor ke markas, foto dicatatkan ke blockchain. Sistem menghitung hash SHA-256 berkas, merangkainya ke blok sebelumnya, dan menjalankan algoritma konsensus Proof-of-Work (PoW) mencari Nonce yang menghasilkan hash berawalan `00`.
    </li>
    <li>
        <strong>Fase 7: Aktivasi Panic Switch (Dead Man's Switch)</strong><br>
        Jika situasi lapangan terancam bahaya, agen cukup mencabut SD Card Reader dari port USB. Sistem secara instan mendeteksi hilangnya media penyimpanan eksternal, menghapus sesi login di memori, dan mengunci kembali seluruh modul kriptografi ke tampilan dasar foto editor biasa (*Plausible Deniability*).
    </li>
</ol>


<!-- ========================================================================= -->
<!-- 5. BAB III: LANDASAN TEORI & FORMULASI MATEMATIS                           -->
<!-- ========================================================================= -->
<div class="page-break"></div>
<h1>BAB III: Landasan Teori & Formulasi Matematis Kriptografi</h1>

<h2>3.1 Kriptografi Klasik: Vigenère Cipher (Substitusi Polialfabetik)</h2>
<p>
    Sesuai dengan <strong>Materi 4 (Vigenere Cipher)</strong>, algoritma Vigenère merupakan bentuk kriptografi klasik berbasis substitusi polialfabetik yang ditemukan oleh Blaise de Vigenère pada abad ke-16. Berbeda dengan Caesar Cipher yang menggunakan pergeseran tunggal konstan (monoalfabetik), Vigenère menggunakan kunci berupa kata yang diulang sepanjang teks pesan untuk menentukan nilai pergeseran yang dinamis pada setiap karakter.
</p>
<div class="formula-box">
    <strong>Enkripsi:</strong> C<sub>i</sub> = (P<sub>i</sub> + K<sub>(i mod m)</sub>) mod 26<br>
    <strong>Dekripsi:</strong> P<sub>i</sub> = (C<sub>i</sub> - K<sub>(i mod m)</sub> + 26) mod 26
</div>
<p>
    Di mana P<sub>i</sub> adalah nilai numerik karakter Plaintext (A=0, B=1, ..., Z=25), C<sub>i</sub> adalah nilai numerik karakter Ciphertext, K adalah karakter kunci ke-i, dan m adalah panjang karakter kata kunci.
</p>
<p>
    <strong>Kelemahan & Alasan Super Enkripsi:</strong> Meskipun tahan terhadap analisis frekuensi huruf tunggal, Vigenère memiliki kelemahan periodisitas kunci yang dapat dipecahkan menggunakan <em>Metode Uji Kasiski</em> dan <em>Indeks Koinsidensi Friedman</em>. Oleh sebab itu, di dalam Darkroom 2.0, Vigenère Cipher tidak digunakan sendirian melainkan dijadikan <em>lapisan konfusi awal (Stage 1)</em> sebelum hasilnya dienkripsi kembali oleh cipher modern standar militer (AES-256).
</p>

<h2>3.2 Kriptografi Modern: AES-256 Rijndael (Block Cipher SPN)</h2>
<p>
    Mengacu pada <strong>Materi 5 & 6 (Block Cipher & AES)</strong>, <em>Advanced Encryption Standard (AES)</em> merupakan algoritma enkripsi simetris standar internasional (FIPS PUB 197) yang berbasis jaringan substitusi-permutasi (*Substitution-Permutation Network / SPN*). AES-256 menggunakan panjang kunci 256 bit (32 byte) dan memproses blok data biner berukuran 128 bit (16 byte) yang direpresentasikan dalam matriks status 4x4 berdimensi byte.
</p>
<p>
    Proses enkripsi AES-256 terdiri dari <strong>14 putaran (rounds)</strong>, di mana setiap putaran melakukan 4 transformasi matematis yang sangat ketat:
</p>
<ol>
    <li><strong>SubBytes:</strong> Transformasi substitusi non-linear byte per byte menggunakan tabel S-Box berbasis inversi multiplikatif pada medan berhingga Galois Field <em>GF(2<sup>8</sup>)</em> diikuti oleh transformasi afinitas. Transformasi ini menjamin prinsip <em>Confusion</em> Shannon.</li>
    <li><strong>ShiftRows:</strong> Operasi permutasi siklis baris matriks status ke arah kiri. Baris ke-0 tidak digeser, baris ke-1 digeser 1 byte, baris ke-2 digeser 2 byte, dan baris ke-3 digeser 3 byte.</li>
    <li><strong>MixColumns:</strong> Operasi transformasi linear kolom matriks status di mana setiap kolom dikalikan dengan polinomial tetap <em>c(x)</em> di atas medan <em>GF(2<sup>8</sup>)</em>. Operasi ini bersama ShiftRows menjamin prinsip <em>Diffusion</em> Shannon (efek longsoran / *Avalanche Effect*).</li>
    <li><strong>AddRoundKey:</strong> Setiap byte pada matriks status dioperasikan secara bitwise XOR dengan sub-kunci putaran (*Round Key*) yang dihasilkan dari algoritma ekspansi kunci Rijndael.</li>
</ol>
<p>
    <strong>Mode Operasi GCM & Authenticated Encryption:</strong> Sistem Darkroom mengimplementasikan AES-256-GCM AEAD dengan nonce acak dan authentication tag. Selain menjaga kerahasiaan, tag memastikan ciphertext dan data terikat tidak berubah saat dekripsi:
</p>
<div class="formula-box">
    (ciphertext, tag) = AES-GCM<sub>K</sub>(nonce, plaintext, associated data)
</div>

<h2>3.3 Kriptografi File: ChaCha20-Poly1305 AEAD</h2>
<p>
    Sesuai instruksi tugas bahwa algoritma file <strong>harus berbeda</strong> dari algoritma pesan teks, Darkroom 2.0 memilih <strong>ChaCha20-Poly1305 AEAD</strong> (RFC 8439). Kombinasi ini menyediakan enkripsi ChaCha20 dan autentikasi Poly1305 untuk ciphertext serta metadata terikat:
</p>
<div class="formula-box">
    ciphertext_and_tag = ChaCha20Poly1305(key).encrypt(nonce, file_data, associated_data)
</div>
<p>
    <strong>Properti perlindungan file:</strong>
</p>
<div class="formula-box">
    key = HKDF-SHA256(passphrase, salt, info, length=32)<br>
    tag = Poly1305(ciphertext, associated_data)
</div>
<p>
    <strong>Mengapa ChaCha20 Dipilih untuk Berkas Foto RAW?</strong>
</p>
<ul>
    <li><strong>Keragaman algoritma:</strong> ChaCha20-Poly1305 berbeda dari AES-256-GCM yang digunakan untuk teks.</li>
    <li><strong>Authenticated Encryption:</strong> Metadata dan ciphertext dilindungi tag Poly1305, sehingga perubahan pada isi atau header berkas dapat terdeteksi saat dekripsi.</li>
    <li><strong>Derivasi kunci:</strong> Kunci 256-bit diturunkan menggunakan HKDF-SHA256 dengan salt dan context yang sesuai.</li>
</ul>

<h2>3.4 Fungsi Hash SHA-256 & Key Stretching PBKDF2</h2>
<p>
    Berdasarkan <strong>Materi 8 (Algoritma Fungsi Hash)</strong>, <em>Secure Hash Algorithm 256-bit (SHA-256)</em> merupakan fungsi hash satu arah yang memetakan masukan biner berukuran sembarang menjadi intisari pesan (*message digest*) berukuran tetap 256 bit (64 karakter heksadesimal). SHA-256 beroperasi dengan konstruksi Merkle-Damg&aring;rd melalui 64 putaran kompresi pada blok pesan 512 bit.
</p>
<p>
    <strong>Karakteristik Mutlak SHA-256:</strong>
</p>
<ol>
    <li><strong>One-Way Property (Pre-image Resistance):</strong> Secara komputasi mustahil merekonstruksi data foto atau kata sandi asli jika hanya diketahui nilai hash-nya: <em>diberikan H = Hash(M), mustahil mencari M</em>.</li>
    <li><strong>Second Pre-image Resistance:</strong> Diberikan foto M<sub>1</sub>, mustahil secara komputasi menemukan foto berbeda M<sub>2</sub> yang memiliki hash identik.</li>
    <li><strong>Collision Resistance:</strong> Mustahil menemukan dua pasangan foto berbeda sembarang yang menghasilkan nilai hash sama.</li>
    <li><strong>Avalanche Effect (Efek Longsoran):</strong> Perubahan 1 bit saja pada foto (misal memodifikasi 1 nilai pixel) akan mengubah lebih dari 50% karakter digest secara acak.</li>
</ol>
<p>
    <strong>PBKDF2-HMAC-SHA256:</strong> Untuk otentikasi login agen, kata sandi tidak di-hash menggunakan SHA-256 biasa karena rentan terhadap serangan kamus berbasis GPU. Darkroom menerapkan <em>Password-Based Key Derivation Function 2 (RFC 2898)</em> dengan 100.000 putaran iterasi HMAC-SHA256 yang dikombinasikan dengan <em>Cryptographic Salt</em> unik berukuran 16 byte.
</p>

<h2>3.5 Steganografi Citra Spasial LSB (Least Significant Bit)</h2>
<p>
    Mengacu pada <strong>Materi 9 (Steganografi)</strong>, steganografi adalah seni dan ilmu menyembunyikan eksistensi pesan rahasia di dalam media pembawa (*carrier/cover*) sehingga pihak ketiga tidak menyadari adanya komunikasi rahasia.
</p>
<p>
    Citra digital standar (24-bit Truecolor RGB) tersusun atas piksel-piksel yang masing-masing memiliki 3 kanal warna: Red, Green, dan Blue. Setiap kanal bernilai integer 8-bit (0 hingga 255):
</p>
<div class="formula-box">
    Representasi Biner 1 Byte Pixel: [ b<sub>7</sub> b<sub>6</sub> b<sub>5</sub> b<sub>4</sub> b<sub>3</sub> b<sub>2</sub> b<sub>1</sub> <strong>b<sub>0</sub></strong> ]<br>
    MSB (Most Significant Bit) = b<sub>7</sub> (Nilai 128) &bull; LSB (Least Significant Bit) = b<sub>0</sub> (Nilai 1)
</div>
<p>
    Karena bit ke-0 (LSB) hanya menyumbang perbedaan nilai intensitas sebesar 1 satuan tingkat kecerahan, mata manusia (*Human Visual System / HVS*) secara fisiologis <strong>mustahil</strong> membedakan warna RGB `(200, 150, 80)` dengan `(201, 150, 80)`.
</p>
<p>
    <strong>Akselerasi Biner NumPy (Super Fast Embedding):</strong><br>
    Berbeda dengan kode steganografi pemula yang melakukan loop `for` di Python secara lambat (bisa memakan waktu 15-30 detik pada foto kamera 16 Megapixel), Darkroom 2.0 mengimplementasikan manipulasi matriks tervektorisasi murni NumPy:
</p>
<div class="formula-box">
    P' = (P &amp; 254) | B<sub>payload</sub>
</div>
<p>
    Operasi bitwise AND dengan nilai 254 (`11111110` biner) me-nol-kan bit LSB pixel pembawa, lalu operasi bitwise OR memasukkan bit muatan rahasia `B`. Proses ini selesai dalam waktu <strong>kurang dari 0,02 detik</strong> pada citra beresolusi penuh.
</p>

<h2>3.6 Buku Besar Terdistribusi: Blockchain Proof-of-Work</h2>
<p>
    Untuk menjamin integritas aset foto bukti jurnalistik (*Chain of Custody*), Darkroom mengimplementasikan struktur data rantai blok sederhana. Setiap blok memiliki struktur data:
</p>
<div class="formula-box">
    Block = {<br>
    &nbsp;&nbsp;Index, Timestamp, Asset_Name, Photo_Hash (SHA-256),<br>
    &nbsp;&nbsp;Photographer_ID, Metadata, Previous_Hash, Nonce, Current_Hash<br>
    }
</div>
<p>
    <strong>Mekanisme Konsensus Proof of Work (PoW):</strong><br>
    Untuk mencegah modifikasi data masa lalu secara sepihak, setiap blok harus "ditambang" (*mined*). Sistem mencari nilai integer acak `Nonce` sedemikian rupa sehingga:
</p>
<div class="formula-box">
    SHA-256(Block_Data + Nonce) diawali dengan "00" (Difficulty Target = 2)
</div>
<p>
    Jika seorang penyerang memodifikasi 1 pixel foto di harddisk, maka `Photo_Hash` blok tersebut berubah. Perubahan tersebut menyebabkan `Current_Hash` blok tidak valid dan rantai `Previous_Hash` ke seluruh blok berikutnya terputus seketika (*Tamper Detected*).
</p>


<!-- ========================================================================= -->
<!-- 6. BAB IV: BEDAH KODE PROGRAM LENGKAP                                      -->
<!-- ========================================================================= -->
<div class="page-break"></div>
<h1>BAB IV: Bedah Kode Program Lengkap (Source Code Walkthrough)</h1>

<h2>4.1 Modul Hardware Dongle (backend/hardware/dongle.py)</h2>
<p>
    Modul ini bertanggung jawab memeriksa media penyimpanan eksternal (SD Card / Flashdisk) secara langsung ke sistem operasi Windows menggunakan antarmuka CTypes Kernel32:
</p>
<pre><code>def get_removable_drives():
    removable_drives = []
    # Membaca bitmask drive aktif di Windows (A-Z)
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if (bitmask >> (ord(letter) - ord('A'))) & 1:
            drive_path = f"{letter}:\\\\"
            # Nilai 2 merepresentasikan DRIVE_REMOVABLE (Flashdisk / SD Card)
            if ctypes.windll.kernel32.GetDriveTypeW(drive_path) == 2:
                removable_drives.append(drive_path)
    return removable_drives

def verify_dongle():
    drives = get_removable_drives()
    if not drives:
        return False, "Tidak ada SD Card / Flashdisk terdeteksi.", None
    for drive in drives:
        key_p = os.path.join(drive, "darkroom.key")
        if os.path.exists(key_p):
            with open(key_p, "r", encoding="utf-8") as f:
                content = f.read().strip()
            # Validasi hash SHA-256 token terhadap token resmi
            if hashlib.sha256(content.encode('utf-8')).hexdigest() == EXPECTED_TOKEN_HASH:
                return True, f"Dongle Sah Ditemukan di {drive}", drive
    return False, "File kunci darkroom.key tidak valid!", None</code></pre>

<h2>4.2 Modul Biometrik Wajah (backend/hardware/biometric.py)</h2>
<p>
    Menggunakan AI Model OpenCV Zoo yang dijalankan secara lokal (100% offline). YuNet mendeteksi koordinat wajah, SFace mengekstrak 128-dimensional embedding, dan perbandingan dilakukan dengan Cosine Similarity NumPy:
</p>
<pre><code>def compare_faces(current_feature, registered_feature):
    # Representasi vektor 128 dimensi
    f1 = current_feature.flatten().astype(np.float32)
    f2 = registered_feature.flatten().astype(np.float32)
    
    # Formulasi Matematis: Cosine Similarity = (A . B) / (||A|| * ||B||)
    dot_product = np.dot(f1, f2)
    norm_f1 = np.linalg.norm(f1)
    norm_f2 = np.linalg.norm(f2)
    
    if norm_f1 == 0 or norm_f2 == 0:
        return False, 0.0
    cosine_score = dot_product / (norm_f1 * norm_f2)
    
    # Threshold standar model SFace: >= 0.363 dianggap orang yang sama
    is_match = bool(cosine_score >= COSINE_THRESHOLD)
    return is_match, float(cosine_score)</code></pre>

<h2>4.3 Modul Otentikasi Sandi (backend/crypto/auth.py)</h2>
<p>
    Mengamankan otentikasi kata sandi dengan PBKDF2-HMAC-SHA256 berkekuatan 100.000 iterasi dan verifikasi waktu konstan (*constant-time comparison*):
</p>
<pre><code>def hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16) # 128-bit cryptographic salt
    derived_key = hashlib.pbkdf2_hmac(
        hash_name='sha256',
        password=password.encode('utf-8'),
        salt=salt.encode('utf-8'),
        iterations=100_000
    )
    return derived_key.hex(), salt

def verify_login(password_input: str) -> tuple:
    with open(AUTH_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    test_hash, _ = hash_password(password_input, data["salt"])
    # secrets.compare_digest mencegah kebocoran Timing Attack
    if secrets.compare_digest(test_hash, data["password_hash"]):
        return True, "Login Berhasil!"
    return False, "Password Salah!"</code></pre>

<h2>4.4 Modul Super Enkripsi Teks (backend/crypto/super_encrypt.py)</h2>
<p>
    Menggabungkan kriptografi klasik (Vigenère) dan modern (AES-256-GCM AEAD) secara berantai:
</p>
<pre><code>def super_encrypt(plaintext: str, vigenere_key: str, aes_key: str) -> dict:
    # Lapis 1: Enkripsi Klasik (Substitusi Polialfabetik Vigenère)
    stage1_result = vigenere_encrypt(plaintext, vigenere_key)
    # Lapis 2: Enkripsi Modern (AES-256-GCM dengan authentication tag)
    stage2_result = aes_encrypt(stage1_result, aes_key)
    return {
        "plaintext": plaintext,
        "intermediate_vigenere": stage1_result,
        "final_ciphertext": stage2_result
    }

def super_decrypt(ciphertext: str, vigenere_key: str, aes_key: str) -> dict:
    # Kupas Lapis 1: Dekripsi Modern (AES-256-GCM dengan validasi tag)
    stage1_result = aes_decrypt(ciphertext, aes_key)
    # Kupas Lapis 2: Dekripsi Klasik (Vigenère)
    stage2_result = vigenere_decrypt(stage1_result, vigenere_key)
    return {"final_plaintext": stage2_result}</code></pre>

<h2>4.5 Modul Enkripsi Berkas ChaCha20 (backend/crypto/file_cipher.py)</h2>
<p>
    Enkripsi file biner menggunakan ChaCha20-Poly1305 AEAD dengan header metadata dan tag autentikasi:
</p>
<pre><code>def encrypt_file(input_filepath: str, output_filepath: str, passphrase: str) -> dict:
    key = derive_key_hkdf(passphrase, salt=salt, info=HKDF_INFO_FILE, length=32)
    ciphertext_and_tag = ChaCha20Poly1305(key).encrypt(nonce, file_data, aad)
    return {"status": "LOCKED", "algorithm": "ChaCha20-Poly1305 AEAD"}</code></pre>

<h2>4.6 Modul Steganografi LSB Hibrida (backend/stego/lsb.py)</h2>
<p>
    Penyisipan muatan biner ke dalam LSB kanal RGB citra yang dioptimasi menggunakan NumPy:
</p>
<pre><code>def embed_raw_bytes(cover_image_path: str, payload_bytes: bytes, output_image_path: str):
    img = Image.open(cover_image_path).convert('RGB')
    arr = np.array(img, dtype=np.uint8)
    full_data = payload_bytes + b":::END_ATOSE:::" # Delimiter penanda akhir pesan
    bits = np.unpackbits(np.frombuffer(full_data, dtype=np.uint8))
    
    flat = arr.reshape(-1) # Ratakan matriks 3D RGB menjadi 1D array
    # Inti Akselerasi: Nol-kan LSB dengan & 254 lalu timpa dengan bit payload
    flat[:len(bits)] = (flat[:len(bits)] & np.uint8(254)) | bits
    
    stego_img = Image.fromarray(arr)
    stego_img.save(output_image_path, format='PNG') # Format PNG lossless wajib!</code></pre>

<h2>4.7 Modul Database SQLite Terenkripsi (backend/database/db.py)</h2>
<p>
    Field-Level Encryption (FLE) untuk melindungi catatan intelijen di dalam tabel basis data:
</p>
<pre><code>def insert_photo_with_encrypted_note(title, filename, public_caption, secret_note, photo_hash, key):
    # Kolom sensitif 'secret_intel_note' selalu dienkripsi AES sebelum SQL INSERT
    encrypted_note = aes_encrypt(secret_note, key)
    conn = get_connection()
    c = conn.cursor()
    query = "INSERT INTO photo_catalog (photo_title, filename, public_caption, secret_intel_note, photo_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)"
    c.execute(query, (title, filename, public_caption, encrypted_note, photo_hash, time.ctime()))
    conn.commit()
    conn.close()</code></pre>

<h2>4.8 Modul Integritas Blockchain (backend/blockchain/ledger.py)</h2>
<p>
    Implementasi rantai blok dan penambangan konsensus Proof of Work:
</p>
<pre><code>class Block:
    def compute_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index, "timestamp": self.timestamp,
            "asset_name": self.asset_name, "photo_hash": self.photo_hash,
            "previous_hash": self.previous_hash, "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    def mine_block(self):
        # Proof of Work: Hash blok harus diawali dengan "00"
        while not self.current_hash.startswith("00"):
            self.nonce += 1
            self.current_hash = self.compute_hash()</code></pre>

<h2>4.9 API Server FastAPI & Frontend UI (Darkroom/app.py)</h2>
<p>
    FastAPI menyediakan 15 rute endpoint modular, termasuk fitur penghapusan foto katalog fisik:
</p>
<pre><code>@app.post("/api/catalog/delete")
def delete_catalog_photo(filename: str = Form(...)):
    clean_name = os.path.basename(filename).strip()
    p = os.path.join(CATALOG_DIR, clean_name)
    deleted = False
    if os.path.exists(p):
        os.remove(p)
        deleted = True
    if os.path.exists(p + ".enc"): # Hapus juga versi terenkripsi jika ada
        os.remove(p + ".enc")
        deleted = True
    if not deleted:
        raise HTTPException(status_code=404, detail="Foto tidak ditemukan!")
    return {"success": True, "deleted_filename": clean_name}</code></pre>


<!-- ========================================================================= -->
<!-- 7. BAB V: PANDUAN MENGHADAPI TANYA-JAWAB SIDANG DOSEN (15 CHEAT SHEET)      -->
<!-- ========================================================================= -->
<div class="page-break"></div>
<h1>BAB V: Panduan Tanya-Jawab Sidang Dosen (15 Cheat Sheet Kritis)</h1>

<div class="callout callout-warning avoid-break">
    <div class="callout-title">Petunjuk Penggunaan Cheat Sheet Saat Presentasi</div>
    <p>
        Bagian ini dirancang khusus untuk mengantisipasi pertanyaan mendalam dari dosen penguji mengenai logika algoritma, keamanan sistem, dan alasan pemilihan arsitektur. Hafalkan poin-poin kunci di bawah ini agar kamu tampil percaya diri dan menguasai seluruh kode yang kamu bangun.
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q1: Mengapa enkripsi berkas foto menggunakan ChaCha20, sedangkan teks menggunakan AES-256?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Sesuai ketentuan tugas bahwa algoritma berkas harus berbeda dari teks, teks menggunakan AES-256-GCM AEAD, sedangkan berkas menggunakan ChaCha20-Poly1305 AEAD. ChaCha20-Poly1305 memberikan enkripsi sekaligus autentikasi integritas melalui tag Poly1305, sehingga perubahan pada ciphertext atau metadata dapat ditolak saat dekripsi."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q2: Mengapa perlu Super Enkripsi? Bukankah AES-256 saja sudah sangat kuat?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Super Enkripsi diterapkan untuk mengimplementasikan prinsip pertahanan berlapis (*Defense in Depth*) yang menggabungkan Kriptografi Klasik dan Kriptografi Modern. Vigenère Cipher memberikan lapisan konfusi substitusi alfabetik awal pada karakter plaintext, sedangkan AES-256 memberikan konfusi matematis non-linear (S-Box) dan difusi matriks status (ShiftRows dan MixColumns). Jika seandainya ada kelemahan implementasi pada salah satu algoritma, ciphertext tetap terlindungi oleh algoritma pasangannya."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q3: Mengapa kata sandi tidak di-hash menggunakan SHA-256 biasa? Kenapa harus PBKDF2?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Fungsi hash SHA-256 standar dirancang untuk berjalan sangat cepat (menghitung jutaan hash per detik). Hal ini justru berbahaya untuk kata sandi karena penyerang dapat melakukan serangan *Brute-Force* dan mencocokkan *Rainbow Table* menggunakan GPU modern dalam waktu singkat. Dengan menerapkan PBKDF2-HMAC-SHA256 sebanyak 100.000 iterasi (*Key Stretching*) dan salt 16-byte unik, waktu komputasi untuk menebak satu tebakan kata sandi diperlambat secara drastis, membuat serangan brute force secara komputasi tidak layak (*computationally infeasible*)."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q4: Mengapa hasil foto steganografi LSB harus disimpan dalam format PNG dan tidak boleh JPG?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Format JPEG menggunakan algoritma kompresi berbayar rugi (*Lossy Compression*) berbasis *Discrete Cosine Transform (DCT)* dan kuantisasi frekuensi. Kompresi JPEG secara sengaja membuang dan mengubah nilai-nilai bit frekuensi tinggi pada pixel untuk menghemat ukuran berkas. Perubahan nilai pixel tersebut akan seketika merusak bit muatan rahasia yang tersimpan di bit LSB. Sebaliknya, format PNG menggunakan algoritma kompresi Deflate tanpa rugi (*Lossless Compression*), sehingga nilai RGB setiap pixel dijamin 100% identik sebelum dan sesudah penyimpanan berkas."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q5: Bagaimana cara kerja deteksi manipulasi (*Tamper Detection*) pada Blockchain foto?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Setiap blok diikat oleh rantai kriptografi: Blok ke-N menyimpan hash dari Blok ke-(N-1) pada variabel `previous_hash`. Jika ada oknum yang mengubah 1 pixel saja pada foto bukti di harddisk, maka `photo_hash` foto tersebut akan berubah drastis karena *Avalanche Effect* SHA-256. Akibatnya, `current_hash` blok tersebut tidak lagi cocok, dan seluruh keterkaitan `previous_hash` pada blok-blok setelahnya akan terputus. Sistem fungsi verifikasi `verify_integrity()` akan langsung mendeteksi inkonsistensi tersebut dan menyatakan rantai bukti tidak valid."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q6: Mengapa memilih basis data SQLite daripada MySQL / PostgreSQL?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Aplikasi penyunting foto profesional seperti Adobe Lightroom asli menggunakan SQLite sebagai mesin katalog lokalnya (`.lrcat`). Karena fotografer investigasi bekerja secara mandiri di lapangan tanpa koneksi internet atau server sentral, basis data lokal terbenam (*embedded database*) seperti SQLite adalah standar de facto industri. Kami menerapkan <em>Field-Level Encryption (FLE)</em> di mana kolom sensitif `secret_intel_note` dienkripsi AES-256 sebelum dieksekusi perintah SQL `INSERT`. Jika file `darkroom.db` dicuri atau dibuka paksa menggunakan DB Browser for SQLite, data catatan tetap berupa ciphertext acak yang tidak dapat dibaca."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q7: Bagaimana mekanisme pengamanan biometrik wajah di Darkroom 2.0?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Sistem tidak menyimpan foto wajah agen mentah secara telanjang di harddisk karena berisiko dicuri. Sistem mendeteksi wajah agen via neural network OpenCV YuNet, lalu mengekstrak representasi matematika berupa vektor fitur berdimensi 128 (*128-D embedding*) menggunakan OpenCV SFace. Vektor fitur inilah yang disimpan. Saat login, vektor wajah dari kamera dibandingkan dengan vektor tersimpan menggunakan metrik <em>Cosine Similarity</em>. Vektor embedding ini bersifat satu arah dan tidak dapat direkonstruksi kembali menjadi foto wajah asli."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q8: Bagaimana implementasi Dead Man's Switch / Panic Switch bekerja secara teknis?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Sistem memanfaatkan Windows Kernel32 API `GetDriveTypeW` yang memeriksa drive dengan flag `DRIVE_REMOVABLE = 2` (SD Card Reader) melalui pemanggilan berkala di background setiap 2 detik. Jika kartu memori dicabut dari port laptop, respons API seketika bernilai `is_valid: false`. Frontend JavaScript seketika memusnahkan kredensial agen dari memori, mengunci kembali tampilan ke mode Lightroom normal, dan menutup seluruh akses ke brankas rahasia (*Plausible Deniability*)."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q9: Apa perbedaan mendasar antara AES-GCM dan ChaCha20-Poly1305?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "AES-GCM dan ChaCha20-Poly1305 sama-sama merupakan AEAD: keduanya menjaga kerahasiaan sekaligus memverifikasi integritas melalui authentication tag. Perbedaannya terletak pada primitive enkripsi yang digunakan, yaitu AES berbasis blok dengan mode GCM dan ChaCha20 berbasis arus yang dipasangkan dengan Poly1305."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q10: Mengapa perbandingan kata sandi menggunakan `secrets.compare_digest` bukan operator `==` biasa?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Operator string `==` standar di bahasa pemrograman menggunakan perbandingan *early-exit*: perulangan langsung berhenti begitu menemukan karakter pertama yang berbeda. Hal ini membuka celah serangan <em>Timing Attack</em>, di mana peretas dapat mengukur perbedaan waktu eksekusi mikrodetik untuk menebak karakter demi karakter hash yang benar. Fungsi `secrets.compare_digest` membandingkan string dalam waktu konstan (*Constant-Time Comparison*) terlepas dari di mana posisi karakter yang salah, sehingga kebal terhadap analisis waktu."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q11: Berapa kapasitas maksimal teks rahasia yang dapat disisipkan pada foto LSB?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Setiap 1 pixel RGB memiliki 3 kanal warna (R, G, B), sehingga 1 pixel dapat menampung 3 bit pesan. Untuk menyisipkan 1 byte (8 bit) data, dibutuhkan minimal 8/3 &approx; 2,67 pixel. Pada foto kamera standar beresolusi 12 Megapixel (4000 &times; 3000 pixel), tersedia 36.000.000 byte kanal warna, yang setara dengan kapasitas muatan teoritis sebesar 4,5 Megabyte data biner atau ratusan ribu kata dokumen teks."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q12: Bagaimana cara sistem memisahkan pesan rahasia dengan bit pixel foto yang tidak terpakai saat ekstraksi LSB?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Saat proses embedding, sistem menambahkan penanda biner khusus (*Sentinel / Delimiter*) bernama `:::END_ATOSE:::` di akhir muatan data. Saat proses ekstraksi, sistem membaca bit LSB secara bertahap (chunk 1 KB) dan menyusunnya kembali menjadi byte. Begitu urutan byte delimiter ditemukan, pembacaan seketika dihentikan dan byte sebelum delimiter didekodekan sebagai payload yang sah."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q13: Mengapa Proof-of-Work di Blockchain Darkroom menggunakan tingkat kesulitan (Difficulty) 2?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Di aplikasi enterprise seperti Bitcoin, tingkat kesulitan sangat tinggi karena melibatkan jutaan komputer penambang di seluruh dunia. Namun untuk aplikasi studio foto lokal pada laptop jurnalis, Proof of Work dirancang ringan (mencari hash berawalan '00' yang membutuhkan rata-rata 200 hingga 1.000 iterasi Nonce). Ini membuktikan konsep matematis konsensus PoW secara nyata di hadapan dewan penguji dalam waktu penambangan yang responsif (di bawah 0,5 detik) tanpa membuat laptop mengalami *freeze*."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q14: Apakah sistem dapat mendeteksi jika foto decoy (steganografi gambar-dalam-gambar) ditimpa foto lain?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Ya, sistem Darkroom menyertakan header penanda biner tipe konten di awal muatan bit LSB: `DARKROOM_TEXT:` untuk pesan teks super-enkripsi dan `DARKROOM_IMG:` untuk steganografi berkas citra decoy. Menu Dekripsi & Ekstraktor secara otomatis membaca header ini dan menampilkan formulir dekripsi teks atau mengekspor kembali file citra rahasia yang tersembunyi."
    </p>
</div>

<div class="avoid-break" style="margin-bottom: 14px;">
    <h3>Q15: Apa inovasi terbesar dari proyek Darkroom 2.0 ini dibandingkan tugas kriptografi mahasiswa lain?</h3>
    <p>
        <strong>Jawaban Ilmiah:</strong> "Sebagian besar tugas akhir mahasiswa hanya membuat antarmuka kalkulator kriptografi sederhana dengan tombol terisolasi. Inovasi terbesar Darkroom 2.0 adalah <strong>Integrasi Tematik Real-World (Plausible Deniability)</strong>: seluruh 7 kriteria tugas kuliah menyatu secara organis ke dalam alur kerja studio foto investigasi. Dongle menggunakan card reader kamera, steganografi menyatu dalam proses ekspor foto, enkripsi file mengamankan negatif mentah RAW, database FLE mengamankan catatan lapangan, dan blockchain menjamin orisinalitas bukti di persidangan."
    </p>
</div>


<!-- ========================================================================= -->
<!-- 8. BAB VI: KESIMPULAN & PENUTUP                                            -->
<!-- ========================================================================= -->
<div class="page-break"></div>
<h1>BAB VI: Kesimpulan & Penutup</h1>

<h2>6.1 Kesimpulan Proyek</h2>
<p>
    Berdasarkan perancangan, implementasi kode, dan serangkaian pengujian sistem yang telah dilakukan, dapat diambil kesimpulan sebagai berikut:
</p>
<ol>
    <li>
        <strong>Pemenuhan Kriteria 100%:</strong> Seluruh 7 kriteria teknis tugas akhir mata kuliah Kriptografi (Slide 46 Materi 8) telah berhasil diwujudkan secara mandiri (*solo player*) tanpa ada kriteria yang terlewatkan.
    </li>
    <li>
        <strong>Harmonisasi Fungsional & Estetika Visual:</strong> Konsep kamuflase <em>Plausible Deniability</em> yang meniru antarmuka Adobe Lightroom berhasil menyamarkan fungsionalitas kriptografi tingkat tinggi di balik utilitas kerja fotografer yang legal dan wajar.
    </li>
    <li>
        <strong>Ketahanan Algoritma & Kecepatan Eksekusi:</strong> Kombinasi algoritma klasik (Vigenère) dan modern (AES-256-GCM AEAD) memberikan perlindungan berlapis pada data intelijen. Pemilihan ChaCha20-Poly1305 AEAD menjaga kerahasiaan dan integritas berkas multimedia, sedangkan implementasi LSB tervektorisasi NumPy menghasilkan kinerja steganografi instan (&lt; 0,02 detik).
    </li>
    <li>
        <strong>Integritas Bukti Tak Terbantahkan:</strong> Pemanfaatan rantai blok dengan konsensus Proof-of-Work SHA-256 menjamin orisinalitas foto bukti jurnalistik terhadap segala bentuk manipulasi pixel maupun pemalsuan waktu (*anti-tamper digital chain of custody*).
    </li>
</ol>

<h2>6.2 Saran & Pengembangan Mendatang</h2>
<p>
    Untuk pengembangan sistem di masa yang akan datang, beberapa potensi peningkatan yang dapat ditambahkan meliputi:
</p>
<ul>
    <li>Integrasi algoritma steganografi domain transformasi frekuensi seperti <strong>DCT (Discrete Cosine Transform)</strong> atau <strong>DWT (Discrete Wavelet Transform)</strong> agar muatan rahasia tahan terhadap kompresi format JPEG.</li>
    <li>Implementasi algoritma tanda tangan digital asimetris (*Digital Signature*) seperti <strong>ECDSA (Elliptic Curve Digital Signature Algorithm)</strong> atau Ed25519 untuk memvalidasi identitas fotografer langsung di tingkat blok blockchain.</li>
    <li>Pengembangan aplikasi versi desktop executable mandiri menggunakan Electron atau PyQt agar dapat didistribusikan dalam bentuk paket biner `.exe` portabel.</li>
</ul>

<div style="margin-top: 50px; text-align: right;" class="avoid-break">
    <p style="margin-bottom: 60px;">
        Yogyakarta, 1 November 2026<br>
        Pengembang Mandiri (*Solo Player*),
    </p>
    <p style="font-weight: 700; text-decoration: underline; margin-bottom: 2px;">
        Rafi Dzaka Pratama Putra
    </p>
    <p style="color: #64748b; font-size: 9pt; margin-top: 0;">
        NIM: 123240104 &bull; Teknik Informatika UPN "Veteran" Yogyakarta
    </p>
</div>

</body>
</html>
"""

print(f"Menulis file HTML sumber ke: {HTML_OUTPUT_PATH}...")
with open(HTML_OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

print("Memeriksa browser Chrome untuk rendering PDF...")
chrome_paths = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
]

browser_exe = None
for p in chrome_paths:
    if os.path.exists(p):
        browser_exe = p
        break

if not browser_exe:
    print("Browser Chrome/Edge tidak ditemukan di sistem!")
    sys.exit(1)

print(f"Menggunakan browser: {browser_exe}")
print(f"Mengonversi ke PDF: {PDF_OUTPUT_PATH}...")

cmd = [
    browser_exe,
    "--headless",
    "--disable-gpu",
    "--no-pdf-header-footer",
    "--run-all-compositor-stages-before-draw",
    f"--print-to-pdf={PDF_OUTPUT_PATH}",
    HTML_OUTPUT_PATH
]

res = subprocess.run(cmd, capture_output=True, text=True)

if os.path.exists(PDF_OUTPUT_PATH) and os.path.getsize(PDF_OUTPUT_PATH) > 0:
    pdf_size_kb = round(os.path.getsize(PDF_OUTPUT_PATH) / 1024, 2)
    print(f"SUKSES! File PDF berhasil dibuat: {PDF_OUTPUT_PATH}")
    print(f"Ukuran Berkas: {pdf_size_kb} KB")
    
    # Periksa total halaman dengan pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(PDF_OUTPUT_PATH)
        print(f"Total Halaman PDF: {len(reader.pages)} halaman")
    except Exception as e:
        pass
else:
    print(f"Gagal membuat PDF: {res.stderr}")
    sys.exit(1)
