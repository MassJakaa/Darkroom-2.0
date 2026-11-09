"""
=============================================================================
DARKROOM 2.0 - ROOT LAUNCHER FORWARDER
=============================================================================
Menjalankan Darkroom launcher dari root repository atau folder subdirektori.
=============================================================================
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DARKROOM_DIR = os.path.join(ROOT_DIR, "Darkroom")

if __name__ == "__main__":
    target_script = os.path.join(DARKROOM_DIR, "run.py")
    if os.path.exists(target_script):
        import runpy
        sys.path.insert(0, DARKROOM_DIR)
        os.chdir(DARKROOM_DIR)
        runpy.run_path(target_script, run_name="__main__")
    else:
        from app import app
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
