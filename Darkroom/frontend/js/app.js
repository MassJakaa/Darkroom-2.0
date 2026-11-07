/**
 * ==============================================================================
 * DARKROOM 2.0 - PROFESSIONAL PHOTOGRAPHY & INTEGRATED COVERT SUITE
 * ==============================================================================
 * 5 Lightroom Workspaces:
 * 1. Library     : Katalog aset, filter, metadata teknis, manajemen berkas.
 * 2. Develop     : Sliders Light & Tone, Temperature/Tint, Transforms, Before/After.
 * 3. Transfer    : 2-Panel Outgoing/Incoming Stego V2, binary capacity meter, AEAD.
 * 4. Export      : Format JPEG/PNG/TIFF, scaling resolusi, kontrol kualitas.
 * 5. Preferences : Security foundation, session state machine, dongle, blockchain.
 * ==============================================================================
 */

// STATE TERPUSAT APLIKASI
const appState = {
    appMode: "lightroom",                  // "lightroom" (Kamuflase Publik) | "darkroom" (Covert Studio)
    sessionState: "PHOTOGRAPHY_WORKSPACE", // PHOTOGRAPHY_WORKSPACE | AUTHORIZED_PRIVATE | SESSION_LOCKED
    sessionToken: null,
    username: "Guest",

    catalog: [],              // Daftar semua foto di storage/catalog
    activePhoto: null,        // Foto yang dipilih saat ini di Develop/Global
    activeImg: null,          // Objek Image HTML asli untuk kanvas
    
    // Develop Tone & Transform Filters
    filters: {
        brightness: 0,
        contrast: 0,
        highlights: 0,
        shadows: 0,
        temperature: 0,       // Kelvin offset (-50 to +50)
        tint: 0,              // Green-Magenta (-50 to +50)
        saturation: 0,
        sepia: 0,
        rotation: 0,          // 0, 90, 180, 270 derajat
        flipH: false,
        flipV: false
    },
    isSplitView: false,       // Mode komparasi Sebelum / Sesudah

    // Transfer State
    transferCover: null,      // Foto cover terpilih di Transfer
    transferCapacity: null,   // Data kalkulasi kapasitas cover
    outgoingPayloadType: "TEXT", // TEXT | FILE | IMAGE
    
    // Export State
    exportFormat: "JPEG",
    exportScale: 100,
    exportQuality: 92
};

let renameTargetFilename = null;
let pendingAuthCallback = null;
// # FIX: integrasi biometrik wajib
let authBioStream = null;
let authBiometricImageBase64 = null;
let authBiometricMatch = false;

// ==============================================================================
// 1. DOM READY & INITIALIZATION
// ==============================================================================
document.addEventListener("DOMContentLoaded", () => {
    initModeSwitcher();
    initWorkspaceNavigation();
    initSessionManager();
    initLibraryWorkspace();
    initDevelopWorkspace();
    initTransferWorkspace();
    initDecryptWorkspace();
    initExportWorkspace();
    initPreferencesWorkspace();
    initRenameModal();
    initAuthModal();
    initPanicLock();

    // Muat data awal
    loadCatalog();
    checkSessionStatus();
    setInterval(checkSessionStatus, 3000); // Polling hardware dongle & session state
});

// ==============================================================================
// 1.5. MODE SWITCHER: LIGHTROOM (KAMUFLASE) <-> DARKROOM (COVERT STUDIO)
// ==============================================================================
function initModeSwitcher() {
    const btnToggleMode = document.getElementById("btn-toggle-app-mode");
    if (btnToggleMode) {
        btnToggleMode.addEventListener("click", () => {
            toggleAppMode();
        });
    }

    // Set status awal sesuai appState.appMode
    toggleAppMode(appState.appMode);
}

async function toggleAppMode(targetMode) {
    const newMode = targetMode || (appState.appMode === "lightroom" ? "darkroom" : "lightroom");
    appState.appMode = newMode;

    const brandName = document.getElementById("app-brand-name");
    const brandSub = document.getElementById("app-brand-sub");
    const brandBadge = document.getElementById("app-brand-badge");
    const modeText = document.getElementById("mode-text-label");

    if (newMode === "darkroom") {
        document.body.className = "mode-darkroom";
        document.title = "Darkroom 2.0 - Studio Fotografi & Covert Suite";
        if (brandName) brandName.textContent = "Darkroom";
        if (brandSub) brandSub.textContent = "Covert Studio 2.0";
        if (brandBadge) brandBadge.textContent = "Dk";
        if (modeText) modeText.textContent = "Mode: Darkroom";

        // # FIX: penyesuaian payload & state
        // Mode hanya mengganti tampilan; operasi privat meminta autentikasi lewat modal.
    } else {
        // Mode: Lightroom (Kamuflase Publik)
        document.body.className = "mode-lightroom";
        document.title = "Adobe Lightroom - Digital Photography Suite";
        if (brandName) brandName.textContent = "Adobe Lightroom";
        if (brandSub) brandSub.textContent = "Develop Studio";
        if (brandBadge) brandBadge.textContent = "Lr";
        if (modeText) modeText.textContent = "Mode: Lightroom";

        // Jika pengguna sedang berada di view covert (transfer, decrypt, preferences),
        // alihkan seketika ke view-develop untuk menjaga kamuflase
        const currentActiveView = document.querySelector(".app-view.active");
        if (currentActiveView && (currentActiveView.id === "view-transfer" || currentActiveView.id === "view-decrypt" || currentActiveView.id === "view-preferences")) {
            switchWorkspace("view-develop");
        }
    }
}

// ==============================================================================
// 2. WORKSPACE NAVIGATION (5 RUANG KERJA UTAMA)
// ==============================================================================
function initWorkspaceNavigation() {
    const navBtns = document.querySelectorAll(".sidebar-tab-btn");
    const views = document.querySelectorAll(".app-view");

    navBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetViewId = btn.getAttribute("data-view");
            switchWorkspace(targetViewId);
        });
    });

    // Badge status sesi di sidebar bisa diklik untuk buka Preferences
    const sessionBadge = document.getElementById("sidebar-session-badge");
    if (sessionBadge) {
        sessionBadge.addEventListener("click", () => {
            switchWorkspace("view-preferences");
        });
    }

    // Tombol Cepat dari Develop ke Export
    const btnQuickExport = document.getElementById("btn-quick-goto-export");
    if (btnQuickExport) {
        btnQuickExport.addEventListener("click", () => {
            switchWorkspace("view-export");
        });
    }
}

function switchWorkspace(targetViewId) {
    // Keamanan Mode: Cegah membuka ruang kerja rahasia jika berada dalam Mode Lightroom
    if (appState.appMode === "lightroom" && (targetViewId === "view-transfer" || targetViewId === "view-decrypt" || targetViewId === "view-preferences")) {
        console.warn(`Akses ke '${targetViewId}' diblokir: Ruang kerja kriptografi hanya dapat diakses dalam Mode Darkroom.`);
        targetViewId = "view-develop";
    }

    const navBtns = document.querySelectorAll(".sidebar-tab-btn");
    const views = document.querySelectorAll(".app-view");

    navBtns.forEach(b => {
        if (b.getAttribute("data-view") === targetViewId) {
            b.classList.add("active");
        } else {
            b.classList.remove("active");
        }
    });

    views.forEach(v => {
        if (v.id === targetViewId) {
            v.style.display = "flex";
            v.classList.add("active");
        } else {
            v.style.display = "none";
            v.classList.remove("active");
        }
    });

    // Trigger update view spesifik saat dibuka
    if (targetViewId === "view-library") {
        renderLibraryGrid();
    } else if (targetViewId === "view-export") {
        updateExportPreview();
    } else if (targetViewId === "view-preferences") {
        loadBlockchain();
        checkBiometricStatus();
    } else if (targetViewId === "view-transfer") {
        syncTransferCover();
    } else if (targetViewId === "view-decrypt") {
        populateDecryptCatalog();
    }
}

// ==============================================================================
// 3. SECURITY FOUNDATION & SESSION STATE MACHINE
// ==============================================================================
function initSessionManager() {
    // Tombol Buka Kunci di Preferences
    const btnPrefUnlock = document.getElementById("btn-pref-do-unlock");
    if (btnPrefUnlock) {
        btnPrefUnlock.addEventListener("click", async () => {
            const pwdInput = document.getElementById("pref-unlock-password");
            const pwd = pwdInput ? pwdInput.value.trim() : "";
            if (!pwd) {
                alert("Masukkan password admin!");
                return;
            }
            const imageBase64 = captureFrameBase64();
            if (!imageBase64) {
                alert("Aktifkan kamera dan pindai wajah sebelum membuka sesi privat!");
                if (pwdInput) pwdInput.value = "";
                return;
            }
            try {
                const biometric = await verifyBiometricImage(imageBase64);
                if (biometric.is_match !== true) {
                    throw new Error(biometric.message || "Wajah tidak cocok.");
                }
                await executeUnlock(pwd, imageBase64, biometric.is_match);
            } catch (err) {
                alert("Autentikasi biometrik gagal: " + err.message);
            } finally {
                if (pwdInput) pwdInput.value = "";
            }
        });
    }

    // Tombol Kunci Kembali di Preferences
    const btnPrefLock = document.getElementById("btn-pref-lock-session");
    if (btnPrefLock) {
        btnPrefLock.addEventListener("click", executeLock);
    }
}

async function checkSessionStatus() {
    try {
        const headers = {};
        if (appState.sessionToken) {
            headers["Authorization"] = `Bearer ${appState.sessionToken}`;
        }

        const res = await fetch("/api/session/status", { headers });
        const data = await res.json();

        // # FIX: penyesuaian payload & state
        const isAuthorized =
            data.state === "AUTHORIZED_PRIVATE" &&
            data.is_authorized === true;

        appState.sessionState = isAuthorized
            ? data.state
            : data.state === "SESSION_LOCKED"
                ? data.state
                : "PHOTOGRAPHY_WORKSPACE";

        // Update indikator dongle di sidebar & preferences
        const dongleIndicator = document.getElementById("dongle-indicator");
        const dongleText = document.getElementById("dongle-status-text");
        const prefDongleDrive = document.getElementById("pref-dongle-drive");
        const prefDongleMsg = document.getElementById("pref-dongle-msg");

        if (data.dongle_valid) {
            if (dongleIndicator) dongleIndicator.classList.add("dongle-active");
            if (dongleText) dongleText.innerHTML = `<strong>${data.dongle_drive || "SD"}</strong> Kunci SD`;
            if (prefDongleDrive) prefDongleDrive.textContent = `${data.dongle_drive || "Virtual Drive"} (Terpasang)`;
            if (prefDongleMsg) prefDongleMsg.textContent = data.dongle_message || "darkroom.key valid";
        } else {
            if (dongleIndicator) dongleIndicator.classList.remove("dongle-active");
            if (dongleText) dongleText.textContent = "SD Reader";
            if (prefDongleDrive) prefDongleDrive.textContent = "Tidak Terdeteksi";
            if (prefDongleMsg) prefDongleMsg.textContent = data.dongle_message || "Menunggu SD Card";
        }

        // Update badge sesi di sidebar
        const sessionDot = document.getElementById("session-dot");
        const sessionLabel = document.getElementById("session-mode-label");
        const sessionIcon = document.getElementById("session-lock-icon");
        const prefStateBadge = document.getElementById("pref-state-badge");
        const prefUnlockBox = document.getElementById("pref-unlock-box");
        const prefAuthBox = document.getElementById("pref-authorized-box");
        const prefAuthUser = document.getElementById("pref-auth-user");

        if (isAuthorized) {
            if (sessionDot) sessionDot.className = "status-dot dot-authorized";
            if (sessionLabel) sessionLabel.textContent = "Sesi: Privat Aktif";
            if (sessionIcon) sessionIcon.className = "fa-solid fa-lock-open";
            if (prefStateBadge) {
                prefStateBadge.className = "state-pill state-authorized";
                prefStateBadge.textContent = "AUTHORIZED_PRIVATE";
            }
            if (prefUnlockBox) prefUnlockBox.style.display = "none";
            if (prefAuthBox) prefAuthBox.style.display = "block";
            if (prefAuthUser) prefAuthUser.textContent = data.username || "Agent";
        } else if (data.state === "SESSION_LOCKED") {
            appState.sessionToken = null;
            if (sessionDot) sessionDot.className = "status-dot dot-locked";
            if (sessionLabel) sessionLabel.textContent = "Sesi: TERKUNCI";
            if (sessionIcon) sessionIcon.className = "fa-solid fa-lock";
            if (prefStateBadge) {
                prefStateBadge.className = "state-pill state-locked";
                prefStateBadge.textContent = "SESSION_LOCKED (Panic)";
            }
            if (prefUnlockBox) prefUnlockBox.style.display = "block";
            if (prefAuthBox) prefAuthBox.style.display = "none";
        } else {
            // PHOTOGRAPHY_WORKSPACE
            appState.sessionToken = null;
            if (sessionDot) sessionDot.className = "status-dot dot-public";
            if (sessionLabel) sessionLabel.textContent = "Mode: Fotografi";
            if (sessionIcon) sessionIcon.className = "fa-solid fa-lock";
            if (prefStateBadge) {
                prefStateBadge.className = "state-pill state-public";
                prefStateBadge.textContent = "PHOTOGRAPHY_WORKSPACE";
            }
            if (prefUnlockBox) prefUnlockBox.style.display = "block";
            if (prefAuthBox) prefAuthBox.style.display = "none";
        }
    } catch (err) {
        console.warn("Gagal mengecek status sesi:", err);
    }
}

