@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
call "%~dp0PREPARAR_ENTORNO.bat"
if errorlevel 1 goto :end
"%~dp0python\python.exe" -B "%~dp0exportar_historial.py"
:end
pause
