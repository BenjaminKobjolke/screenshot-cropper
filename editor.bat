@echo off
setlocal
rem Usage: editor.bat [project-directory]  (defaults to current directory)
set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=%CD%"
rem Run from repo root so uv finds the project and fonts/ resolves for text preview
pushd "%~dp0"
uv run python main.py --editor --directory "%TARGET%"
popd