async function verifyBiometricImage(imageBase64) {
    if (!imageBase64) throw new Error("Pindai wajah terlebih dahulu.");
    const res = await fetch("/api/auth/biometric/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_base64: imageBase64 })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.message || "Verifikasi wajah gagal!");
    return data;
}

// # FIX: integrasi biometrik wajib
async function executeUnlock(password, imageBase64, isMatch) {
    if (!imageBase64 || isMatch !== true) {
        alert("Password dan hasil scan wajah yang cocok wajib diisi untuk membuka sesi privat.");
        return false;
    }
    try {
        const res = await fetch("/api/session/unlock", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                password: password,
                is_match: isMatch,
                image_base64: imageBase64
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Otorisasi gagal!");

        appState.sessionToken = data.token;
        appState.username = data.username;
        appState.sessionState = "AUTHORIZED_PRIVATE";

        await checkSessionStatus();
        alert(`🔓 SESI PRIVAT DIAKTIFKAN!\nSelamat datang, ${data.username}. Ruang kerja Transfer dan fitur kriptografi sekarang dapat digunakan.`);
        return true;
    } catch (err) {
        alert("Autentikasi Gagal: " + err.message);
        return false;
    }
}

async function executeLock() {
    try {
        const headers = {};
        if (appState.sessionToken) {
            headers["Authorization"] = `Bearer ${appState.sessionToken}`;
        }
        await fetch("/api/session/lock?reason=Kunci%20Manual%20Pengguna", {
            method: "POST",
            headers
        });
        appState.sessionToken = null;
        appState.sessionState = "PHOTOGRAPHY_WORKSPACE";
        await checkSessionStatus();
        alert("🔒 Sesi privat ditutup. Aplikasi kembali ke Mode Fotografi.");
    } catch (err) {
        console.error("Gagal mengunci sesi:", err);
    }
}

function initPanicLock() {
    const handlePanic = async () => {
        const ok = confirm("🚨 AKTIFKAN PANIC LOCK DARURAT?\nSeluruh token otorisasi akan dicabut dan sesi privat dikunci seketika!");
        if (!ok) return;

        try {
            const headers = {};
            if (appState.sessionToken) {
                headers["Authorization"] = `Bearer ${appState.sessionToken}`;
            }
            await fetch("/api/session/lock?reason=Emergency%20Panic%20Lock", {
                method: "POST",
                headers
            });
            appState.sessionToken = null;
            appState.sessionState = "SESSION_LOCKED";
            await checkSessionStatus();
            await toggleAppMode("lightroom");
            alert("🚨 EMERGENCY PANIC LOCK DIAKTIFKAN!\nSesi privat telah dicabut dan aplikasi berada dalam mode kamuflase Lightroom.");
            switchWorkspace("view-develop");
        } catch (err) {
            alert("Error panic lock: " + err.message);
        }
    };

    const sidePanic = document.getElementById("sidebar-panic-btn");
    const prefPanic = document.getElementById("btn-pref-panic");
    if (sidePanic) sidePanic.addEventListener("click", handlePanic);
    if (prefPanic) prefPanic.addEventListener("click", handlePanic);
}

function ensurePrivateSession(actionCallback) {
    if (appState.sessionState === "AUTHORIZED_PRIVATE" && appState.sessionToken) {
        actionCallback();
        return;
    }
    // Jika belum terotorisasi, munculkan modal otorisasi
    pendingAuthCallback = actionCallback;
    openAuthModal();
}

// ==============================================================================
// 4. WORKSPACE 1: LIBRARY (KATALOG & ASSET MANAGEMENT)
// ==============================================================================
function initLibraryWorkspace() {
    const searchInput = document.getElementById("library-search-input");
    const filterChips = document.querySelectorAll(".filter-chip");
    const importInput = document.getElementById("library-import-input");

    if (searchInput) {
        searchInput.addEventListener("input", () => renderLibraryGrid());
    }

    filterChips.forEach(chip => {
        chip.addEventListener("click", () => {
            filterChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            renderLibraryGrid();
        });
    });

    if (importInput) {
        importInput.addEventListener("change", handleImportPhotos);
    }

    // Detail Panel Actions
    const btnOpenDevelop = document.getElementById("btn-lib-open-develop");
    const btnUseTransfer = document.getElementById("btn-lib-use-transfer");
    const btnRename = document.getElementById("btn-lib-rename");
    const btnDelete = document.getElementById("btn-lib-delete");

    if (btnOpenDevelop) {
        btnOpenDevelop.addEventListener("click", () => {
            if (appState.activePhoto) {
                switchWorkspace("view-develop");
                selectPhoto(appState.activePhoto);
            }
        });
    }

    if (btnUseTransfer) {
        btnUseTransfer.addEventListener("click", () => {
            if (appState.activePhoto) {
                setTransferCover(appState.activePhoto);
                switchWorkspace("view-transfer");
            }
        });
    }

    if (btnRename) {
        btnRename.addEventListener("click", () => {
            if (appState.activePhoto) openRenameModal(appState.activePhoto.filename);
        });
    }

    if (btnDelete) {
        btnDelete.addEventListener("click", () => {
            if (appState.activePhoto) deletePhotoPrompt(appState.activePhoto.filename);
        });
    }

    const btnLibLock = document.getElementById("btn-lib-toggle-lock");
    if (btnLibLock) {
        btnLibLock.addEventListener("click", () => {
            if (!appState.activePhoto) return;
            const pass = prompt(
                appState.activePhoto.is_locked 
                    ? `Masukkan passphrase ChaCha20 untuk membuka "${appState.activePhoto.filename}":`
                    : `Masukkan passphrase ChaCha20 untuk mengunci "${appState.activePhoto.filename}":`,
                "BrankasDarkroom2026!"
            );
            if (pass !== null) {
                if (appState.activePhoto.is_locked) {
                    executeUnlockPhotoFile(appState.activePhoto.filename, pass.trim());
                } else {
                    executeLockPhotoFile(appState.activePhoto.filename, pass.trim());
                }
            }
        });
    }
}

function renderLibraryGrid() {
    const grid = document.getElementById("library-grid");
    if (!grid) return;

    const searchVal = (document.getElementById("library-search-input")?.value || "").toLowerCase().trim();
    const activeChip = document.querySelector(".filter-chip.active");
    const filterType = activeChip ? activeChip.getAttribute("data-filter") : "all";

    grid.innerHTML = "";

    const filtered = appState.catalog.filter(p => {
        // Filter nama berkas
        if (searchVal && !p.filename.toLowerCase().includes(searchVal)) return false;

        // Filter tipe
        if (filterType === "locked") return p.is_locked;
        if (filterType === "unlocked") return !p.is_locked;
        if (filterType === "stego") return p.filename.startsWith("STEGO_") || p.filename.startsWith("DECOY_");
        return true;
    });

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 48px; color: var(--text-muted);">
                <i class="fa-solid fa-folder-open" style="font-size: 38px; margin-bottom: 12px; color: #333;"></i>
                <p>Tidak ada foto yang cocok dengan pencarian atau filter.</p>
            </div>
        `;
        return;
    }

    filtered.forEach(photo => {
        const card = document.createElement("div");
        card.className = "lib-photo-card";
        if (appState.activePhoto && appState.activePhoto.filename === photo.filename) {
            card.classList.add("selected");
        }

        let badgeHtml = `<span class="lib-card-badge badge-normal">NORMAL</span>`;
        if (photo.is_locked) {
            badgeHtml = `<span class="lib-card-badge badge-locked">LOCKED</span>`;
        } else if (photo.filename.startsWith("STEGO_") || photo.filename.startsWith("DECOY_")) {
            badgeHtml = `<span class="lib-card-badge badge-stego">STEGO</span>`;
        }

        card.innerHTML = `
            <div class="lib-card-thumb-wrap">
                <img src="${photo.url}" class="lib-card-thumb" alt="${photo.filename}">
                ${badgeHtml}
            </div>
            <div class="lib-card-meta">
                <span class="lib-card-name" title="${photo.filename}">${photo.filename}</span>
                <span class="lib-card-sub">${photo.size_mb} MB • ${photo.dimensions || "Foto"}</span>
            </div>
        `;

        card.addEventListener("click", () => {
            selectLibraryPhoto(photo);
        });

        // Double click langsung buka di develop
        card.addEventListener("dblclick", () => {
            selectPhoto(photo);
            switchWorkspace("view-develop");
        });

        grid.appendChild(card);
    });
}

function selectLibraryPhoto(photo) {
    appState.activePhoto = photo;
    document.querySelectorAll(".lib-photo-card").forEach(c => c.classList.remove("selected"));
    renderLibraryGrid();

    // Update detail panel
    const detailImg = document.getElementById("library-detail-img");
    const detailEmpty = document.getElementById("library-detail-empty");
    const detailInfo = document.getElementById("library-detail-info");
    const detailActions = document.getElementById("library-detail-actions");

    if (detailImg) {
        detailImg.src = photo.url;
        detailImg.style.display = "block";
    }
    if (detailEmpty) detailEmpty.style.display = "none";
    if (detailInfo) detailInfo.style.display = "flex";
    if (detailActions) detailActions.style.display = "flex";

    document.getElementById("lib-meta-filename").textContent = photo.filename;
    document.getElementById("lib-meta-filesize").textContent = `${photo.size_mb} MB`;
    document.getElementById("lib-meta-status").textContent = photo.is_locked ? "Terkunci (.enc)" : "Normal";
    document.getElementById("lib-meta-path").textContent = `storage/catalog/${photo.filename}`;

    const btnLibLock = document.getElementById("btn-lib-toggle-lock");
    if (btnLibLock) {
        if (photo.is_locked) {
            btnLibLock.innerHTML = `<i class="fa-solid fa-lock-open"></i> Buka Kunci (.enc)`;
        } else {
            btnLibLock.innerHTML = `<i class="fa-solid fa-file-shield"></i> Kunci Berkas (.enc)`;
        }
    }
}

// ==============================================================================
// 5. WORKSPACE 2: DEVELOP / STUDIO EDITOR (PENGEMBANGAN FOTO)
// ==============================================================================
function initDevelopWorkspace() {
    const sBrightness = document.getElementById("slider-brightness");
    const sContrast = document.getElementById("slider-contrast");
    const sHighlights = document.getElementById("slider-highlights");
    const sShadows = document.getElementById("slider-shadows");
    const sTemperature = document.getElementById("slider-temperature");
    const sTint = document.getElementById("slider-tint");
    const sSaturation = document.getElementById("slider-saturation");
    const sSepia = document.getElementById("slider-sepia");

    const btnReset = document.getElementById("btn-reset-develop");
    const btnToggleSplit = document.getElementById("btn-toggle-split");

    const updateFilters = () => {
        appState.filters.brightness = parseInt(sBrightness?.value || 0);
        appState.filters.contrast = parseInt(sContrast?.value || 0);
        appState.filters.highlights = parseInt(sHighlights?.value || 0);
        appState.filters.shadows = parseInt(sShadows?.value || 0);
        appState.filters.temperature = parseInt(sTemperature?.value || 0);
        appState.filters.tint = parseInt(sTint?.value || 0);
        appState.filters.saturation = parseInt(sSaturation?.value || 0);
        appState.filters.sepia = parseInt(sSepia?.value || 0);

        // Update teks label slider
        document.getElementById("val-brightness").textContent = (appState.filters.brightness >= 0 ? "+" : "") + (appState.filters.brightness / 100).toFixed(2);
        document.getElementById("val-contrast").textContent = (appState.filters.contrast >= 0 ? "+" : "") + appState.filters.contrast;
        document.getElementById("val-highlights").textContent = (appState.filters.highlights >= 0 ? "+" : "") + appState.filters.highlights;
        document.getElementById("val-shadows").textContent = (appState.filters.shadows >= 0 ? "+" : "") + appState.filters.shadows;
        document.getElementById("val-temperature").textContent = `${5500 + (appState.filters.temperature * 50)} K`;
        document.getElementById("val-tint").textContent = (appState.filters.tint >= 0 ? "+" : "") + appState.filters.tint;
        document.getElementById("val-saturation").textContent = (appState.filters.saturation >= 0 ? "+" : "") + appState.filters.saturation;
        document.getElementById("val-sepia").textContent = appState.filters.sepia + "%";

        renderCanvas();
    };

    [sBrightness, sContrast, sHighlights, sShadows, sTemperature, sTint, sSaturation, sSepia].forEach(slider => {
        if (slider) slider.addEventListener("input", updateFilters);
    });

    // Presets fotografi
    document.querySelectorAll(".presets-bar .chip").forEach(chip => {
        chip.addEventListener("click", () => {
            document.querySelectorAll(".presets-bar .chip").forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            applyDevelopPreset(chip.getAttribute("data-preset"));
            updateFilters();
        });
    });

    // Reset Sliders & Transforms
    if (btnReset) {
        btnReset.addEventListener("click", () => {
            resetDevelopTuning();
            updateFilters();
        });
    }

    // Toggle Before / After Split View
    if (btnToggleSplit) {
        btnToggleSplit.addEventListener("click", () => {
            appState.isSplitView = !appState.isSplitView;
            btnToggleSplit.classList.toggle("active", appState.isSplitView);
            const beforeCanvas = document.getElementById("before-canvas");
            if (beforeCanvas) {
                beforeCanvas.style.display = appState.isSplitView ? "block" : "none";
            }
            renderCanvas();
        });
    }

    // Transform buttons (Rotate CCW, CW, Flip H, Flip V)
    document.getElementById("btn-rotate-ccw")?.addEventListener("click", () => {
        appState.filters.rotation = (appState.filters.rotation - 90 + 360) % 360;
        renderCanvas();
    });
    document.getElementById("btn-rotate-cw")?.addEventListener("click", () => {
        appState.filters.rotation = (appState.filters.rotation + 90) % 360;
        renderCanvas();
    });
    document.getElementById("btn-flip-h")?.addEventListener("click", () => {
        appState.filters.flipH = !appState.filters.flipH;
        renderCanvas();
    });
    document.getElementById("btn-flip-v")?.addEventListener("click", () => {
        appState.filters.flipV = !appState.filters.flipV;
        renderCanvas();
    });

    // Header buttons (Rename & Delete active photo)
    document.getElementById("btn-rename-active-photo")?.addEventListener("click", () => {
        if (appState.activePhoto) openRenameModal(appState.activePhoto.filename);
    });
    document.getElementById("btn-delete-active-photo")?.addEventListener("click", () => {
        if (appState.activePhoto) deletePhotoPrompt(appState.activePhoto.filename);
    });

    // File Lock (ChaCha20-Poly1305) & Blockchain Sealing
    const btnLockActive = document.getElementById("btn-lock-active-file");
    const btnSealBlockchain = document.getElementById("btn-seal-active-blockchain");

    if (btnLockActive) {
        btnLockActive.addEventListener("click", () => {
            if (!appState.activePhoto) {
                alert("Pilih foto terlebih dahulu!");
                return;
            }
            const pass = document.getElementById("input-lock-passphrase")?.value.trim() || "BrankasDarkroom2026!";
            if (appState.activePhoto.is_locked) {
                executeUnlockPhotoFile(appState.activePhoto.filename, pass);
            } else {
                executeLockPhotoFile(appState.activePhoto.filename, pass);
            }
        });
    }

    if (btnSealBlockchain) {
        btnSealBlockchain.addEventListener("click", async () => {
            if (!appState.activePhoto || appState.activePhoto.is_locked) {
                alert("Pilih foto yang aktif dan tidak terkunci terlebih dahulu!");
                return;
            }
            btnSealBlockchain.disabled = true;
            btnSealBlockchain.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Menambang Bukti PoW...`;

            try {
                const headers = {};
                if (appState.sessionToken) {
                    headers["Authorization"] = `Bearer ${appState.sessionToken}`;
                }
                const formData = new FormData();
                formData.append("filename", appState.activePhoto.filename);
                formData.append("agent_id", appState.username || "Agent");
                formData.append("notes", "Bukti foto otentik diverifikasi di Darkroom Studio");

                const res = await fetch("/api/blockchain/seal", {
                    method: "POST",
                    headers,
                    body: formData
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Gagal menyegel ke blockchain!");

                const blk = data.block;
                alert(`⛓️ BLOK BERHASIL DITAMBANG!\n\nIndex: #${blk.index}\nSHA-256 Hash: ${blk.current_hash.slice(0, 20)}...\nNonce PoW: ${blk.nonce}\nTimestamp: ${blk.timestamp}\n\nBukti telah tercatat permanen di Buku Besar Blockchain.`);
            } catch (err) {
                alert("Error Blockchain: " + err.message);
            } finally {
                btnSealBlockchain.disabled = false;
                btnSealBlockchain.innerHTML = `<i class="fa-solid fa-cube"></i> Catat Hash ke Blockchain`;
            }
        });
    }
}

async function executeLockPhotoFile(filename, passphrase) {
    if (!passphrase) {
        alert("Passphrase ChaCha20 wajib diisi!");
        return;
    }
    try {
        const headers = {};
        if (appState.sessionToken) {
            headers["Authorization"] = `Bearer ${appState.sessionToken}`;
        }
        const formData = new FormData();
        formData.append("filename", filename);
        formData.append("passphrase", passphrase);

        const res = await fetch("/api/vault/lock-photo", {
            method: "POST",
            headers,
            body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Gagal mengunci berkas!");

        alert(`🔒 BERKAS DIKUNCI!\nBerkas "${data.locked_filename}" berhasil dienkripsi dengan ChaCha20-Poly1305. File asli telah diamankan dari disk.`);
        await loadCatalog();
    } catch (err) {
        alert("Gagal mengunci: " + err.message);
    }
}

async function executeUnlockPhotoFile(filename, passphrase) {
    if (!passphrase) {
        alert("Passphrase ChaCha20 wajib diisi!");
        return;
    }
    try {
        const headers = {};
        if (appState.sessionToken) {
            headers["Authorization"] = `Bearer ${appState.sessionToken}`;
        }
        const formData = new FormData();
        formData.append("filename", filename);
        formData.append("passphrase", passphrase);

        const res = await fetch("/api/vault/unlock-photo", {
            method: "POST",
            headers,
            body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Gagal membuka kunci!");

        alert(`🔓 BERKAS DIPULIHKAN!\nBerkas "${data.unlocked_filename}" berhasil didekripsi dan diverifikasi dengan tag otentikasi Poly1305.`);
        await loadCatalog();
    } catch (err) {
        alert("Gagal membuka kunci: " + err.message);
    }
}

function applyDevelopPreset(presetName) {
    const sBrightness = document.getElementById("slider-brightness");
    const sContrast = document.getElementById("slider-contrast");
    const sHighlights = document.getElementById("slider-highlights");
    const sShadows = document.getElementById("slider-shadows");
    const sTemp = document.getElementById("slider-temperature");
    const sTint = document.getElementById("slider-tint");
    const sSat = document.getElementById("slider-saturation");
    const sSepia = document.getElementById("slider-sepia");

    if (presetName === "normal") {
        if (sBrightness) sBrightness.value = 0;
        if (sContrast) sContrast.value = 0;
        if (sHighlights) sHighlights.value = 0;
        if (sShadows) sShadows.value = 0;
        if (sTemp) sTemp.value = 0;
        if (sTint) sTint.value = 0;
        if (sSat) sSat.value = 0;
        if (sSepia) sSepia.value = 0;
    } else if (presetName === "vibrant") {
        if (sBrightness) sBrightness.value = 6;
        if (sContrast) sContrast.value = 15;
        if (sHighlights) sHighlights.value = -10;
        if (sShadows) sShadows.value = 15;
        if (sTemp) sTemp.value = 4;
        if (sTint) sTint.value = 2;
        if (sSat) sSat.value = 35;
        if (sSepia) sSepia.value = 0;
    } else if (presetName === "bw") {
        if (sBrightness) sBrightness.value = 0;
        if (sContrast) sContrast.value = 30;
        if (sHighlights) sHighlights.value = 15;
        if (sShadows) sShadows.value = -15;
        if (sTemp) sTemp.value = 0;
        if (sTint) sTint.value = 0;
        if (sSat) sSat.value = -100;
        if (sSepia) sSepia.value = 0;
    } else if (presetName === "vintage") {
        if (sBrightness) sBrightness.value = -4;
        if (sContrast) sContrast.value = -8;
        if (sHighlights) sHighlights.value = -20;
        if (sShadows) sShadows.value = 20;
        if (sTemp) sTemp.value = 20;
        if (sTint) sTint.value = -5;
        if (sSat) sSat.value = -15;
        if (sSepia) sSepia.value = 35;
    } else if (presetName === "cinematic") {
        if (sBrightness) sBrightness.value = 5;
        if (sContrast) sContrast.value = 25;
        if (sHighlights) sHighlights.value = -15;
        if (sShadows) sShadows.value = 10;
        if (sTemp) sTemp.value = -10;
        if (sTint) sTint.value = 10;
        if (sSat) sSat.value = 15;
        if (sSepia) sSepia.value = 5;
    } else if (presetName === "moody") {
        if (sBrightness) sBrightness.value = -12;
        if (sContrast) sContrast.value = 20;
        if (sHighlights) sHighlights.value = -30;
        if (sShadows) sShadows.value = -10;
        if (sTemp) sTemp.value = -8;
        if (sTint) sTint.value = 5;
        if (sSat) sSat.value = -25;
        if (sSepia) sSepia.value = 0;
    }
}

function resetDevelopTuning() {
    applyDevelopPreset("normal");
    appState.filters.rotation = 0;
    appState.filters.flipH = false;
    appState.filters.flipV = false;
}

function renderCanvas() {
    if (!appState.activeImg) return;
    const canvas = document.getElementById("photo-canvas");
    const beforeCanvas = document.getElementById("before-canvas");
    if (!canvas) return;

    const img = appState.activeImg;
    const isRotated90 = (appState.filters.rotation === 90 || appState.filters.rotation === 270);
    const renderW = isRotated90 ? img.naturalHeight : img.naturalWidth;
    const renderH = isRotated90 ? img.naturalWidth : img.naturalHeight;

    canvas.width = renderW;
    canvas.height = renderH;

    const ctx = canvas.getContext("2d");
    ctx.save();

    // Transformasi Geometri (Rotasi & Flip)
    ctx.translate(renderW / 2, renderH / 2);
    ctx.rotate((appState.filters.rotation * Math.PI) / 180);
    ctx.scale(appState.filters.flipH ? -1 : 1, appState.filters.flipV ? -1 : 1);

    // CSS Filters
    const b = 100 + appState.filters.brightness;
    const c = 100 + appState.filters.contrast;
    const s = 100 + appState.filters.saturation;
    const sp = appState.filters.sepia;
    const hue = appState.filters.tint * 1.5;
    const highlights = appState.filters.highlights / 100;
    const shadows = appState.filters.shadows / 100;
    const temperature = appState.filters.temperature;

    ctx.filter = `brightness(${b}%) contrast(${c}%) saturate(${s}%) sepia(${sp}%) hue-rotate(${hue}deg)`;
    ctx.drawImage(img, -img.naturalWidth / 2, -img.naturalHeight / 2);
    ctx.restore();

    // # FIX: slider Highlights, Shadows, dan Temperature diterapkan ke piksel canvas.
    if (highlights !== 0 || shadows !== 0 || temperature !== 0) {
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const pixels = imageData.data;
        const temperatureShift = temperature * 0.45;

        for (let i = 0; i < pixels.length; i += 4) {
            const red = pixels[i];
            const green = pixels[i + 1];
            const blue = pixels[i + 2];
            const luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue;
            const highlightWeight = Math.max(0, Math.min(1, (luminance - 64) / 176));
            const shadowWeight = Math.max(0, Math.min(1, (192 - luminance) / 160));
            const toneShift = highlights * 48 * highlightWeight + shadows * 48 * shadowWeight;

            pixels[i] = Math.max(0, Math.min(255, red + toneShift + temperatureShift));
            pixels[i + 1] = Math.max(0, Math.min(255, green + toneShift + temperatureShift * 0.08));
            pixels[i + 2] = Math.max(0, Math.min(255, blue + toneShift - temperatureShift));
        }

        ctx.putImageData(imageData, 0, 0);
    }

    // RENDER BEFORE CANVAS (JIKA SPLIT VIEW AKTIF)
    if (appState.isSplitView && beforeCanvas) {
        beforeCanvas.width = img.naturalWidth;
        beforeCanvas.height = img.naturalHeight;
        const bCtx = beforeCanvas.getContext("2d");
        bCtx.drawImage(img, 0, 0);
    }
}

// # FIX: mengenali stego Darkroom agar ekspor mengambil byte sumber, bukan canvas yang diedit.
function isDarkroomStegoPhoto(photo) {
    if (!photo) return false;
    const filename = String(photo.filename || "");
    if (/^(MODIFIED_STEGO_|STEGO_|DECOY_)/i.test(filename)) return true;

    const img = appState.activeImg;
    if (!img || img.naturalWidth < 14 || img.naturalHeight < 1) return false;
    try {
        const probeCanvas = document.createElement("canvas");
        probeCanvas.width = 14;
        probeCanvas.height = 1;
        const probeCtx = probeCanvas.getContext("2d", { willReadFrequently: true });
        probeCtx.drawImage(img, 0, 0, 14, 1, 0, 0, 14, 1);
        const sample = probeCtx.getImageData(0, 0, 14, 1).data;
        const header = new Uint8Array(5);

        for (let bitIndex = 0; bitIndex < 40; bitIndex++) {
            const pixelIndex = Math.floor(bitIndex / 3);
            const channelIndex = bitIndex % 3;
            const bit = sample[pixelIndex * 4 + channelIndex] & 1;
            header[bitIndex >> 3] |= bit << (7 - (bitIndex & 7));
        }

        return String.fromCharCode(...header.slice(0, 4)) === "DKRM" && header[4] === 2;
    } catch (err) {
        console.warn("Tidak dapat memeriksa header stego canvas:", err);
        return false;
    }
}

async function fetchImageAsDataUrl(imageUrl) {
    const res = await fetch(imageUrl);
    if (!res.ok) throw new Error("Gagal membaca citra sumber untuk menjaga payload steganografi.");
    const blob = await res.blob();
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error("Gagal mengubah citra sumber menjadi payload ekspor."));
        reader.readAsDataURL(blob);
    });
}

// ==============================================================================
// 6. WORKSPACE 3: TRANSFER (THE PRIMARY 2-PANEL WORKSPACE & FULL BOTTOM RESULT)
// ==============================================================================
function initTransferWorkspace() {
    // 1. Cover Image Picker & Upload
    const coverPicker = document.getElementById("transfer-cover-picker");
    const coverUpload = document.getElementById("transfer-upload-cover");

    if (coverPicker) {
        coverPicker.addEventListener("change", (e) => {
            const filename = e.target.value;
            if (!filename) return;
            const photo = appState.catalog.find(p => p.filename === filename);
            if (photo) setTransferCover(photo);
        });
    }

    if (coverUpload) {
        coverUpload.addEventListener("change", handleUploadTransferCover);
    }

    // 2. Mode Outgoing vs Incoming Tabs
    const tabOutgoing = document.getElementById("tab-transfer-outgoing");
    const tabIncoming = document.getElementById("tab-transfer-incoming");
    const deckOutgoing = document.getElementById("deck-transfer-outgoing");
    const deckIncoming = document.getElementById("deck-transfer-incoming");

    if (tabOutgoing && tabIncoming) {
        tabOutgoing.addEventListener("click", () => {
            tabOutgoing.classList.add("active");
            tabIncoming.classList.remove("active");
            deckOutgoing.classList.add("active");
            deckOutgoing.style.display = "flex";
            deckIncoming.classList.remove("active");
            deckIncoming.style.display = "none";
        });

        tabIncoming.addEventListener("click", () => {
            tabIncoming.classList.add("active");
            tabOutgoing.classList.remove("active");
            deckIncoming.classList.add("active");
            deckIncoming.style.display = "flex";
            deckOutgoing.classList.remove("active");
            deckOutgoing.style.display = "none";
        });
    }

    // 3. Payload Type Selector (TEXT, FILE, IMAGE)
    const radioText = document.getElementById("radio-payload-text");
    const radioFile = document.getElementById("radio-payload-file");
    const radioImage = document.getElementById("radio-payload-image");

    const groupText = document.getElementById("group-input-text");
    const groupFile = document.getElementById("group-input-file");
    const groupImage = document.getElementById("group-input-image");

    const setPayloadType = (type) => {
        appState.outgoingPayloadType = type;
        [radioText, radioFile, radioImage].forEach(r => r?.classList.remove("active"));
        [groupText, groupFile, groupImage].forEach(g => { if (g) g.style.display = "none"; });

        if (type === "TEXT") {
            radioText?.classList.add("active");
            if (groupText) groupText.style.display = "flex";
        } else if (type === "FILE") {
            radioFile?.classList.add("active");
            if (groupFile) groupFile.style.display = "flex";
        } else if (type === "IMAGE") {
            radioImage?.classList.add("active");
            if (groupImage) groupImage.style.display = "flex";
        }
    };

    radioText?.addEventListener("click", () => setPayloadType("TEXT"));
    radioFile?.addEventListener("click", () => setPayloadType("FILE"));
    radioImage?.addEventListener("click", () => setPayloadType("IMAGE"));

    // 4. Character counter for Outgoing Text
    const textInput = document.getElementById("outgoing-text-content");
    const charCounter = document.getElementById("text-char-counter");
    if (textInput && charCounter) {
        textInput.addEventListener("input", () => {
            const count = textInput.value.length;
            const bytes = new Blob([textInput.value]).size;
            charCounter.textContent = `${count} karakter (${bytes} B)`;
        });
    }

    // 5. Binary File Picked card
    const fileInput = document.getElementById("outgoing-binary-file");
    const filePickedCard = document.getElementById("outgoing-file-picked");
    if (fileInput && filePickedCard) {
        fileInput.addEventListener("change", (e) => {
            if (e.target.files && e.target.files[0]) {
                const f = e.target.files[0];
                filePickedCard.style.display = "flex";
                document.getElementById("picked-file-name").textContent = f.name;
                document.getElementById("picked-file-size").textContent = `${(f.size / 1024).toFixed(1)} KB | MIME: ${f.type || "application/octet-stream"}`;
            } else {
                filePickedCard.style.display = "none";
            }
        });
    }

    // 6. Secret Image Picked card
    const secretImgInput = document.getElementById("outgoing-secret-image");
    const imgPickedCard = document.getElementById("outgoing-img-picked");
    if (secretImgInput && imgPickedCard) {
        secretImgInput.addEventListener("change", (e) => {
            if (e.target.files && e.target.files[0]) {
                const f = e.target.files[0];
                imgPickedCard.style.display = "flex";
                document.getElementById("picked-img-name").textContent = f.name;
                document.getElementById("picked-img-dims").textContent = `${(f.size / 1024).toFixed(1)} KB`;

                const reader = new FileReader();
                reader.onload = (re) => {
                    document.getElementById("picked-img-thumb").src = re.target.result;
                };
                reader.readAsDataURL(f);
            } else {
                imgPickedCard.style.display = "none";
            }
        });
    }

    // 7. Execute Outgoing Action Button
    const btnExecuteOutgoing = document.getElementById("btn-execute-outgoing");
    if (btnExecuteOutgoing) {
        btnExecuteOutgoing.addEventListener("click", () => {
            ensurePrivateSession(executeOutgoingTransfer);
        });
    }

    // 8. Execute Incoming Action Button
    const btnExecuteIncoming = document.getElementById("btn-execute-incoming");
    if (btnExecuteIncoming) {
        btnExecuteIncoming.addEventListener("click", () => {
            ensurePrivateSession(executeIncomingTransfer);
        });
    }

    // 9. Copy revealed text button
    const btnCopy = document.getElementById("btn-copy-revealed-text");
    if (btnCopy) {
        btnCopy.addEventListener("click", () => {
            const txt = document.getElementById("revealed-text-content")?.textContent || "";
            navigator.clipboard.writeText(txt).then(() => {
                alert("Teks rahasia berhasil disalin ke clipboard!");
            });
        });
    }
}

function syncTransferCover() {
    const coverPicker = document.getElementById("transfer-cover-picker");
    if (coverPicker) {
        coverPicker.innerHTML = `<option value="">-- Pilih Cover dari Library --</option>`;
        appState.catalog.forEach(p => {
            if (!p.is_locked) {
                const opt = document.createElement("option");
                opt.value = p.filename;
                opt.textContent = `${p.filename} (${p.size_mb} MB)`;
                coverPicker.appendChild(opt);
            }
        });
    }

    if (!appState.transferCover && appState.activePhoto && !appState.activePhoto.is_locked) {
        setTransferCover(appState.activePhoto);
    }
}

async function setTransferCover(photo) {
    appState.transferCover = photo;

    const coverImg = document.getElementById("transfer-cover-img");
    const coverEmpty = document.getElementById("transfer-cover-empty");
    const picker = document.getElementById("transfer-cover-picker");

    if (coverImg) {
        coverImg.src = photo.url;
        coverImg.style.display = "block";
    }
    if (coverEmpty) coverEmpty.style.display = "none";
    if (picker) picker.value = photo.filename;

    document.getElementById("trans-meta-filename").textContent = photo.filename;
    document.getElementById("trans-meta-filesize").textContent = `${photo.size_mb} MB`;

    // Fetch Kapasitas LSB dari Backend
    try {
        const res = await fetch(`/api/transfer/capacity/${photo.filename}`);
        const data = await res.json();
        if (data.success && data.capacity) {
            const cap = data.capacity;
            appState.transferCapacity = cap;

            document.getElementById("trans-meta-dimensions").textContent = `${cap.format} (${cap.width} x ${cap.height})`;
            const badge = document.getElementById("trans-meta-suitability");
            if (badge) {
                badge.className = `meta-badge ${cap.is_suitable ? 'badge-optimal' : 'badge-warning'}`;
                badge.textContent = cap.suitability_note || (cap.is_suitable ? "Optimal untuk LSB" : "Perlu Lossless PNG");
            }

            document.getElementById("trans-capacity-text").textContent = cap.max_payload_formatted;
            const fill = document.getElementById("trans-capacity-fill");
            if (fill) fill.style.width = "100%";
        }
    } catch (err) {
        console.error("Gagal menghitung kapasitas cover:", err);
    }
}

async function handleUploadTransferCover(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    formData.append("files", files[0]);

    try {
        const res = await fetch("/api/catalog/import", { method: "POST", body: formData });
        const data = await res.json();
        if (data.success && data.imported && data.imported.length > 0) {
            await loadCatalog();
            const newPhoto = appState.catalog.find(p => p.filename === data.imported[0]);
            if (newPhoto) setTransferCover(newPhoto);
        }
    } catch (err) {
        alert("Gagal mengunggah foto cover: " + err.message);
    } finally {
        e.target.value = "";
    }
}

async function executeOutgoingTransfer() {
    if (!appState.transferCover) {
        alert("Pilih foto cover pembawa terlebih dahulu di panel kiri!");
        return;
    }

    const type = appState.outgoingPayloadType;
    const btn = document.getElementById("btn-execute-outgoing");
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Memproses Enkripsi & LSB...`;

    // Reset result panel
    hideAllTransferResults();

    try {
        const headers = {};
        if (appState.sessionToken) {
            headers["Authorization"] = `Bearer ${appState.sessionToken}`;
        }

        let endpoint = "";
        const formData = new FormData();
        formData.append("cover_filename", appState.transferCover.filename);

        if (type === "TEXT") {
            endpoint = "/api/transfer/outgoing/text";
            const text = document.getElementById("outgoing-text-content")?.value.trim();
            const vigKey = document.getElementById("outgoing-vigenere-key")?.value.trim();
            const aesKey = document.getElementById("outgoing-aes-key")?.value.trim();

            if (!text) throw new Error("Pesan teks rahasia tidak boleh kosong!");
            if (!aesKey) throw new Error("Passphrase AES-256-GCM wajib diisi!");

            formData.append("plaintext", text);
            formData.append("vigenere_key", vigKey);
            formData.append("aes_key", aesKey);

        } else if (type === "FILE") {
            endpoint = "/api/transfer/outgoing/file";
            const fileInput = document.getElementById("outgoing-binary-file");
            const pass = document.getElementById("outgoing-file-passphrase")?.value.trim();

            if (!fileInput.files || !fileInput.files[0]) throw new Error("Pilih berkas yang akan disembunyikan!");
            if (!pass) throw new Error("Passphrase ChaCha20-Poly1305 wajib diisi!");

            formData.append("payload_file", fileInput.files[0]);
            formData.append("passphrase", pass);

        } else if (type === "IMAGE") {
            endpoint = "/api/transfer/outgoing/image";
            const imgInput = document.getElementById("outgoing-secret-image");
            const pass = document.getElementById("outgoing-img-passphrase")?.value.trim();

            if (!imgInput.files || !imgInput.files[0]) throw new Error("Pilih citra rahasia yang akan disembunyikan!");
            if (!pass) throw new Error("Passphrase proteksi citra wajib diisi!");

            formData.append("secret_image", imgInput.files[0]);
            formData.append("passphrase", pass);
        }

        const res = await fetch(endpoint, {
            method: "POST",
            headers,
            body: formData
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Gagal menyisipkan muatan!");

        // Tampilkan Hasil Sukses di Bottom Panel
        const resBox = document.getElementById("trans-result-outgoing");
        const downloadBtn = document.getElementById("btn-download-outgoing-stego");
        const badge = document.getElementById("trans-result-badge");

        if (resBox && downloadBtn) {
            resBox.style.display = "flex";
            downloadBtn.href = data.download_url;
            downloadBtn.download = data.output_filename;

            document.getElementById("out-res-filename").textContent = data.output_filename;
            document.getElementById("out-res-cap").textContent = data.capacity_used;
            document.getElementById("out-res-bytes").textContent = `${data.bytes_embedded} Bytes`;
            document.getElementById("out-result-desc").textContent = `Payload tipe ${data.type} berhasil dienkripsi dan disisipkan ke pixel LSB cover ${appState.transferCover.filename}.`;

            // Shortcut navigasi dari hasil transfer
            const btnGotoDevelop = document.getElementById("btn-transfer-goto-develop");
            if (btnGotoDevelop) {
                btnGotoDevelop.onclick = () => {
                    if (data.output_filename) {
                        const p = appState.catalog.find(x => x.filename === data.output_filename);
                        if (p) selectPhoto(p);
                    }
                    switchWorkspace("view-develop");
                };
            }

            const btnGotoDecrypt = document.getElementById("btn-transfer-goto-decrypt");
            if (btnGotoDecrypt) {
                btnGotoDecrypt.onclick = () => {
                    switchWorkspace("view-decrypt");
                    populateDecryptCatalog(data.output_filename);
                };
            }
        }

        if (badge) {
            badge.className = "badge badge-optimal";
            badge.textContent = "LSB Selesai";
        }

        // Muat ulang katalog foto agar stego PNG yang baru dibuat muncul
        await loadCatalog();
        populateDecryptCatalog(data.output_filename);

    } catch (err) {
        showTransferError("Gagal Eksekusi Outgoing", err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-lock"></i> Enkripsi & Sisipkan ke Cover (LSB V2)`;
    }
}

async function executeIncomingTransfer() {
    const fileInput = document.getElementById("incoming-stego-file");
    if (!fileInput.files || !fileInput.files[0]) {
        alert("Pilih berkas citra bersteganografi terlebih dahulu!");
        return;
    }

    const vigKey = document.getElementById("incoming-vigenere-key")?.value.trim();
    const pass = document.getElementById("incoming-passphrase")?.value.trim();

    const btn = document.getElementById("btn-execute-incoming");
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Memindai LSB & Verifikasi AEAD...`;

    hideAllTransferResults();

    try {
        const headers = {};
        if (appState.sessionToken) {
            headers["Authorization"] = `Bearer ${appState.sessionToken}`;
        }

        const formData = new FormData();
        formData.append("stego_file", fileInput.files[0]);
        formData.append("vigenere_key", vigKey || "");
        formData.append("aes_key", pass || "");
        formData.append("passphrase", pass || "");

        const res = await fetch("/api/transfer/incoming/extract", {
            method: "POST",
            headers,
            body: formData
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Gagal ekstraksi steganografi!");

        if (!data.has_payload) {
            showTransferError("Muatan Tidak Dikenali", "Tidak ditemukan payload Darkroom yang valid pada citra ini (Magic Byte DKRM\\x02 tidak terdeteksi).");
            return;
        }

        const badge = document.getElementById("trans-result-badge");
        if (badge) {
            badge.className = "badge badge-optimal";
            badge.textContent = `Payload Ditemukan: ${data.type}`;
        }

        if (data.type === "TEXT") {
            const textBox = document.getElementById("trans-result-inc-text");
            const content = document.getElementById("revealed-text-content");
            if (textBox && content) {
                textBox.style.display = "block";
                content.textContent = data.plaintext || `[Ciphertext: ${data.raw_ciphertext}]\n(Tag otentikasi valid namun kunci teks tidak cocok)`;
            }
        } else if (data.type === "FILE") {
            const fileBox = document.getElementById("trans-result-inc-file");
            const dlBtn = document.getElementById("btn-download-recovered-file");
            if (fileBox && dlBtn) {
                fileBox.style.display = "flex";
                dlBtn.href = data.download_url;
                dlBtn.download = data.original_filename || "recovered_file";
                document.getElementById("inc-recovered-filename").textContent = data.original_filename || "recovered_file";
                document.getElementById("inc-recovered-size").textContent = `${data.bytes_recovered || 0} Bytes | Tag Poly1305 VALID`;
            }
        } else if (data.type === "IMAGE") {
            const imgBox = document.getElementById("trans-result-inc-img");
            const dlBtn = document.getElementById("btn-download-recovered-img");
            const preview = document.getElementById("inc-recovered-img-preview");
            if (imgBox && dlBtn && preview) {
                imgBox.style.display = "flex";
                preview.src = data.download_url;
                dlBtn.href = data.download_url;
                dlBtn.download = data.saved_file ? data.saved_file.split("/").pop() : "recovered_image.png";
                document.getElementById("inc-recovered-imgname").textContent = "Citra Rahasia Dipulihkan";
                document.getElementById("inc-recovered-imgdims").textContent = "Integritas Byte 100% Cocok";
            }
        }

    } catch (err) {
        showTransferError("Ekstraksi Gagal", err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-barcode"></i> Pindai & Bongkar Muatan Rahasia`;
    }
}

