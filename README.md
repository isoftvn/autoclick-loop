# Auto Click Loop

Tool desktop Python dùng để tạo và chạy automation click theo step, có hỗ trợ delay, lấy tọa độ chuột, click theo tọa độ, tìm ảnh rồi click, và chạy lặp nhiều vòng.

## Chạy source

```bash
cd /Users/m3pro/ezp/autoclick-loop
.venv/bin/python app.py
```

Nếu chưa có dependency:

```bash
cd /Users/m3pro/ezp/autoclick-loop
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Lưu ý trên macOS:
- Cần cấp quyền `Accessibility` cho Terminal hoặc app Python.
- Nếu icon trên Dock chưa refresh khi chạy source, có thể chạy `killall Dock`.

## Build macOS

Build app `.app` bằng PyInstaller:

```bash
cd /Users/m3pro/ezp/autoclick-loop
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

## Windows code signing

Workflow GitHub Actions đã hỗ trợ ký số file Windows `.exe` bằng Azure Trusted Signing nếu repo có đủ secrets sau:

```text
AZURE_TENANT_ID
AZURE_CLIENT_ID
AZURE_CLIENT_SECRET
TRUSTED_SIGNING_ENDPOINT
TRUSTED_SIGNING_ACCOUNT_NAME
TRUSTED_SIGNING_CERTIFICATE_PROFILE_NAME
```

Khi các secrets này được cấu hình trong GitHub repository settings, workflow build Windows sẽ tự ký `AutoClickLoop.exe` trước khi upload artifact và tạo Release.

## Asset icon

- `logo-app.png`: icon dùng khi chạy `python3 app.py`
- `logo.icns`: icon dùng cho macOS app bundle
- `logo.png`: ảnh nguồn để generate icon và đóng gói cùng app
