@echo off
if exist "%~dp0runtime\python\pythonw.exe" (
  start "" "%~dp0runtime\python\pythonw.exe" "%~dp0launch.pyw"
  exit /b 0
)
where pythonw.exe >nul 2>nul
if errorlevel 1 (
  powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Install Python 3.11+ (including tkinter), then open this launcher again.','Director Desk')"
  exit /b 1
)
start "" pythonw.exe "%~dp0launch.pyw"