function hideAllTransferResults() {
    // # FIX: penyesuaian payload & state
    ["trans-result-empty", "trans-result-outgoing", "trans-result-inc-text", "trans-result-inc-file", "trans-result-inc-img", "trans-result-error"]
        .forEach(id => {
            const result = document.getElementById(id);
            if (result) result.style.display = "none";
        });
}

function showTransferError(title, desc) {
    hideAllTransferResults();
    const errBox = document.getElementById("trans-result-error");
    if (errBox) {
        errBox.style.display = "flex";
        document.getElementById("trans-error-title").textContent = title;
        document.getElementById("trans-error-desc").textContent = desc;
    }
    const badge = document.getElementById("trans-result-badge");
    if (badge) {
        badge.className = "badge badge-warning";
        badge.textContent = "Error";
    }
}

// ==============================================================================
// 6.5. WORKSPACE: DEKRIPSI & EKSTRAKTOR STEGANOGRAFI (COVERT FEATURE)
// ==============================================================================
function initDecryptWorkspace() {
    const picker = document.getElementById("decrypt-catalog-picker");
    const fileInput = document.getElementById("decrypt-file-input");
    const btnExecute = document.getElementById("btn-execute-decrypt");

    if (picker) {
        picker.addEventListener("change", () => {
            if (picker.value && fileInput) {
                fileInput.value = "";
            }
        });
    }

    if (fileInput) {
        fileInput.addEventListener("change", () => {
            if (fileInput.files && fileInput.files[0] && picker) {
                picker.value = "";
            }
        });
    }

    if (btnExecute) {
        // # FIX: penyesuaian payload & state
        btnExecute.addEventListener("click", () => ensurePrivateSession(executeDecryptWorkspace));
    }

    const btnCopy = document.getElementById("btn-copy-decrypt-text");
    if (btnCopy) {
        btnCopy.addEventListener("click", () => {
            const text = document.getElementById("decrypt-text-content")?.textContent;
            if (text) {
                navigator.clipboard.writeText(text).then(() => {
                    alert("Teks rahasia berhasil disalin ke clipboard!");
                }).catch(() => {
                    alert("Gagal menyalin teks ke clipboard.");
                });
            }
        });
    }
}

