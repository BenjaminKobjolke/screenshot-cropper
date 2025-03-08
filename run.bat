@echo off
echo Activating virtual environment...
call %~dp0\venv\Scripts\activate.bat
echo.

echo Running Screenshot Cropper...
echo.
echo Usage: python main.py --directory path/to/your/directory
echo.
echo Example: python main.py --directory test
echo.

set /p directory=Enter directory path: 

if "%directory%"=="" (
    echo No directory specified. Exiting.
    pause
    exit /b
)

call python main.py --directory %directory%
echo.
pause
