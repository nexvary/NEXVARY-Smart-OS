@echo off
setlocal
cd /d "%~dp0"
py -3.12 -m venv .venv
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m pip install .
if errorlevel 1 goto fail
".venv\Scripts\smart-windows-driver.exe"
exit /b %errorlevel%
:fail
echo Failed. Python 3.12 x64 and Internet are required for first-time setup.
pause
exit /b 1
