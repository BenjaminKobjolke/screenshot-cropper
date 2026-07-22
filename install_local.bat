@echo off
echo ========================================
echo  Screenshot Cropper - Local Dev Setup
echo ========================================
echo.

:: Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: uv is not installed or not in PATH
    echo Please install uv first: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

echo [1/2] Creating virtual environment and installing dependencies...
uv sync --all-extras
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to sync dependencies
    pause
    exit /b 1
)

echo.
echo [2/2] Installing adobe-document-handler from local sibling directory...
uv pip install -e "..\adobe-document-handler[all]"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install local adobe-document-handler
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Setup complete (local development mode)
echo ========================================
echo NOTE: running "uv sync" later reverts adobe-document-handler
echo to the git version - re-run this script afterwards.
echo.
pause
