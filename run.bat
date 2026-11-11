@echo off
title Codebase Copilot - AI for GitHub Repositories
echo =======================================================
echo    CODEBASE COPILOT - AI FOR GITHUB REPOSITORIES
echo =======================================================
echo.
echo Installing dependencies...
python -m pip install -r requirements.txt
echo.
echo Starting application server...
start http://localhost:5000
python app.py
pause
