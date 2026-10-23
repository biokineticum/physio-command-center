@echo off
title Physio & Sports Command Center
cd /d "%~dp0"

echo =========================================================
echo            PHYSIO & SPORTS COMMAND CENTER
echo =========================================================
echo.

:: 1. Check & start Ollama in background if not already running
echo [*] Checking Ollama AI service...
tasklist /fi "imagename eq ollama app.exe" 2>nul | find /i "ollama app.exe" >nul
if errorlevel 1 (
    tasklist /fi "imagename eq ollama.exe" 2>nul | find /i "ollama.exe" >nul
    if errorlevel 1 (
        if exist "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe" (
            echo [*] Starting Ollama in system tray...
            start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
            timeout /t 3 /nobreak >nul
        )
    )
)

:: 2. Launch Streamlit Web App
echo [*] Starting web interface...
echo [*] Opening your browser at http://localhost:8501
echo.
echo [INFO] Keep this window open while using the app.
echo [INFO] Close this window when you want to stop the application.
echo =========================================================
echo.

python -m streamlit run app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application failed to start or crashed.
    echo Press any key to exit.
    pause >nul
)