function populateDecryptCatalog(preselectFilename) {
    const picker = document.getElementById("decrypt-catalog-picker");
    if (!picker) return;

    const currentVal = preselectFilename || picker.value;
    picker.innerHTML = '<option value="">-- Pilih dari Katalog Foto --</option>';

    const stegoPhotos = [];
    const regularPhotos = [];

    appState.catalog.forEach(p => {
        if (p.filename.startsWith("MODIFIED_STEGO_") || p.filename.startsWith("STEGO_")) {
            stegoPhotos.push(p);
        } else {
            regularPhotos.push(p);
        }
    });

    if (stegoPhotos.length > 0) {
        const groupStego = document.createElement("optgroup");
        groupStego.label = "⭐ Foto Modifikasi Steganografi (LSB Framing)";
        stegoPhotos.forEach(p => {
            const opt = document.createElement("option");
            opt.value = p.filename;
            opt.textContent = `${p.filename} (${p.size_formatted || (p.size + ' B')})`;
            groupStego.appendChild(opt);
        });
        picker.appendChild(groupStego);
    }

    if (regularPhotos.length > 0) {
        const groupReg = document.createElement("optgroup");
        groupReg.label = "Katalog Foto Lainnya";
        regularPhotos.forEach(p => {
            const opt = document.createElement("option");
            opt.value = p.filename;
            opt.textContent = `${p.filename} (${p.size_formatted || (p.size + ' B')})`;
            groupReg.appendChild(opt);
        });
        picker.appendChild(groupReg);
    }

    if (currentVal) {
        picker.value = currentVal;
    }
}

