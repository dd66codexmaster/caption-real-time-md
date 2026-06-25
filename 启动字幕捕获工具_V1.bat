@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Windows实时字幕捕获工具 V1.0
echo ================================================
echo    Windows实时字幕捕获工具 V1.0
echo ================================================
echo 功能：实时捕获Windows系统字幕，保存历史记录
echo 快捷键：Win+Ctrl+C 开启Windows实时字幕
echo ================================================
echo.
python subtitle_capture.py
pause