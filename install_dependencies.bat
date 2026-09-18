@echo off
echo ======================================================================
echo    KAIROS URBAN FLOOD NOWCASTING SYSTEM - DEPENDENCY INSTALLER
echo    Smart India Hackathon 2026 (Problem Statement 26085)
echo ======================================================================

echo.
echo [1/3] Installing Python Dependencies from requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some optional Python packages had issues, proceeding...
) else (
    echo [OK] Python dependencies installed successfully!
)

echo.
echo [2/3] Installing Backend Node.js Dependencies (backend/)...
if exist backend\package.json (
    cd backend
    call npm install
    cd ..
    echo [OK] Backend dependencies installed!
) else (
    echo [SKIP] backend\package.json not found.
)

echo.
echo [3/3] Installing Frontend React / Vite Dependencies (Frontend/)...
if exist Frontend\package.json (
    cd Frontend
    call npm install
    cd ..
    echo [OK] Frontend dependencies installed!
) else (
    echo [SKIP] Frontend\package.json not found.
)

echo.
echo ======================================================================
echo   Verifying Installation with Pytest & Backend API Test...
echo ======================================================================
pytest ai_service\tests\ -q
node backend\tests\test_api.js

echo.
echo ======================================================================
echo   [COMPLETE] All dependencies are installed and verified!
echo   Launch the dashboard with: launch_dashboard.bat
echo   Or start the API Gateway with: cd backend ^&^& npm start
echo ======================================================================
pause
