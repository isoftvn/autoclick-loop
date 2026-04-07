@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv-win\Scripts\python.exe" (
    py -3 -m venv .venv-win
)

call ".venv-win\Scripts\activate.bat"
if errorlevel 1 exit /b 1

python -m pip install --upgrade pip
if errorlevel 1 exit /b 1

python -m pip install pyinstaller pyautogui pillow pyscreeze pymsgbox pytweening mouseinfo pygetwindow pyrect pyperclip
if errorlevel 1 exit /b 1

if not exist "logo.ico" (
    python -c "from PIL import Image; Image.open('logo.png').save('logo.ico')"
)

set ICON_ARG=
if exist "logo.ico" set ICON_ARG=--icon logo.ico

pyinstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name AutoClickLoop ^
  --add-data "logo.png;." ^
  --add-data "logo-app.png;." ^
  %ICON_ARG% ^
  app.py

endlocal
