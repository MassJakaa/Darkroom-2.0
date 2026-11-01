"""
=============================================================================
DARKROOM - STANDALONE LAUNCHER
=============================================================================
Menjalankan backend server dan secara otomatis membuka antarmuka Darkroom
dalam mode jendela aplikasi mandiri (PWA / Standalone App Window).
=============================================================================
"""

import os
import sys
import time
import subprocess
import webbrowser

# Tambahkan direktori Darkroom ke sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DARKROOM_DIR = os.path.join(BASE_DIR, "Darkroom")
sys.path.append(DARKROOM_DIR)


def open_browser():
    """Membuka browser otomatis setelah server siap."""
    time.sleep(1.5)
    url = "http://localhost:8000"
    
    # Coba buka dalam mode jendela mandiri (Chrome / Edge --app)
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    
    opened = False
    for p in chrome_paths:
        if os.path.exists(p):
            try:
                subprocess.Popen([p, f"--app={url}"])
                opened = True
                break
            except Exception:
                pass
                
    if not opened:
        webbrowser.open(url)


if __name__ == "__main__":
    import threading
    import uvicorn
    
    print("\n" + "="*70)
    print("      DARKROOM - DIGITAL PHOTO & COVERT CRYPTOGRAPHY SUITE")
    print("="*70)
    print("Memulai server lokal di: http://localhost:8000")
    print("Jendela aplikasi akan terbuka otomatis...")
    print("Tekan Ctrl+C di terminal ini untuk mematikan server.")
    print("="*70 + "\n")
    
    # Jalankan pembuka browser di thread terpisah
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Jalankan FastAPI Server
    from app import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
