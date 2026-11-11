Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "   CODEBASE COPILOT - AI FOR GITHUB REPOSITORIES" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt
Write-Host ""
Write-Host "Starting Codebase Copilot on http://localhost:5000 ..." -ForegroundColor Green
Start-Process "http://localhost:5000"
python app.py
