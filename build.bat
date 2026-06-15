@echo off
cd /d "%~dp0"

echo [1/3] Kiem tra PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Cai dat PyInstaller...
    pip install pyinstaller
)

echo [2/3] Tao logo.ico neu chua co...
python -c "from PIL import Image; img=Image.open('logo.png'); img.resize((32,32)).save('logo.ico',format='ICO')" 2>nul

echo [3/3] Dang build...
pyinstaller --noconfirm --onedir --windowed ^
    --name "ALGOBOT-TradingView" ^
    --icon "logo.ico" ^
    --add-data "logo.png;." ^
    --add-data "logo.ico;." ^
    --collect-all customtkinter ^
    --hidden-import MetaTrader5 ^
    --hidden-import flask ^
    --hidden-import werkzeug ^
    app.py

echo.
echo ========================================
echo Build xong! Thu muc: dist\ALGOBOT-TradingView
echo Zip thu muc do gui cho khach hang.
echo ========================================
pause
