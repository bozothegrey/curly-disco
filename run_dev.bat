@echo off
REM Initialize Conda for cmd.exe
call %USERPROFILE%\miniconda3\Scripts\activate.bat
call conda activate base

REM Start backend in debug mode
echo Starting backend server in debug mode...
cd backend
start "Backend Server" python app.py debug
cd ..

REM Start frontend server
echo Starting frontend server...
cd docs
start "Frontend Server" python -m http.server 8000
cd ..

echo Servers running:
echo - Backend: http://localhost:10000
echo - Frontend: http://localhost:8000
echo.
echo Press any key to stop servers...
pause >nul

REM Kill background processes
taskkill /FI "WINDOWTITLE eq Backend Server" /F
taskkill /FI "WINDOWTITLE eq Frontend Server" /F