async function executeDecryptWorkspace() {
    const picker = document.getElementById("decrypt-catalog-picker");
    const fileInput = document.getElementById("decrypt-file-input");
    const vigKeyInput = document.getElementById("decrypt-vigenere-key");
    const passInput = document.getElementById("decrypt-passphrase");
    const btnExecute = document.getElementById("btn-execute-decrypt");

    const catalogFilename = picker ? picker.value : "";
    const uploadedFile = fileInput && fileInput.files ? fileInput.files[0] : null;

    if (!catalogFilename && !uploadedFile) {
        alert("Pilih foto bersteganografi dari katalog atau unggah berkas citra terlebih dahulu!");
        return;
    }

    const vigKey = vigKeyInput ? vigKeyInput.value.trim() : "JURNALIS";
    const passphrase = passInput ? passInput.value.trim() : "OperasiSenyap2026!";

    const placeholder = document.getElementById("decrypt-placeholder");
    const textBox = document.getElementById("decrypt-text-box");
    const fileBox = document.getElementById("decrypt-file-box");
    const imgBox = document.getElementById("decrypt-img-box");
    const errBox = document.getElementById("decrypt-error-box");

    if (placeholder) placeholder.style.display = "none";
    if (textBox) textBox.style.display = "none";
    if (fileBox) fileBox.style.display = "none";
    if (imgBox) imgBox.style.display = "none";
    if (errBox) errBox.style.display = "none";

    btnExecute.disabled = true;
    btnExecute.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Mengekstrak LSB & Memverifikasi Otentikasi AEAD...';

    try {
        const formData = new FormData();
        if (uploadedFile) {
            formData.append("stego_file", uploadedFile);
        } else {
            formData.append("filename", catalogFilename);
        }
        formData.append("vigenere_key", vigKey || "JURNALIS");
        formData.append("passphrase", passphrase || "OperasiSenyap2026!");

        const headers = {};
        if (appState.sessionToken) {
            headers["Authorization"] = `Bearer ${appState.sessionToken}`;
        }

        const res = await fetch("/api/transfer/incoming/extract", {
            method: "POST",
            headers,
            body: formData
        });

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Gagal membongkar payload!");
        }

        // # FIX: penyesuaian payload & state
        if (data.type === "TEXT") {
            if (textBox) {
                textBox.style.display = "block";
                const contentEl = document.getElementById("decrypt-text-content");
                if (contentEl) {
                    contentEl.textContent = data.is_decrypted
                        ? (data.plaintext || "")
                        : (data.error || data.raw_ciphertext || "Payload teks belum dapat didekripsi.");
                }
            }
        } else if (data.type === "FILE") {
            if (fileBox) {
                fileBox.style.display = "block";
                const nameEl = document.getElementById("decrypt-recovered-filename");
                const sizeEl = document.getElementById("decrypt-recovered-size");
                const dlBtn = document.getElementById("btn-download-decrypt-file");

                if (nameEl) nameEl.textContent = data.filename || "file_terekstrak.bin";
                if (sizeEl) {
                    const sizeText = data.file_size_formatted || (data.file_size != null ? `${data.file_size} B` : "Berkas berhasil dipulihkan");
                    sizeEl.textContent = `${sizeText} | Tag Poly1305 VALID`;
                }
                if (dlBtn) {
                    dlBtn.href = data.download_url;
                    dlBtn.download = data.filename || "file_terekstrak.bin";
                }
            }
        } else if (data.type === "IMAGE") {
            if (imgBox) {
                imgBox.style.display = "block";
                const imgEl = document.getElementById("decrypt-recovered-img");
                const nameEl = document.getElementById("decrypt-recovered-imgname");
                const dimsEl = document.getElementById("decrypt-recovered-imgdims");
                const dlBtn = document.getElementById("btn-download-decrypt-img");

                if (imgEl) imgEl.src = data.download_url;
                if (nameEl) nameEl.textContent = data.filename || "citra_rahasia.png";
                if (dimsEl) dimsEl.textContent = `${data.dimensions || 'Citra Rahasia'} | 100% Cocok Byte-for-Byte`;
                if (dlBtn) {
                    dlBtn.href = data.download_url;
                    dlBtn.download = data.filename || "citra_rahasia.png";
                }
            }
        } else {
            throw new Error(data.message || "Tipe payload tidak dikenali.");
        }
    } catch (err) {
        if (errBox) {
            errBox.style.display = "flex";
            const errEl = document.getElementById("decrypt-error-desc");
            if (errEl) errEl.textContent = err.message;
        } else {
            alert("Gagal dekripsi: " + err.message);
        }
    } finally {
        btnExecute.disabled = false;
        btnExecute.innerHTML = '<i class="fa-solid fa-barcode"></i> Pindai & Bongkar Muatan Rahasia';
    }
}

