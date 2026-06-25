@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Windows实时字幕捕获工具 V3.0
echo ================================================
echo    Windows实时字幕捕获工具 V3.0
echo ================================================
echo 功能：多文件选择、实时字幕转写、文件命名
echo       Markdown导出、文本格式化、自动保存
echo       编辑区工具栏优化、复制全部内容
echo 快捷键：Win+Ctrl+C 开启Windows实时字幕
echo ================================================
echo.
python subtitle_capture_v3.py
pause