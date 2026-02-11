@echo off
echo ========================================
echo   CryptoMentor - Educational Trading Bot
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Setting up Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created!
) else (
    echo Virtual environment already exists.
)

echo.
echo [2/3] Installing Python dependencies...
call venv\Scripts\activate
pip install -r backend\requirements.txt --quiet

echo.
echo [3/3] Starting backend server...
echo.
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo To start frontend, open a NEW terminal and run:
echo   cd "%~dp0frontend"
echo   npm install
echo   npm run dev
echo.
echo Then open: http://localhost:3000
echo ========================================
echo.

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
