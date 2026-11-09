@echo off
title Darkroom Launcher
echo ===================================================
echo    MEMULAI DARKROOM SUITE
echo ===================================================
if exist Darkroom\run.py (
    python run.py
) else (
    python app.py
)
pause
