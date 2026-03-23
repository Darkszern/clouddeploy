@echo off
title LXCC Cloud Deploy - Build Installer
echo =============================================================================
echo  LXCC Cloud Deploy - Build Installer
echo =============================================================================
echo.
echo  This script builds the complete installer in 2 steps:
echo    Step 1: PyInstaller  -> builds DeployTool.exe
echo    Step 2: Inno Setup   -> packages everything into Setup EXE
echo.
echo =============================================================================
echo.

:: ---- Step 0: Check prerequisites ----
echo [Step 0] Checking prerequisites...

python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo         Download: https://www.python.org/downloads/
    echo         Make sure "Add Python to PATH" is checked.
    pause
    exit /b 1
)
echo    [OK] Python found

:: Check for Inno Setup
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
)

if "%ISCC%"=="" (
    echo [ERROR] Inno Setup 6 is not installed!
    echo         Download: https://jrsoftware.org/isdl.php
    echo         Install it, then run this script again.
    pause
    exit /b 1
)
echo    [OK] Inno Setup found: %ISCC%
echo.

:: ---- Step 1: Build EXE with PyInstaller ----
echo [Step 1] Installing Python dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install paramiko pyinstaller >nul 2>&1
echo    [OK] Dependencies installed
echo.

echo [Step 1] Building DeployTool.exe with PyInstaller...
echo          This may take 1-3 minutes...

:: Clean previous build
if exist dist rmdir /s /q dist >nul 2>&1
if exist build rmdir /s /q build >nul 2>&1
if exist DeployTool.spec del DeployTool.spec >nul 2>&1

:: Build
if exist "%~dp0LXCCLOGO.ico" (
    pyinstaller --onefile --windowed --name "DeployTool" --icon="%~dp0LXCCLOGO.ico" "%~dp0cdpl.py"
) else (
    pyinstaller --onefile --windowed --name "DeployTool" "%~dp0cdpl.py"
)

if %errorLevel% neq 0 (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)

if not exist "dist\DeployTool.exe" (
    echo [ERROR] DeployTool.exe was not created!
    pause
    exit /b 1
)
echo    [OK] DeployTool.exe built successfully
echo.

:: ---- Step 2: Build Installer with Inno Setup ----
echo [Step 2] Building installer with Inno Setup...

:: Create output directory
if not exist dist_installer mkdir dist_installer

"%ISCC%" "%~dp0installer.iss"

if %errorLevel% neq 0 (
    echo [ERROR] Inno Setup compilation failed!
    pause
    exit /b 1
)
echo    [OK] Installer built successfully
echo.

:: ---- Cleanup ----
echo [Cleanup] Removing temporary build files...
if exist build rmdir /s /q build >nul 2>&1
if exist DeployTool.spec del DeployTool.spec >nul 2>&1
echo    [OK] Cleaned up
echo.

:: ---- Done ----
echo =============================================================================
echo  BUILD COMPLETE!
echo =============================================================================
echo.
echo  Installer EXE:  dist_installer\LXCC_CloudDeploy_Setup_v1.21.0.exe
echo  Standalone EXE:  dist\DeployTool.exe
echo.
echo  You can distribute the Setup EXE to users.
echo =============================================================================
echo.
pause
