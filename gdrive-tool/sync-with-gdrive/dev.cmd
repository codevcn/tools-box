@echo off
REM ================================
REM  SynRive - Dev launcher
REM ================================

REM Luôn chạy từ root project
cd /d %~dp0

REM (Tuỳ chọn) kích hoạt venv
REM call .venv\Scripts\activate

REM Chạy app qua entrypoint
python run_app.py %*