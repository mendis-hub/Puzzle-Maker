@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM start.bat — One-command launcher for Puzzle Generator (Windows)
REM
REM Usage: Double-click start.bat or run from Command Prompt
REM ─────────────────────────────────────────────────────────────────────────────

echo Puzzle Generator — startup
echo.

REM Check for Python
where python3 >nul 2>&1
if %ERRORLEVEL%==0 (
    set PYTHON=python3
) else (
    where python >nul 2>&1
    if %ERRORLEVEL%==0 (
        set PYTHON=python
    ) else (
        echo ERROR: Python not found. Install Python 3.9+ and retry.
        pause
        exit /b 1
    )
)

echo Using: %PYTHON%
echo.

echo Installing dependencies...
%PYTHON% -m pip install -r requirements.txt --quiet

echo.
echo ============================================================
echo   Puzzle Generator - FastAPI server starting...
echo   Open your browser at: http://localhost:8000
echo ============================================================
echo.

%PYTHON% server.py
pause
