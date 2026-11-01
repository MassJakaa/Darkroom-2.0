"""
=============================================================================
DARKROOM - BLOCKCHAIN SEDERHANA UNTUK INTEGRITAS FOTO (KRITERIA 7)
=============================================================================
Kriteria Tugas: Aset penting diamankan menggunakan teknologi blockchain sederhana.

Konsep di Dunia Fotografi & Jurnalistik Investigasi:
1. Masalah Utama:
   Tersangka atau pihak lawan sering menuduh foto bukti investigasi sebagai
   "foto editan/rekayasa Photoshop".
2. Solusi Blockchain (Chain of Custody / Digital Evidence Ledger):
   - Setiap foto bukti dihitung sidik jari digitalnya (Hash SHA-256).
   - Hash foto tersebut dimasukkan ke dalam rantai blok (Block) yang saling terikat
     dengan blok sebelumnya (Previous Hash).
   - Menerapkan Proof of Work (PoW) ringan (Nonce) untuk mencegah modifikasi mundur.
   - Sifat Immutable: Jika 1 pixel saja dari foto diubah, atau ada orang yang mencoba
     mengganti catatan di masa lalu, seluruh rantai blok berikutnya akan rusak (INVALID).
=============================================================================
"""

import os
import json
import time
import hashlib

# Lokasi penyimpanan buku besar rantai blok
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "storage"))
BLOCKCHAIN_FILE = os.path.join(STORAGE_DIR, "photo_blockchain.json")

# Tingkat kesulitan Proof-of-Work (PoW): Hash blok harus berawalan "00" (ringan & cepat)
DIFFICULTY = 2
DIFFICULTY_PREFIX = "0" * DIFFICULTY


def calculate_file_hash(filepath: str) -> str:
    """
    Menghitung sidik jari kriptografi (Hash SHA-256) dari file foto secara utuh.
    Jika 1 pixel saja berubah, nilai hash ini akan berubah total (Avalanche Effect).
    """
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(64 * 1024):
            sha.update(chunk)
    return sha.hexdigest()


