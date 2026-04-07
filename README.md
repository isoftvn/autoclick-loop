# Auto Click Loop

Tool desktop Python dùng để tạo và chạy automation click theo step, có hỗ trợ delay, lấy tọa độ chuột, click theo tọa độ, tìm ảnh rồi click, và chạy lặp nhiều vòng.

## Chạy source

```bash
cd /Users/m3pro/ezp/automation
python3 app.py
```

Nếu chưa có dependency:

```bash
cd /Users/m3pro/ezp/automation
python3 -m venv .venv
source .venv/bin/activate
pip install pyautogui pillow pyscreeze pymsgbox pytweening mouseinfo pygetwindow pyrect pyperclip pyobjc-core pyobjc-framework-quartz
python3 app.py
```

Lưu ý trên macOS:
- Cần cấp quyền `Accessibility` cho Terminal hoặc app Python.
- Nếu icon trên Dock chưa refresh khi chạy source, có thể chạy `killall Dock`.

## Build macOS

Build app `.app` bằng PyInstaller:

```bash
cd /Users/m3pro/ezp/automation
.venv/bin/pyinstaller -y AutoClickLoop.spec
```

Output:

```bash
dist/AutoClickLoop.app
```

## Build Windows

Build trên chính máy Windows.

CMD:

```bat
build_windows.bat
```

PowerShell:

```powershell
.\build_windows.ps1
```

Output:

```text
dist\AutoClickLoop\AutoClickLoop.exe
```

## Asset icon

- `logo-app.png`: icon dùng khi chạy `python3 app.py`
- `logo.icns`: icon dùng cho macOS app bundle
- `logo.png`: ảnh nguồn để generate icon và đóng gói cùng app
