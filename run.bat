@echo off
echo Running Screenshot Cropper...
echo.
echo Usage: uv run python main.py --directory path/to/your/directory
echo.
echo Example: uv run python main.py --directory test
echo.

set /p directory=Enter directory path:

if "%directory%"=="" (
    echo No directory specified. Exiting.
    pause
    exit /b
)

uv run python main.py --directory %directory%
echo.
pause
