@echo off
setlocal
chcp 65001 >nul
if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" "%~dp0launcher.py" %*
) else (
  py -3 "%~dp0launcher.py" %*
)
set "TASK_RESULT=%ERRORLEVEL%"
if not "%TASK_RESULT%"=="0" echo See PORTABLE_GUIDE.md for dependency setup.
pause
exit /b %TASK_RESULT%
