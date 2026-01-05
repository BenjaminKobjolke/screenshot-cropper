@echo off
echo Creating virtual environment...
python -m venv venv
echo.

echo Activating virtual environment...
%~dp0\venv\Scripts\activate.bat
echo.

echo Installing dependencies...
pip install -r requirements.txt
echo.

echo Installing adobe-document-handler from local sibling directory...
pip install -e ..\adobe-document-handler[all]
echo.

echo Installation completed successfully (local development mode)!
echo To run the application, use run.bat
pause
