@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title NILO - Edicion portable
call "%~dp0PREPARAR_ENTORNO.bat"
if errorlevel 1 goto :fail
"%~dp0python\python.exe" -B "%~dp0primer_inicio.py"
if errorlevel 1 goto :fail
"%~dp0python\python.exe" -B "%~dp0nilo.py"
if errorlevel 1 goto :fail
exit /b 0
:fail
echo.
echo Nilo no se inicio. Revisa el mensaje anterior.
pause
exit /b 1
