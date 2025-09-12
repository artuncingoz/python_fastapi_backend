# bootstrap-compose.ps1
# Build images, start Docker Compose, wait until the API is ready, then open Swagger.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Info($m){ Write-Host "==> $m" -ForegroundColor Cyan }

# 0) Check Docker
Info "Checking Docker..."
docker version | Out-Null

# 1) Ensure .env exists
if (-not (Test-Path ".env")) {
  if (Test-Path ".env.example") {
    Info "Creating .env from .env.example"
    Copy-Item ".env.example" ".env"
  } else {
    throw ".env not found and .env.example missing. Create a .env first."
  }
}

# 2) Fresh start (remove old containers; keep volumes)
Info "Stopping previous stack (if any)..."
docker compose down --remove-orphans

# 3) Build
Info "Building images..."
docker compose build

# 4) Up
Info "Starting stack..."
docker compose up -d

# 5) Wait for health
$healthUrl = "http://localhost:8000/health"
$maxTries = 60
$ok = $false
for ($i=1; $i -le $maxTries; $i++) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 3
    if ($r.StatusCode -eq 200) { $ok = $true; break }
  } catch {}
  Start-Sleep -Seconds 2
}
if (-not $ok) {
  Write-Warning "API did not become healthy. Showing recent logs:"
  docker compose logs --tail=200 api
  throw "API health check failed at $healthUrl"
}

Info "API is healthy at $healthUrl"
Info "Opening Swagger UI..."
Start-Process "http://localhost:8000/docs"

Info "Done. To follow logs:"
Write-Host "  docker compose logs -f api" -ForegroundColor Yellow
Write-Host "  docker compose logs -f worker" -ForegroundColor Yellow
