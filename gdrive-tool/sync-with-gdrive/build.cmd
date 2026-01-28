@echo off
REM ================================
REM  SynRive - Build script
REM  Build type: PyInstaller one-folder
REM ================================

REM Chạy từ thư mục chứa file này
cd /d %~dp0

REM (Optional) kích hoạt venv build
REM call .venv-build\Scripts\activate

REM Dọn build cũ (tránh nhiễu)
rmdir /s /q build
rmdir /s /q dist

REM Build
pyinstaller ^
  --onedir ^
  --name SynRive ^
  --noconsole ^
  --add-binary "app\build\bin\rclone.exe;." ^
  run_app.py

echo.
echo ================================
echo  BUILD FINISHED
echo  Output: dist\SynRive\
echo ================================

pause
