@echo off
setlocal
cd /d "%~dp0"
py -3.12 -m venv .venv-linux
if errorlevel 1 goto fail
".venv-linux\Scripts\python.exe" -m pip install ".[linux]"
if errorlevel 1 goto fail
".venv-linux\Scripts\smart-linux-installer.exe"
exit /b %errorlevel%
:fail
echo Failed. Python 3.12 x64 and Internet are required for first-time setup.
pause
exit /b 1
