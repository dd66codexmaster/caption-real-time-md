@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Windows实时字幕捕获工具 V2.0
echo ================================================
echo    Windows实时字幕捕获工具 V2.0
echo ================================================
echo 功能：多文件选择、实时字幕转写、文件命名
echo       Markdown导出、文本格式化、拖拽交互
echo 快捷键：Win+Ctrl+C 开启Windows实时字幕
echo ================================================
echo.
python subtitle_capture_v2.py
pause