// ==============================================================================
// 7. WORKSPACE 4: EXPORT (FORMAT, RESOLUSI, KUALITAS)
// ==============================================================================
function initExportWorkspace() {
    // Format choice pills (JPEG, PNG, TIFF)
    document.querySelectorAll(".choice-pill[data-format]").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll(".choice-pill[data-format]").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            appState.exportFormat = pill.getAttribute("data-format");

            const qualityGroup = document.getElementById("export-quality-group");
            if (qualityGroup) {
                qualityGroup.style.display = appState.exportFormat === "JPEG" ? "flex" : "none";
            }
            updateExportFilenameDefault();
        });
    });

    // Scale choice pills (100%, 75%, 50%)
    document.querySelectorAll(".choice-pill[data-scale]").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll(".choice-pill[data-scale]").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            appState.exportScale = parseInt(pill.getAttribute("data-scale") || 100);
        });
    });

    // Quality Slider for JPEG
    const qualitySlider = document.getElementById("slider-export-quality");
    if (qualitySlider) {
        qualitySlider.addEventListener("input", (e) => {
            appState.exportQuality = parseInt(e.target.value);
            document.getElementById("val-export-quality").textContent = `${appState.exportQuality}%`;
        });
    }

    // Tombol Eksekusi Ekspor
    const btnDoExport = document.getElementById("btn-do-develop-export");
    if (btnDoExport) {
        btnDoExport.addEventListener("click", executeDevelopExport);
    }
}

function updateExportPreview() {
    const previewImg = document.getElementById("export-preview-img");
    const emptyMsg = document.getElementById("export-empty-msg");
    const infoBox = document.getElementById("export-photo-info");

    if (appState.activePhoto && appState.activeImg) {
        if (previewImg) {
            // Gunakan snapshot canvas saat ini jika sudah diedit
            const canvas = document.getElementById("photo-canvas");
            previewImg.src = canvas ? canvas.toDataURL("image/jpeg", 0.9) : appState.activePhoto.url;
            previewImg.style.display = "block";
        }
        if (emptyMsg) emptyMsg.style.display = "none";
        if (infoBox) infoBox.style.display = "flex";

        document.getElementById("export-src-name").textContent = appState.activePhoto.filename;
        document.getElementById("export-src-dims").textContent = `${appState.activeImg.naturalWidth} x ${appState.activeImg.naturalHeight}`;

        updateExportFilenameDefault();
    } else {
        if (previewImg) previewImg.style.display = "none";
        if (emptyMsg) emptyMsg.style.display = "block";
        if (infoBox) infoBox.style.display = "none";
    }
}

function updateExportFilenameDefault() {
    const nameInput = document.getElementById("export-custom-filename");
    if (!nameInput || !appState.activePhoto) return;

    const base = appState.activePhoto.filename.replace(/\.[^/.]+$/, "");
    const ext = appState.exportFormat.toLowerCase() === "jpeg" ? "jpg" : appState.exportFormat.toLowerCase();
    // # FIX: penyesuaian payload & state
    nameInput.value = `${base}.${ext}`;
}

async function executeDevelopExport() {
    if (!appState.activePhoto) {
        alert("Pilih foto terlebih dahulu di Develop!");
        return;
    }

    const btn = document.getElementById("btn-do-develop-export");
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Merender Berkas Ekspor...`;

    try {
        const canvas = document.getElementById("photo-canvas");
        // # FIX: untuk stego, ekspor byte sumber PNG agar edit canvas tidak mengubah bit LSB.
        const preserveStegoPayload = isDarkroomStegoPhoto(appState.activePhoto);
        const exportFormat = preserveStegoPayload ? "PNG" : appState.exportFormat;
        const imageBase64 = preserveStegoPayload
            ? await fetchImageAsDataUrl(appState.activePhoto.url)
            : (canvas ? canvas.toDataURL("image/png") : null);
        const customName = document.getElementById("export-custom-filename")?.value.trim() || appState.activePhoto.filename;

        const payload = {
            filename: customName,
            export_format: exportFormat,
            quality: appState.exportQuality,
            scale_percent: appState.exportScale,
            image_base64: imageBase64
        };

        const res = await fetch("/api/develop/export", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Gagal mengekspor foto!");

        // # FIX: penyesuaian payload & state
        data.output_filename = data.filename || customName;
        data.format = data.format || appState.exportFormat;

        const banner = document.getElementById("export-result-banner");
        const link = document.getElementById("link-download-exported-file");
        if (banner && link) {
            banner.style.display = "flex";
            link.href = data.download_url;
            // # FIX: penyesuaian payload & state
            link.download = data.filename || customName;
        }

        alert(`✅ FOTO BERHASIL DIEKSPOR!\n\nNama: ${data.output_filename}\nFormat: ${data.format}\nUkuran: ${data.size_mb} MB\nResolusi: ${data.dimensions}`);

        // Muat ulang katalog
        await loadCatalog();

    } catch (err) {
        alert("Gagal ekspor: " + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-download"></i> Ekspor & Unduh Berkas`;
    }
}

// ==============================================================================
// 8. WORKSPACE 5: PREFERENCES (DONGLE, BLOCKCHAIN AUDIT)
// ==============================================================================
function initPreferencesWorkspace() {
    // Virtual Dongle Toggle
    const virtualToggle = document.getElementById("toggle-virtual-dongle");
    if (virtualToggle) {
        virtualToggle.addEventListener("change", async (e) => {
            const active = e.target.checked;
            try {
                const res = await fetch(`/api/dongle/virtual?active=${active}`, { method: "POST" });
                const data = await res.json();
                alert(`Virtual Dongle: ${data.virtual_dongle ? "DIAKTIFKAN (Testing Mode)" : "DINONAKTIFKAN"}`);
                await checkSessionStatus();
            } catch (err) {
                console.error("Gagal toggle virtual dongle:", err);
            }
        });
    }

    // Biometric Controls
    initBiometricControls();

    // Blockchain Audit Buttons
    const btnAudit = document.getElementById("btn-audit-blockchain");
    const btnTamper = document.getElementById("btn-tamper-demo");

    if (btnAudit) {
        btnAudit.addEventListener("click", async () => {
            const audit = await loadBlockchain();
            if (audit?.is_valid === true) {
                alert(`Audit valid: ${audit.message}`);
            } else {
                alert(`Audit gagal / rantai tidak valid: ${audit?.message || "Tidak ada hasil validasi dari backend."}`);
            }
        });
    }

    if (btnTamper) {
        btnTamper.addEventListener("click", () => {
            ensurePrivateSession(async () => {
                try {
                    // # FIX: token sesi dikirim ke endpoint terproteksi
                    const headers = {};
                    if (appState.sessionToken) {
                        headers["Authorization"] = `Bearer ${appState.sessionToken}`;
                    }
                    const res = await fetch("/api/blockchain/simulate-tamper", { method: "POST", headers });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || "Gagal simulasi serangan!");

                    const statusAlert = document.getElementById("bc-status-alert");
                    const statusText = document.getElementById("bc-status-text");
                    if (data.tamper_detected === true && data.is_valid === false) {
                        if (statusAlert) statusAlert.className = "blockchain-status-alert tampered";
                        if (statusText) statusText.textContent = `Manipulasi terdeteksi oleh verifikasi hash: ${data.message}`;

                        const cards = document.querySelectorAll(".chain-block-card");
                        if (cards.length > 1) cards[1].classList.add("tampered-card");
                        alert(`Simulasi tamper terdeteksi oleh backend.\n\n${data.message}`);
                    } else {
                        await loadBlockchain();
                        alert(`Backend tidak mengonfirmasi manipulasi: ${data.message || "hasil tidak valid"}`);
                    }
                } catch (err) {
                    alert("Simulasi Tamper: " + err.message);
                }
            });
        });
    }
}

