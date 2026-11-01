"""
=============================================================================
DARKROOM - BIOMETRIC FACE RECOGNITION CONTROLLER
=============================================================================
Modul ini bertugas melakukan autentikasi biometrik wajah jurnalis/agen
menggunakan webcam laptop secara offline dan real-time.

Teknologi yang Digunakan:
1. OpenCV YuNet: Detektor wajah neural network yang sangat cepat dan akurat.
2. OpenCV SFace: Pengekstrak vektor fitur wajah (128-dimensi).
3. Cosine Similarity: Menghitung persentase kemiripan antara wajah yang
   didaftarkan dengan wajah yang sedang berada di depan kamera.

Konsep Pertahanan Kripto/Keamanan:
- Wajah agen disimpan dalam bentuk representasi matematika (Feature Vector).
- Bukan menyimpan foto mentah secara telanjang, melainkan vektor embedding.
=============================================================================
"""

import os
import cv2
import numpy as np

# Lokasi model neural network bawaan OpenCV Zoo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
YUNET_PATH = os.path.join(MODELS_DIR, "face_detection_yunet.onnx")
SFACE_PATH = os.path.join(MODELS_DIR, "face_recognition_sface.onnx")

# Lokasi penyimpanan vektor fitur wajah agen resmi
STORAGE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "storage"))
FACE_DATA_PATH = os.path.join(STORAGE_DIR, "agent_face_embedding.npy")

# Ambang batas kemiripan (Standar Cosine Similarity SFace: >= 0.363 dianggap orang yang sama)
COSINE_THRESHOLD = 0.363

YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
SFACE_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"


