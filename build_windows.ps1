$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv-win\Scripts\python.exe")) {
    py -3 -m venv .venv-win
}

& ".venv-win\Scripts\Activate.ps1"

python -m pip install --upgrade pip
python -m pip install pyinstaller pyautogui pillow pyscreeze pymsgbox pytweening mouseinfo pygetwindow pyrect pyperclip

if (-not (Test-Path "logo.ico")) {
    python -c "from PIL import Image; Image.open('logo.png').save('logo.ico')"
}

$iconArgs = @()
if (Test-Path "logo.ico") {
    $iconArgs = @("--icon", "logo.ico")
}

python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name AutoClickLoop `
  --add-data "logo.png;." `
  --add-data "logo-app.png;." `
  @iconArgs `
  app.py
