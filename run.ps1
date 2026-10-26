Set-Location $PSScriptRoot
docker compose up -d --build
Start-Process "http://localhost:8000"
