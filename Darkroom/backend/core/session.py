"""
=============================================================================
DARKROOM 2.0 - SESSION STATE MACHINE & SECURITY FOUNDATION
=============================================================================
Mengelola siklus hidup sesi agen dan menegakkan autorisasi pada tingkat backend.

Status Sesi (State Machine):
1. PHOTOGRAPHY_WORKSPACE : Mode umum default (hanya fitur fotografi aktif).
2. AUTH_PENDING          : Dongle terdeteksi, menunggu biometrik & password.
3. AUTHORIZED_PRIVATE    : Sesi rahasia aktif dengan token kriptografis sah.
4. SESSION_LOCKED        : Sesi dikunci darurat (dongle dicabut / user lock).
=============================================================================
"""

import time
import secrets
from enum import Enum
from typing import Optional, Dict
from fastapi import Header, HTTPException, status, Depends


class SessionState(str, Enum):
    PHOTOGRAPHY_WORKSPACE = "PHOTOGRAPHY_WORKSPACE"
    AUTH_PENDING = "AUTH_PENDING"
    AUTHORIZED_PRIVATE = "AUTHORIZED_PRIVATE"
    SESSION_LOCKED = "SESSION_LOCKED"


class SessionInfo:
    def __init__(self, token: str, username: str = "Agent"):
        self.token = token
        self.username = username
        self.state = SessionState.AUTHORIZED_PRIVATE
        self.created_at = time.time()
        self.last_activity = time.time()
        self.dongle_drive: Optional[str] = None
        self.biometric_score: float = 0.0

    def touch(self):
        self.last_activity = time.time()

    def is_expired(self, max_idle_seconds: int = 3600) -> bool:
        return (time.time() - self.last_activity) > max_idle_seconds


class SessionManager:
    """
    Manajer sesi backend tunggal (in-memory) untuk studio desktop Darkroom.
    """
    def __init__(self):
        self.current_state: SessionState = SessionState.PHOTOGRAPHY_WORKSPACE
        self.active_sessions: Dict[str, SessionInfo] = {}
        self.active_dongle_drive: Optional[str] = None

    def start_pending(self, drive: Optional[str] = None) -> SessionState:
        """Memulai proses otentikasi jika dongle terpasang."""
        self.active_dongle_drive = drive
        self.current_state = SessionState.AUTH_PENDING
        return self.current_state

    def authorize(self, username: str = "Agent", drive: Optional[str] = None, bio_score: float = 1.0) -> str:
        """
        Menerbitkan token sesi baru dan menetapkan status AUTHORIZED_PRIVATE.
        """
        token = secrets.token_hex(32) # 256-bit entropy token
        session = SessionInfo(token=token, username=username)
        session.dongle_drive = drive or self.active_dongle_drive
        session.biometric_score = bio_score

        self.active_sessions[token] = session
        self.current_state = SessionState.AUTHORIZED_PRIVATE
        self.active_dongle_drive = session.dongle_drive
        return token

    def revoke_all(self, reason: str = "Emergency lock / Dongle removed") -> None:
        """
        Panic Switch / Dead Man's Switch:
        Memusnahkan semua sesi aktif di RAM dan mengembalikan ke PHOTOGRAPHY_WORKSPACE.
        """
        self.active_sessions.clear()
        self.active_dongle_drive = None
        self.current_state = SessionState.SESSION_LOCKED

    def reset_to_workspace(self) -> None:
        """Mengembalikan sistem ke mode fotografi biasa."""
        self.active_sessions.clear()
        self.current_state = SessionState.PHOTOGRAPHY_WORKSPACE

    def validate_token(self, token: Optional[str]) -> Optional[SessionInfo]:
        """
        Memeriksa validitas token sesi.
        """
        if not token:
            return None
        session = self.active_sessions.get(token)
        if not session:
            return None
        if session.is_expired():
            del self.active_sessions[token]
            return None
        session.touch()
        return session

    def get_status(self, token: Optional[str] = None) -> dict:
        """Mengecek status terkini sesi untuk frontend."""
        valid_session = self.validate_token(token)
        is_auth = (valid_session is not None) and (self.current_state == SessionState.AUTHORIZED_PRIVATE)

        return {
            "state": self.current_state.value,
            "is_authorized": is_auth,
            "username": valid_session.username if valid_session else None,
            "dongle_drive": self.active_dongle_drive,
            "active_sessions_count": len(self.active_sessions)
        }


# Instansiasi global session manager
session_manager = SessionManager()


# =============================================================================
# DEPENDENCIES UNTUK FASTAPI ROUTE PROTECTION
# =============================================================================

def extract_token_from_headers(
    authorization: Optional[str] = Header(None),
    x_session_token: Optional[str] = Header(None)
) -> Optional[str]:
    """Ekstraksi token dari Authorization: Bearer <token> atau X-Session-Token."""
    if x_session_token:
        return x_session_token.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def require_private_session(
    token: Optional[str] = Depends(extract_token_from_headers)
) -> SessionInfo:
    """
    FastAPI Dependency:
    Memastikan bahwa pemanggil endpoint memiliki sesi AUTHORIZED_PRIVATE yang sah.
    Jika token tidak ada, tidak valid, atau sesi telah dicabut (Dead Man's Switch),
    maka sistem seketika melempar HTTP 401 Unauthorized.
    """
    # 1. Periksa validitas token di SessionManager
    session = session_manager.validate_token(token)
    if not session or session_manager.current_state != SessionState.AUTHORIZED_PRIVATE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Akses ditolak: Operasi kriptografi membutuhkan sesi terotorisasi (Authorized Private Session)."
        )

    # 2. Verifikasi fisik dongle secara real-time
    from backend.hardware.dongle import verify_dongle
    dongle_valid, _, _ = verify_dongle()
    if not dongle_valid:
        # Jika media fisik dicabut, batalkan seluruh sesi seketika!
        session_manager.revoke_all(reason="Dongle fisik dicabut saat eksekusi endpoint terproteksi.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses dicabut: Media hardware dongle telah dicabut dari perangkat!"
        )

    return session