// ==============================================================================
// 8.5. BIOMETRIC FACE RECOGNITION (YUNET + SFACE)
// ==============================================================================
let bioStream = null;

async function checkBiometricStatus() {
    const statusLabel = document.getElementById("bio-reg-status");
    if (!statusLabel) return;
    try {
        const res = await fetch("/api/auth/biometric/status");
        const data = await res.json();
        if (data.is_registered) {
            statusLabel.textContent = "Wajah Terdaftar (Aman)";
            statusLabel.style.color = "var(--accent-green)";
        } else {
            statusLabel.textContent = "Belum Ada Wajah Terdaftar";
            statusLabel.style.color = "var(--accent-cyan)";
        }
    } catch (e) {
        statusLabel.textContent = "Offline";
    }
}

function captureFrameBase64() {
    const video = document.getElementById("bio-video-feed");
    const canvas = document.getElementById("bio-capture-canvas");
    if (!video || !canvas || video.videoWidth === 0) return null;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.85);
}

function initBiometricControls() {
    checkBiometricStatus();

    const btnToggleCam = document.getElementById("btn-bio-toggle-cam");
    const btnCamText = document.getElementById("btn-bio-cam-text");
    const camBox = document.getElementById("bio-cam-container");
    const video = document.getElementById("bio-video-feed");
    const feedback = document.getElementById("bio-action-feedback");

    const showFeedback = (msg, isSuccess = true) => {
        if (!feedback) return;
        feedback.style.display = "block";
        feedback.textContent = msg;
        feedback.style.background = isSuccess ? "rgba(0, 245, 155, 0.1)" : "rgba(255, 51, 102, 0.1)";
        feedback.style.color = isSuccess ? "var(--accent-green)" : "var(--accent-red)";
        feedback.style.border = `1px solid ${isSuccess ? "var(--accent-green)" : "var(--accent-red)"}`;
    };

    if (btnToggleCam) {
        btnToggleCam.addEventListener("click", async () => {
            if (bioStream) {
                // Matikan kamera
                bioStream.getTracks().forEach(track => track.stop());
                bioStream = null;
                if (video) video.srcObject = null;
                if (camBox) camBox.style.display = "none";
                if (btnCamText) btnCamText.textContent = "Buka Kamera";
            } else {
                // Buka kamera
                try {
                    bioStream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 } });
                    if (video) video.srcObject = bioStream;
                    if (camBox) camBox.style.display = "block";
                    if (btnCamText) btnCamText.textContent = "Tutup Kamera";
                    showFeedback("Kamera aktif. Posisikan wajah Anda di depan webcam.", true);
                } catch (err) {
                    showFeedback("Tidak dapat mengakses webcam: " + err.message, false);
                }
            }
        });
    }

    const btnRegister = document.getElementById("btn-bio-register");
    if (btnRegister) {
        btnRegister.addEventListener("click", async () => {
            if (!bioStream) {
                showFeedback("Aktifkan kamera terlebih dahulu sebelum mendaftar!", false);
                return;
            }
            const b64 = captureFrameBase64();
            if (!b64) {
                showFeedback("Frame video belum siap. Tunggu kamera menyala.", false);
                return;
            }
            try {
                btnRegister.disabled = true;
                btnRegister.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Memproses AI...';
                const res = await fetch("/api/auth/biometric/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ image_base64: b64 })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Gagal registrasi wajah!");
                showFeedback(`Berhasil: ${data.message}`, true);
                await checkBiometricStatus();
            } catch (err) {
                showFeedback("Gagal: " + err.message, false);
            } finally {
                btnRegister.disabled = false;
                btnRegister.innerHTML = '<i class="fa-solid fa-user-plus"></i> Daftarkan Wajah';
            }
        });
    }

    const btnVerify = document.getElementById("btn-bio-verify");
    if (btnVerify) {
        btnVerify.addEventListener("click", async () => {
            if (!bioStream) {
                showFeedback("Aktifkan kamera terlebih dahulu untuk memindai wajah!", false);
                return;
            }
            const b64 = captureFrameBase64();
            if (!b64) {
                showFeedback("Frame video belum siap.", false);
                return;
            }
            try {
                btnVerify.disabled = true;
                btnVerify.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Membandingkan...';
                const res = await fetch("/api/auth/biometric/verify", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ image_base64: b64 })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Gagal verifikasi biometrik!");
                showFeedback(data.message, data.is_match);
            } catch (err) {
                showFeedback("Gagal: " + err.message, false);
            } finally {
                btnVerify.disabled = false;
                btnVerify.innerHTML = '<i class="fa-solid fa-id-badge"></i> Verifikasi Wajah';
            }
        });
    }

    const btnReset = document.getElementById("btn-bio-reset");
    if (btnReset) {
        btnReset.addEventListener("click", async () => {
            const ok = confirm("Hapus rekaman embedding biometrik wajah agen?");
            if (!ok) return;
            try {
                const res = await fetch("/api/auth/biometric/reset", { method: "POST" });
                const data = await res.json();
                showFeedback(data.message, true);
                await checkBiometricStatus();
            } catch (err) {
                showFeedback("Gagal reset: " + err.message, false);
            }
        });
    }
}

async function loadBlockchain() {
    const grid = document.getElementById("chain-cards-grid");
    const statusAlert = document.getElementById("bc-status-alert");
    const statusText = document.getElementById("bc-status-text");
    if (!grid) return null;

    try {
        const res = await fetch("/api/blockchain/status");
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Gagal membaca status blockchain.");
        if (typeof data.is_valid !== "boolean" || !Array.isArray(data.chain)) {
            throw new Error("Respons audit blockchain tidak lengkap.");
        }

        if (statusAlert && statusText) {
            statusAlert.className = data.is_valid ? "blockchain-status-alert" : "blockchain-status-alert tampered";
            statusText.textContent = data.message;
        }

        grid.innerHTML = "";
        data.chain.forEach(blk => {
            const card = document.createElement("div");
            card.className = "chain-block-card";
            card.innerHTML = `
                <div class="chain-block-title">
                    <i class="fa-solid fa-cube"></i> Blok #${blk.index} ${blk.index === 0 ? '(Genesis)' : ''}
                </div>
                <div style="font-size:9.5px; color:#aaa; margin-bottom:2px;">${blk.timestamp}</div>
                <div style="font-size:9px; color:#888;">Prev Hash:</div>
                <div class="chain-block-hash">${blk.previous_hash.slice(0, 16)}...</div>
                <div style="font-size:9px; color:#888;">Current Hash:</div>
                <div class="chain-block-hash" style="color:#00f59b;">${blk.current_hash.slice(0, 16)}...</div>
                <div style="font-size:9.5px; color:#777; margin-top:2px;">
                    Nonce: <strong style="color:#fff;">${blk.nonce}</strong><br>
                    Meta: <span style="color:#aaa;">${blk.metadata}</span>
                </div>
            `;
            grid.appendChild(card);
        });
        return data;
    } catch (err) {
        console.error("Gagal memuat status blockchain:", err);
        if (statusAlert) statusAlert.className = "blockchain-status-alert tampered";
        if (statusText) statusText.textContent = `Audit gagal: ${err.message}`;
        grid.innerHTML = "";
        return { is_valid: false, message: err.message, chain: [] };
    }
}

// ==============================================================================
// 9. KATALOG FOTO & FILMSTRIP CONTROLLER
// ==============================================================================
async function loadCatalog() {
    try {
        const res = await fetch("/api/catalog/photos");
        const data = await res.json();
        appState.catalog = data.photos || [];

        renderFilmstrip();
        renderLibraryGrid();
        syncTransferCover();
        populateDecryptCatalog();

        if (appState.activePhoto) {
            const still = appState.catalog.find(p => p.filename === appState.activePhoto.filename);
            if (still) {
                selectPhoto(still);
                return;
            }
        }

        if (appState.catalog.length > 0) {
            const firstUnlocked = appState.catalog.find(p => !p.is_locked) || appState.catalog[0];
            selectPhoto(firstUnlocked);
        }
    } catch (err) {
        console.error("Gagal memuat katalog foto:", err);
    }
}

function selectPhoto(photo) {
    appState.activePhoto = photo;

    // Highlight filmstrip
    document.querySelectorAll(".thumb-card").forEach((c, idx) => {
        if (appState.catalog[idx] && appState.catalog[idx].filename === photo.filename) {
            c.classList.add("active");
        } else {
            c.classList.remove("active");
        }
    });

    const titleDisp = document.getElementById("active-filename-display");
    const sizeDisp = document.getElementById("active-filesize-display");
    if (titleDisp) titleDisp.textContent = photo.filename;
    if (sizeDisp) sizeDisp.textContent = `${photo.size_mb} MB`;

    // Update status gembok di inspector Develop & Library
    const lockStatusLabel = document.getElementById("label-active-lock-status");
    const btnLockActive = document.getElementById("btn-lock-active-file");
    const btnLibLock = document.getElementById("btn-lib-toggle-lock");
    if (lockStatusLabel) {
        if (photo.is_locked) {
            lockStatusLabel.textContent = "LOCKED (.enc)";
            lockStatusLabel.className = "status-locked";
            if (btnLockActive) btnLockActive.innerHTML = `<i class="fa-solid fa-lock-open"></i> Buka Kunci Berkas (.enc)`;
            if (btnLibLock) btnLibLock.innerHTML = `<i class="fa-solid fa-lock-open"></i> Buka Kunci (.enc)`;
        } else {
            lockStatusLabel.textContent = "UNLOCKED";
            lockStatusLabel.className = "status-unlocked";
            if (btnLockActive) btnLockActive.innerHTML = `<i class="fa-solid fa-lock"></i> Kunci Berkas di Harddisk`;
            if (btnLibLock) btnLibLock.innerHTML = `<i class="fa-solid fa-file-shield"></i> Kunci Berkas (.enc)`;
        }
    }

    // Load ke canvas
    const canvas = document.getElementById("photo-canvas");
    const emptyMsg = document.getElementById("empty-state-msg");

    if (photo.is_locked) {
        if (emptyMsg) {
            emptyMsg.style.display = "block";
            emptyMsg.innerHTML = `
                <i class="fa-solid fa-shield-halved" style="color: var(--accent-red); font-size:44px;"></i>
                <p style="color: var(--accent-red); font-weight:700; margin-top:8px;">Berkas ${photo.filename} terkunci dengan ChaCha20 (.enc)</p>
                <div style="margin-top: 14px; max-width: 320px; margin-left: auto; margin-right: auto;">
                    <input type="password" id="canvas-unlock-passphrase" placeholder="Passphrase ChaCha20..." value="BrankasDarkroom2026!" style="margin-bottom: 8px;">
                    <button class="btn btn-success btn-block" id="btn-canvas-unlock"><i class="fa-solid fa-lock-open"></i> Buka Kunci Berkas Ini</button>
                </div>
            `;
            document.getElementById("btn-canvas-unlock")?.addEventListener("click", () => {
                const pass = document.getElementById("canvas-unlock-passphrase")?.value.trim();
                executeUnlockPhotoFile(photo.filename, pass);
            });
        }
        if (canvas) canvas.style.display = "none";
        appState.activeImg = null;
        return;
    }

    if (emptyMsg) emptyMsg.style.display = "none";
    if (canvas) canvas.style.display = "block";

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.src = photo.url;
    img.onload = () => {
        appState.activeImg = img;
        renderCanvas();
        updateExportPreview();
    };
}