def ensure_models_exist():
    """
    Memastikan bobot neural network OpenCV AI (YuNet & SFace) sudah terunduh di lokal.
    Jika berkas belum ada saat teman melakukan kloning, unduh otomatis dari mirror resmi OpenCV Zoo.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    import urllib.request
    
    if not os.path.exists(YUNET_PATH):
        print(f"\n[AI MODEL] Mengunduh model YuNet Face Detector...")
        urllib.request.urlretrieve(YUNET_URL, YUNET_PATH)
        print("[AI MODEL] Model YuNet siap digunakan.")

    if not os.path.exists(SFACE_PATH):
        print(f"\n[AI MODEL] Mengunduh model SFace Face Recognizer (~38 MB)...")
        urllib.request.urlretrieve(SFACE_URL, SFACE_PATH)
        print("[AI MODEL] Model SFace siap digunakan.\n")


def load_models():
    """
    Memuat model deteksi (YuNet) dan model rekognisi (SFace).
    """
    ensure_models_exist()
    detector = cv2.FaceDetectorYN.create(YUNET_PATH, "", (320, 320), score_threshold=0.8)
    recognizer = cv2.FaceRecognizerSF.create(SFACE_PATH, "")
    return detector, recognizer


def get_face_feature_from_frame(frame, detector, recognizer):
    """
    Mendeteksi wajah dari satu frame gambar dan mengekstrak vektor fitur 128-D.
    Mengembalikan: (feature_vector, face_box) atau (None, None) jika tidak ada wajah.
    """
    h, w, _ = frame.shape
    detector.setInputSize((w, h))
    
    _, faces = detector.detect(frame)
    
    if faces is None or len(faces) == 0:
        return None, None
        
    # Ambil wajah pertama yang paling jelas (faces[0])
    primary_face = faces[0]
    
    # Ratakan dan sejajarkan wajah (Face Alignment)
    aligned_face = recognizer.alignCrop(frame, primary_face)
    
    # Ekstrak 128-dimensional embedding
    feature = recognizer.feature(aligned_face)
    
    # Koordinat kotak wajah [x, y, w, h]
    box = primary_face[0:4].astype(int)
    
    return feature, box


def is_agent_registered():
    """
    Mengecek apakah sudah ada data wajah agen yang tersimpan.
    """
    return os.path.exists(FACE_DATA_PATH)


def register_agent_face(feature_vector):
    """
    Menyimpan embedding wajah agen resmi ke penyimpanan lokal.
    """
    os.makedirs(STORAGE_DIR, exist_ok=True)
    np.save(FACE_DATA_PATH, feature_vector)
    return True, "Data biometrik wajah agen berhasil didaftarkan!"


def compare_faces(current_feature, registered_feature):
    """
    Membandingkan 2 vektor fitur wajah menggunakan Cosine Similarity murni NumPy.
    Rumus: (A dot B) / (||A|| * ||B||)
    Mengembalikan: (is_match: bool, score: float)
    """
    f1 = current_feature.flatten().astype(np.float32)
    f2 = registered_feature.flatten().astype(np.float32)
    
    dot_product = np.dot(f1, f2)
    norm1 = np.linalg.norm(f1)
    norm2 = np.linalg.norm(f2)
    
    if norm1 == 0 or norm2 == 0:
        return False, 0.0
        
    score = float(dot_product / (norm1 * norm2))
    is_match = score >= COSINE_THRESHOLD
    return is_match, score


def capture_and_register():
    """
    Membuka webcam untuk merekam wajah agen dan menyimpannya sebagai kredensial biometrik resmi.
    """
    detector, recognizer = load_models()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        return False, "Tidak dapat mengakses webcam laptop!"
        
    print("\n[KAMERA AKTIF] Posisikan wajahmu di dalam lingkaran/kotak.")
    print("Tekan [SPASI] untuk memotret & mendaftarkan wajahmu.")
    print("Tekan [Q] untuk membatalkan.\n")
    
    saved_successfully = False
    message = "Dibatalkan oleh pengguna."
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Flip horizontal agar seperti cermin
        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()
        
        feature, box = get_face_feature_from_frame(frame, detector, recognizer)
        
        # Gambar kotak visual bidik di sekitar wajah
        if box is not None:
            x, y, w, h = box
            # Kotak hijau jika wajah terdeteksi
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(display_frame, "WAJAH TERDETEKSI: SIAP REKAM", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(display_frame, "Mencari wajah agen...", (30, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            
        cv2.putText(display_frame, "[SPASI] Rekam Wajah | [Q] Keluar", (30, display_frame.shape[0] - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
        cv2.imshow("Darkroom - Pendaftaran Biometrik Wajah", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 32: # Tombol SPASI
            if feature is not None:
                register_agent_face(feature)
                saved_successfully = True
                message = "Wajah kamu berhasil didaftarkan sebagai Agen Resmi!"
                break
            else:
                print(">> Wajah belum terdeteksi jelas! Arahkan wajah ke kamera.")
        elif key == ord('q') or key == ord('Q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    return saved_successfully, message


def capture_and_verify():
    """
    Membuka webcam untuk menguji verifikasi biometrik secara langsung.
    """
    if not is_agent_registered():
        return False, "Belum ada wajah agen yang terdaftar! Daftarkan wajah dulu.", 0.0
        
    registered_feature = np.load(FACE_DATA_PATH)
    detector, recognizer = load_models()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        return False, "Tidak dapat mengakses webcam laptop!", 0.0
        
    print("\n[VERIFIKASI AKTIF] Menatap kamera untuk verifikasi biometrik...")
    print("Tekan [SPASI] untuk memverifikasi wajah.")
    print("Tekan [Q] untuk keluar.\n")
    
    is_verified = False
    score = 0.0
    message = "Verifikasi dibatalkan."
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()
        
        feature, box = get_face_feature_from_frame(frame, detector, recognizer)
        
        if box is not None:
            x, y, w, h = box
            match, current_score = compare_faces(feature, registered_feature)
            
            # Ubah warna kotak tergantung cocok atau tidak
            color = (0, 255, 0) if match else (0, 0, 255)
            status_text = f"AGENT COCOK ({current_score:.2f})" if match else f"ORANG ASING ({current_score:.2f})"
            
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(display_frame, status_text, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        
            if match:
                is_verified = True
                score = current_score
        else:
            cv2.putText(display_frame, "Mencari wajah...", (30, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                        
        cv2.putText(display_frame, "[SPASI] Konfirmasi | [Q] Keluar", (30, display_frame.shape[0] - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
        cv2.imshow("Darkroom - Verifikasi Biometrik Wajah", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 32: # SPASI
            if feature is not None:
                match, current_score = compare_faces(feature, registered_feature)
                score = current_score
                if match:
                    is_verified = True
                    message = f"AKSES DITERIMA! Identitas terkonfirmasi (Skor Kemiripan: {score:.2f})"
                else:
                    is_verified = False
                    message = f"AKSES DITOLAK! Wajah tidak cocok dengan Agen (Skor Kemiripan: {score:.2f})"
                break
            else:
                print(">> Wajah belum terdeteksi jelas.")
        elif key == ord('q') or key == ord('Q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    return is_verified, message, score


# =============================================================================
# DEMO INTERAKTIF DI TERMINAL
# =============================================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("      DARKROOM - PENGUJIAN BIOMETRIK SCAN WAJAH")
    print("="*60)
    
    if not is_agent_registered():
        print("\nStatus: Belum ada wajah terdaftar di sistem.")
        print("Sistem akan membuka webcam untuk mendaftarkan wajahmu sekarang...")
        input("Tekan [ENTER] untuk menyalakan kamera...")
        success, msg = capture_and_register()
        print("\nHasil:", msg)
    else:
        print("\nStatus: Data wajah agen sudah tersimpan di sistem.")
        print("Pilih aksi:")
        print("1. Uji Verifikasi Wajah (Coba kenali wajahmu)")
        print("2. Rekam Ulang Wajah (Perbarui data wajah)")
        choice = input("Pilihan (1/2): ").strip()
        
        if choice == "2":
            success, msg = capture_and_register()
            print("\nHasil:", msg)
        else:
            verified, msg, score = capture_and_verify()
            print("\n" + "="*60)
            print("HASIL VERIFIKASI:")
            print(msg)
            print("="*60 + "\n")
