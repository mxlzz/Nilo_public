@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title NILO - Laboratorio del motor
call "%~dp0PREPARAR_ENTORNO.bat"
if errorlevel 1 goto :fail
"%~dp0python\python.exe" -B "%~dp0laboratorio_motor.py"
if errorlevel 1 goto :fail
exit /b 0
:fail
echo.
echo No se pudo iniciar el laboratorio. Revisa el mensaje anterior.
pause
exit /b 1
