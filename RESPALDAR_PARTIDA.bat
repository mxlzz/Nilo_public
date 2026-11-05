@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
call "%~dp0PREPARAR_ENTORNO.bat"
if errorlevel 1 goto :fail
"%~dp0python\python.exe" -B "%~dp0gestionar_partidas.py" backup
if errorlevel 1 goto :fail
echo.
echo Operacion completada.
pause
exit /b 0
:fail
echo.
echo La operacion no pudo completarse. Revisa el mensaje anterior.
pause
exit /b 1
