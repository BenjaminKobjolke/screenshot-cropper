@echo off
echo Activating virtual environment...
call %~dp0\.venv\Scripts\activate.bat
echo.
echo Virtual environment activated!
echo You can now run Python commands with the virtual environment.
echo.
cmd /k
