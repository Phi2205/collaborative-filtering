@echo off
echo Starting Recommend Server...
echo.

REM Kích hoạt virtual environment
call venv\Scripts\activate.bat

REM Kiểm tra xem venv đã được kích hoạt chưa
if errorlevel 1 (
    echo ERROR: Khong the kich hoat virtual environment!
    echo Hay dam bao venv da duoc tao: python -m venv venv
    pause
    exit /b 1
)

echo Virtual environment activated.
echo.

REM Chạy server
python start.py

