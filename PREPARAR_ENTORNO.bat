@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if exist "%~dp0python\python.exe" goto :verify

echo.
echo Nilo necesita preparar su motor Python portable (solo la primera vez).
echo Se guardara dentro de esta carpeta, sin instalar Python en Windows.
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0OBTENER_PYTHON.ps1"
if errorlevel 1 (
 echo.
 echo No se pudo preparar el motor portable.
 echo Lee LEEME_PORTABLE.txt para descargarlo manualmente.
 exit /b 1
)

:verify
if not exist "%~dp0python\python312.zip" (
 echo ERROR: Falta python\python312.zip. La carpeta Python puede estar incompleta.
 exit /b 1
)
if not exist "%~dp0python\python312._pth" (
 echo ERROR: Falta python\python312._pth.
 exit /b 1
)
"%~dp0python\python.exe" -I -c "import sqlite3, ssl, urllib.request; print('Motor portable Python listo.')"
if errorlevel 1 (
 echo ERROR: El motor portable no pudo iniciarse en esta computadora.
 exit /b 1
)
exit /b 0
