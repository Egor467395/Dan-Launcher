@echo off
echo Starting Dan Launcher...
echo.

REM Check if venv exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing requirements...
    pip install -r requirements.txt
)

echo.
echo Launching Dan Launcher...
python launcher.py

pause

