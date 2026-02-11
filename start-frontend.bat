@echo off
echo ========================================
echo   CryptoMentor - Frontend
echo ========================================
echo.

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

echo Starting frontend...
echo Open: http://localhost:3000
echo.

npm run dev