function renderFilmstrip() {
    const track = document.getElementById("filmstrip-track");
    if (!track) return;

    track.innerHTML = "";
    appState.catalog.forEach(photo => {
        const card = document.createElement("div");
        card.className = "thumb-card";
        if (appState.activePhoto && appState.activePhoto.filename === photo.filename) {
            card.classList.add("active");
        }

        if (photo.is_locked) {
            card.innerHTML = `
                <div style="height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; background:#1c1015; color:#ff3366;">
                    <i class="fa-solid fa-lock" style="font-size:14px;"></i>
                    <span style="font-size:7.5px; margin-top:2px; font-weight:700;">LOCKED</span>
                </div>
            `;
        } else {
            card.innerHTML = `<img src="${photo.url}" class="thumb-img" alt="${photo.filename}">`;
        }

        card.addEventListener("click", () => selectPhoto(photo));
        track.appendChild(card);
    });

    document.getElementById("filmstrip-left")?.addEventListener("click", () => track.scrollBy({ left: -200, behavior: "smooth" }));
    document.getElementById("filmstrip-right")?.addEventListener("click", () => track.scrollBy({ left: 200, behavior: "smooth" }));
    document.getElementById("input-import-photos")?.addEventListener("change", handleImportPhotos);
}

async function handleImportPhotos(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append("files", files[i]);
    }

    try {
        const res = await fetch("/api/catalog/import", { method: "POST", body: formData });
        const data = await res.json();
        if (data.success) {
            await loadCatalog();
            if (data.imported && data.imported.length > 0) {
                const newP = appState.catalog.find(p => p.filename === data.imported[0]);
                if (newP) selectPhoto(newP);
            }
        }
    } catch (err) {
        alert("Gagal impor foto: " + err.message);
    } finally {
        e.target.value = "";
    }
}

async function deletePhotoPrompt(filename) {
    const ok = confirm(`Hapus foto "${filename}" secara permanen dari katalog dan disk?`);
    if (!ok) return;

    try {
        const formData = new FormData();
        formData.append("filename", filename);
        const res = await fetch("/api/catalog/delete", { method: "POST", body: formData });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Gagal menghapus file!");

        if (appState.activePhoto && appState.activePhoto.filename === filename) {
            appState.activePhoto = null;
            appState.activeImg = null;
        }
        await loadCatalog();
        alert(`🗑️ Berkas "${filename}" berhasil dihapus.`);
    } catch (err) {
        alert("Gagal menghapus: " + err.message);
    }
}

// ==============================================================================
// 10. MODAL DIALOGS: RENAME & AUTHENTICATION
// ==============================================================================
function initRenameModal() {
    const modal = document.getElementById("modal-rename");
    const btnClose = document.getElementById("btn-close-modal-rename");
    const btnCancel = document.getElementById("btn-cancel-rename");
    const btnConfirm = document.getElementById("btn-confirm-rename");

    if (btnClose) btnClose.addEventListener("click", closeRenameModal);
    if (btnCancel) btnCancel.addEventListener("click", closeRenameModal);

    if (btnConfirm) {
        btnConfirm.addEventListener("click", async () => {
            const oldName = document.getElementById("rename-old-name").value.trim();
            const newName = document.getElementById("rename-new-name").value.trim();
            if (!newName || oldName === newName) {
                closeRenameModal();
                return;
            }

            try {
                const formData = new FormData();
                formData.append("old_filename", oldName);
                formData.append("new_filename", newName);

                const res = await fetch("/api/catalog/rename", { method: "POST", body: formData });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Gagal rename!");

                closeRenameModal();
                await loadCatalog();
                alert(`✅ Nama berhasil diubah ke: ${data.new_filename}`);
            } catch (err) {
                alert("Gagal rename: " + err.message);
            }
        });
    }
}

function openRenameModal(filename) {
    renameTargetFilename = filename;
    const modal = document.getElementById("modal-rename");
    if (!modal) return;
    document.getElementById("rename-old-name").value = filename;
    document.getElementById("rename-new-name").value = filename;
    modal.style.display = "flex";
    setTimeout(() => document.getElementById("rename-new-name")?.focus(), 100);
}

function closeRenameModal() {
    const modal = document.getElementById("modal-rename");
    if (modal) modal.style.display = "none";
}

function stopAuthBiometricCamera() {
    if (authBioStream) {
        authBioStream.getTracks().forEach(track => track.stop());
        authBioStream = null;
    }
    const video = document.getElementById("modal-bio-video");
    if (video) {
        video.srcObject = null;
        video.style.display = "none";
    }
    const cameraButton = document.getElementById("btn-modal-bio-camera");
    const verifyButton = document.getElementById("btn-modal-bio-verify");
    if (cameraButton) cameraButton.textContent = "Buka Kamera";
    if (verifyButton) verifyButton.disabled = true;
}

function initAuthModal() {
    const modal = document.getElementById("modal-auth-prompt");
    const btnClose = document.getElementById("btn-close-modal-auth");
    const btnCancel = document.getElementById("btn-cancel-auth");
    const btnConfirm = document.getElementById("btn-confirm-auth");
    const passwordField = document.getElementById("modal-auth-password");

    // # FIX: integrasi biometrik wajib
    if (modal && passwordField && !document.getElementById("modal-biometric-section")) {
        const biometricSection = document.createElement("div");
        biometricSection.id = "modal-biometric-section";
        biometricSection.className = "form-item";
        biometricSection.style.marginBottom = "12px";
        biometricSection.innerHTML = `
            <label>Verifikasi wajah wajib:</label>
            <video id="modal-bio-video" autoplay playsinline muted
                style="display:none; width:100%; max-height:180px; margin:6px 0; border-radius:6px; background:#090a0c; object-fit:cover;"></video>
            <canvas id="modal-bio-canvas" style="display:none;"></canvas>
            <div class="btn-group" style="display:flex; gap:6px; margin-top:6px;">
                <button type="button" class="btn btn-outline btn-sm" id="btn-modal-bio-camera">Buka Kamera</button>
                <button type="button" class="btn btn-success btn-sm" id="btn-modal-bio-verify" disabled>Scan & Verifikasi Wajah</button>
            </div>
            <div id="modal-bio-feedback" style="font-size:11px; margin-top:6px; color:var(--text-muted);">Wajah yang cocok wajib dipindai sebelum password dikirim.</div>
        `;
        passwordField.closest(".form-item")?.insertAdjacentElement("beforebegin", biometricSection);
    }

    const cameraButton = document.getElementById("btn-modal-bio-camera");
    const verifyButton = document.getElementById("btn-modal-bio-verify");
    const video = document.getElementById("modal-bio-video");
    const canvas = document.getElementById("modal-bio-canvas");
    const biometricFeedback = document.getElementById("modal-bio-feedback");

    const showBiometricFeedback = (message, isSuccess = false) => {
        if (!biometricFeedback) return;
        biometricFeedback.textContent = message;
        biometricFeedback.style.color = isSuccess ? "var(--accent-green)" : "var(--accent-red)";
    };

    if (cameraButton) {
        cameraButton.addEventListener("click", async () => {
            if (authBioStream) {
                stopAuthBiometricCamera();
                authBiometricImageBase64 = null;
                authBiometricMatch = false;
                showBiometricFeedback("Kamera ditutup. Pindai wajah sebelum otorisasi.");
                return;
            }
            try {
                authBioStream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 }, audio: false });
                if (video) {
                    video.srcObject = authBioStream;
                    video.style.display = "block";
                    await video.play();
                }
                if (verifyButton) verifyButton.disabled = false;
                cameraButton.textContent = "Tutup Kamera";
                showBiometricFeedback("Kamera aktif. Posisikan wajah lalu tekan Scan & Verifikasi.");
            } catch (err) {
                showBiometricFeedback("Tidak dapat mengakses webcam: " + err.message);
            }
        });
    }

    if (verifyButton) {
        verifyButton.addEventListener("click", async () => {
            if (!video || !canvas || !authBioStream || video.videoWidth === 0) {
                showBiometricFeedback("Aktifkan kamera dan tunggu frame siap terlebih dahulu.");
                return;
            }
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageBase64 = canvas.toDataURL("image/jpeg", 0.85);
            authBiometricImageBase64 = null;
            authBiometricMatch = false;
            verifyButton.disabled = true;
            try {
                const result = await verifyBiometricImage(imageBase64);
                if (result.is_match !== true) {
                    showBiometricFeedback(result.message || "Wajah tidak cocok. Akses ditolak.");
                    return;
                }
                authBiometricImageBase64 = imageBase64;
                authBiometricMatch = true;
                showBiometricFeedback(result.message || "Wajah cocok. Masukkan password untuk melanjutkan.", true);
            } catch (err) {
                showBiometricFeedback("Verifikasi wajah gagal: " + err.message);
            } finally {
                verifyButton.disabled = false;
            }
        });
    }

    const closeAuth = (clearPending = true) => {
        if (modal) modal.style.display = "none";
        if (clearPending) pendingAuthCallback = null;
        stopAuthBiometricCamera();
        authBiometricImageBase64 = null;
        authBiometricMatch = false;
    };

    if (btnClose) btnClose.addEventListener("click", closeAuth);
    if (btnCancel) btnCancel.addEventListener("click", closeAuth);

    if (btnConfirm) {
        btnConfirm.addEventListener("click", async () => {
            const pwd = document.getElementById("modal-auth-password")?.value.trim();
            const errDiv = document.getElementById("modal-auth-error");
            if (!pwd) {
                if (errDiv) {
                    errDiv.textContent = "Kata sandi tidak boleh kosong!";
                    errDiv.style.display = "block";
                }
                return;
            }

            if (!authBiometricImageBase64 || authBiometricMatch !== true) {
                if (errDiv) {
                    errDiv.textContent = "Scan wajah yang cocok wajib berhasil sebelum password dapat membuka sesi.";
                    errDiv.style.display = "block";
                }
                return;
            }

            const ok = await executeUnlock(pwd, authBiometricImageBase64, authBiometricMatch);
            if (ok) {
                // # FIX: penyesuaian payload & state
                const callback = pendingAuthCallback;
                closeAuth(false);
                try {
                    if (callback) await callback();
                } finally {
                    pendingAuthCallback = null;
                }
            } else {
                if (errDiv) {
                    errDiv.textContent = "Kata sandi salah atau dongle belum terpasang!";
                    errDiv.style.display = "block";
                }
            }
        });
    }
}

function openAuthModal() {
    const modal = document.getElementById("modal-auth-prompt");
    const errDiv = document.getElementById("modal-auth-error");
    const pwdInput = document.getElementById("modal-auth-password");
    if (!modal) return;

    if (errDiv) errDiv.style.display = "none";
    if (pwdInput) pwdInput.value = "";
    stopAuthBiometricCamera();
    authBiometricImageBase64 = null;
    authBiometricMatch = false;
    const bioFeedback = document.getElementById("modal-bio-feedback");
    if (bioFeedback) bioFeedback.textContent = "Wajah yang cocok wajib dipindai sebelum password dikirim.";
    modal.style.display = "flex";
    setTimeout(() => pwdInput?.focus(), 100);
}
