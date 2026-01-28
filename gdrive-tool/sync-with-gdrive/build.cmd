@echo off
setlocal enableextensions

REM ================================
REM  SynRive - Build script
REM  Build type: PyInstaller one-folder
REM ================================

REM --- Kill app nếu đang chạy (tránh file lock) ---
taskkill /F /IM SynRive.exe >nul 2>&1

REM Cho Defender/Explorer nhả handle (nhẹ)
timeout /t 1 /nobreak >nul

REM Chạy từ thư mục chứa file này
cd /d %~dp0

REM (Optional) kích hoạt venv build
REM call .venv-build\Scripts\activate

REM ================================
REM  Clean old build
REM ================================
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM ================================
REM  Build with PyInstaller
REM ================================
pyinstaller ^
  --onedir ^
  --name SynRive ^
  --noconsole ^
  --icon "app_logo.ico" ^
  --version-file app/metadata/version_info.txt ^
  --add-binary "app\build\bin\rclone.exe;." ^
  run_app.py

if errorlevel 1 (
  echo.
  echo ================================
  echo  BUILD FAILED
  echo ================================
  pause
  exit /b 1
)

echo.
echo ================================
echo  BUILD FINISHED
echo  Output: dist\SynRive\
echo ================================

REM ================================
REM  Copy to testing directory (ROBUST)
REM ================================
set "SRC_DIR=%cd%\dist\SynRive"
set "DST_DIR=D:\D-Testing\SynRive"

if not exist "%SRC_DIR%" (
  echo.
  echo [ERROR] Source dir not found: "%SRC_DIR%"
  pause
  exit /b 1
)

REM Xóa thư mục test cũ
if exist "%DST_DIR%" (
  del /f /q "%DST_DIR%\SynRive.exe"
  rmdir /s /q "%DST_DIR%" 2>nul
  echo.
  echo [INFO] Deleted old test dir: "%DST_DIR%"
)

REM ================================
REM  Resolve & log copy paths
REM ================================
for %%I in ("%SRC_DIR%") do set "SRC_DIR_ABS=%%~fI"
for %%I in ("%DST_DIR%") do set "DST_DIR_ABS=%%~fI"

echo.
echo ================================
echo  COPY BUILD OUTPUT
echo  From: %SRC_DIR_ABS%
echo  To  : %DST_DIR_ABS%
echo ================================

REM Copy bằng robocopy
robocopy "%SRC_DIR%" "%DST_DIR%" /MIR /R:2 /W:1 /NFL /NDL /NJH /NJS

REM robocopy exit code:
REM 0–7 = OK, >=8 = ERROR
if %ERRORLEVEL% GEQ 8 (
  echo.
  echo [ERROR] Robocopy failed with code %ERRORLEVEL%
  pause
  exit /b 1
)

echo.
echo ================================
echo  COPIED TO: %DST_DIR%
echo ================================

pause
endlocal