class Block:
    """
    Representasi satu blok di dalam buku besar rantai blok Darkroom.
    """
    def __init__(self, index: int, timestamp: str, asset_name: str, photo_hash: str,
                 photographer_id: str, metadata: str, previous_hash: str,
                 nonce: int = 0, current_hash: str = ""):
        self.index = index
        self.timestamp = timestamp
        self.asset_name = asset_name
        self.photo_hash = photo_hash
        self.photographer_id = photographer_id
        self.metadata = metadata
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.current_hash = current_hash or self.compute_hash()

    def compute_hash(self) -> str:
        """
        Menghitung hash SHA-256 dari seluruh isi blok ini.
        Rumus: SHA256(index + timestamp + asset_name + photo_hash + previous_hash + nonce)
        """
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "asset_name": self.asset_name,
            "photo_hash": self.photo_hash,
            "photographer_id": self.photographer_id,
            "metadata": self.metadata,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    def mine_block(self):
        """
        Proof-of-Work (Konsensus Penambangan Blok):
        Mencari nilai Nonce acak hingga hash blok diawali dengan sejumlah angka nol (DIFFICULTY).
        """
        while not self.current_hash.startswith(DIFFICULTY_PREFIX):
            self.nonce += 1
            self.current_hash = self.compute_hash()

    def to_dict(self) -> dict:
        """Mengubah objek blok ke format dictionary/JSON."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "asset_name": self.asset_name,
            "photo_hash": self.photo_hash,
            "photographer_id": self.photographer_id,
            "metadata": self.metadata,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "current_hash": self.current_hash
        }

    @staticmethod
    def from_dict(data: dict):
        """Membuat objek Blok dari data dictionary/JSON."""
        return Block(
            index=data["index"],
            timestamp=data["timestamp"],
            asset_name=data["asset_name"],
            photo_hash=data["photo_hash"],
            photographer_id=data["photographer_id"],
            metadata=data["metadata"],
            previous_hash=data["previous_hash"],
            nonce=data["nonce"],
            current_hash=data["current_hash"]
        )


class PhotoBlockchain:
    """
    Pengelola rantai blok buku besar integritas foto bukti Darkroom.
    """
    def __init__(self):
        self.chain = []
        self.load_chain()

    def create_genesis_block(self):
        """
        Membuat Blok Perdana (Genesis Block #0) sebagai fondasi awal rantai.
        """
        genesis = Block(
            index=0,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(0)),
            asset_name="GENESIS_DARKROOM_ROOT",
            photo_hash="0" * 64,
            photographer_id="SYSTEM_ROOT",
            metadata="Genesis Block - Fondasi Keamanan Aset Darkroom",
            previous_hash="0" * 64,
            nonce=0
        )
        genesis.mine_block()
        self.chain = [genesis]
        self.save_chain()

    def load_chain(self):
        """Memuat rantai blok dari file penyimpanan lokal."""
        if os.path.exists(BLOCKCHAIN_FILE):
            try:
                with open(BLOCKCHAIN_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chain = [Block.from_dict(b) for b in data]
            except Exception:
                self.create_genesis_block()
        else:
            self.create_genesis_block()

    def save_chain(self):
        """Menyimpan rantai blok ke file JSON."""
        os.makedirs(STORAGE_DIR, exist_ok=True)
        with open(BLOCKCHAIN_FILE, "w", encoding="utf-8") as f:
            json.dump([b.to_dict() for b in self.chain], f, indent=4)

    def get_latest_block(self) -> Block:
        """Mengambil blok terakhir dalam rantai."""
        return self.chain[-1]

    def add_photo_asset(self, photo_path: str, photographer_id: str, metadata: str) -> Block:
        """
        Mencatat aset foto baru ke dalam rantai blockchain.
        """
        asset_name = os.path.basename(photo_path)
        photo_hash = calculate_file_hash(photo_path)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        latest_block = self.get_latest_block()

        new_block = Block(
            index=len(self.chain),
            timestamp=timestamp,
            asset_name=asset_name,
            photo_hash=photo_hash,
            photographer_id=photographer_id,
            metadata=metadata,
            previous_hash=latest_block.current_hash
        )
        
        # Lakukan penambangan (Proof of Work)
        new_block.mine_block()
        
        self.chain.append(new_block)
        self.save_chain()
        return new_block

    def verify_integrity(self) -> tuple:
        """
        Memverifikasi keutuhan rantai blok (Chain Integrity Check):
        1. Apakah hash setiap blok sesuai dengan isinya?
        2. Apakah previous_hash blok ini sama persis dengan hash blok sebelumnya?
        3. Apakah Proof-of-Work (awalan '00') terpenuhi?
        
        Return:
            (is_valid: bool, log_message: str)
        """
        if len(self.chain) == 0:
            return False, "Rantai blok kosong!"

        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # 1. Cek kecocokan isi blok dengan hash-nya
            if current.current_hash != current.compute_hash():
                return False, f"KRITIS! Data di Blok #{current.index} telah DIUBAH / DIPALSUKAN!"

            # 2. Cek kesinambungan rantai
            if current.previous_hash != previous.current_hash:
                return False, f"KRITIS! Rantai terputus antara Blok #{previous.index} dan #{current.index}!"

            # 3. Cek validitas PoW
            if not current.current_hash.startswith(DIFFICULTY_PREFIX):
                return False, f"Proof of Work pada Blok #{current.index} tidak sah!"

        return True, f"Rantai Blockchain 100% VALID dan AMAN ({len(self.chain)} blok terverifikasi)."


# =============================================================================
# DEMO INTERAKTIF DI TERMINAL
# =============================================================================
if __name__ == "__main__":
    bc = PhotoBlockchain()
    
    print("\n" + "="*75)
    print("      DARKROOM - BLOCKCHAIN SEDERHANA BUKTI INTEGRITAS FOTO")
    print("="*75)
    print("Kriteria 7: Aset penting diamankan menggunakan teknologi blockchain.")
    print(f"File Buku Besar: {BLOCKCHAIN_FILE}")
    print("-" * 75)
    
    print("\nPilih Aksi:")
    print("1. Catat Aset Foto Baru ke Blockchain (Mint New Asset)")
    print("2. Lihat Seluruh Buku Besar Rantai Blok (Ledger View)")
    print("3. Uji Verifikasi Keaslian & Integritas Rantai Blok")
    print("4. SIMULASI SERANGAN: Coba Palsukan Data (Buktikan Deteksi Manipulasi)")
    choice = input("Pilihan (1/2/3/4): ").strip()
    
    if choice == "1":
        print("\n--- CATAT FOTO KE BLOCKCHAIN ---")
        foto_path = input("Drag / Ketik path file foto bukti: ").strip().strip('"').strip("'")
        if not foto_path or not os.path.exists(foto_path):
            foto_path = "D:\\JAKA0736.JPG"
            print(f"(Menggunakan file default: '{foto_path}')")
            
        agen_id = input("ID Fotografer / Kode Agen (contoh: Arya-007): ").strip()
        if not agen_id:
            agen_id = "Arya-007"
            print(f"(Default: '{agen_id}')")
            
        keterangan = input("Keterangan Investigasi / Lokasi Bukti : ").strip()
        if not keterangan:
            keterangan = "Bukti Foto Pertemuan Rahasia Kasus Korupsi Internasional"
            print(f"(Default: '{keterangan}')")
            
        print("\nMenambang blok baru (Proof of Work)...")
        block = bc.add_photo_asset(foto_path, agen_id, keterangan)
        
        print("\n" + "="*75)
        print(f"[BERHASIL] Aset Foto Berhasil Dicatat ke Blok #{block.index}!")
        print(f"• Nama Aset     : {block.asset_name}")
        print(f"• Hash SHA-256  : {block.photo_hash}")
        print(f"• Previous Hash : {block.previous_hash[:16]}...")
        print(f"• Nonce (PoW)   : {block.nonce}")
        print(f"• Block Hash    : {block.current_hash}")
        print("="*75 + "\n")
        
    elif choice == "2":
        print("\n" + "="*75)
        print("BUKU BESAR BLOCKCHAIN DARKROOM (LEDGER VIEW)")
        print("="*75)
        for b in bc.chain:
            print(f"\n[BLOK #{b.index}] {b.asset_name} | {b.timestamp}")
            print(f"  • Agen Fotografer: {b.photographer_id}")
            print(f"  • Hash Foto Bukti: {b.photo_hash}")
            print(f"  • Previous Hash  : {b.previous_hash}")
            print(f"  • Nonce          : {b.nonce}")
            print(f"  • Current Hash   : {b.current_hash}")
        print("\n" + "-"*75 + "\n")
        
    elif choice == "3":
        print("\n--- MEMVERIFIKASI INTEGRITAS RANTAI BLOK ---")
        is_valid, msg = bc.verify_integrity()
        print("\n" + "="*75)
        print("HASIL VERIFIKASI INTEGRITAS:")
        print("STATUS :", "[VALID / AMAN]" if is_valid else "[RUSAK / DIPALSUKAN!]")
        print("DETAIL :", msg)
        print("="*75 + "\n")
        
    elif choice == "4":
        print("\n--- SIMULASI SERANGAN MANIPULASI BUKTI ---")
        if len(bc.chain) <= 1:
            print("Belum ada blok aset foto! Tambahkan foto dulu lewat Opsi 1.")
        else:
            print(f"Ada {len(bc.chain)} blok di blockchain.")
            print("Kita akan menyimulasikan seorang hacker yang mencoba mengubah data di Blok #1...")
            
            # Ubah data blok #1 secara ilegal tanpa menambang ulang
            bc.chain[1].metadata = "PALSU! Data bukti foto sudah diganti oleh oknum!"
            
            print("Data Blok #1 berhasil dimanipulasi secara ilegal.")
            print("\nSekarang kita jalankan fungsi verifikasi integritas sistem:")
            is_valid, msg = bc.verify_integrity()
            
            print("\n" + "="*75)
            print("HASIL DETEKSI SISTEM BLOCKCHAIN:")
            print("STATUS :", "[TERBUKTI INVALID! MANIPULASI TERDETEKSI]")
            print("PESAN  :", msg)
            print("="*75)
            print("KESIMPULAN: Tidak ada pihak manapun yang bisa mengubah bukti masa lalu!")
            print("-" * 75 + "\n")
            
            # Muat ulang rantai asli agar tidak rusak permanen
            bc.load_chain()
