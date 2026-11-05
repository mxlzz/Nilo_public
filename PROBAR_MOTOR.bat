@echo off
setlocal
cd /d "%~dp0"
if exist "python\python.exe" ("python\python.exe" validar_escenarios.py --output "diagnostico_motor.json" & goto :end)
if exist "entorno\python\python.exe" ("entorno\python\python.exe" validar_escenarios.py --output "diagnostico_motor.json" & goto :end)
python validar_escenarios.py --output "diagnostico_motor.json"
:end
pause
