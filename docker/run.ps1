$ErrorActionPreference = "Stop"

$composeFile = "docker/compose.yml"

function Test-DockerRunning {
  try {
    docker info | Out-Null
    return $true
  }
  catch {
    return $false
  }
}

Write-Host "==> Using compose file: $composeFile"

# 0) Validar Docker daemon
if (-not (Test-DockerRunning)) {
  Write-Host ""
  Write-Host "ERROR: Docker engine is not reachable from this terminal." -ForegroundColor Red
  Write-Host "Fix:" -ForegroundColor Yellow
  Write-Host "  1) Start Docker Desktop (wait until it says Running)"
  Write-Host "  2) Ensure you are using Linux containers (WSL2 engine)"
  Write-Host "  3) Then re-run this script"
  Write-Host ""
  Write-Host "Debug commands:"
  Write-Host "  docker version"
  Write-Host "  docker info"
  Write-Host "  docker context ls"
  exit 1
}

# 1) Baja el stack si existe (no falla si no está corriendo)
Write-Host "==> Stopping existing stack (if any)..."
try {
  docker compose -f $composeFile down --remove-orphans | Out-Null
}
catch {
  Write-Host "==> down (non-fatal): $($_.Exception.Message)"
}

# 2) BORRA TODO (incluye volúmenes) => resetea Mongo desde cero
# ⚠️ Esto elimina mongo_data y cualquier dato persistido
Write-Host "==> Removing volumes (full reset)..."
try {
  docker compose -f $composeFile down -v --remove-orphans | Out-Null
}
catch {
  Write-Host "==> down -v (non-fatal): $($_.Exception.Message)"
}

# 3) Por si quedó el contenedor por nombre (best effort)
Write-Host "==> Cleaning any leftover containers (best effort)..."
try {
  docker rm -f edugrade-mongodb 2>$null | Out-Null
}
catch {}

# 4) Levanta y recrea
Write-Host "==> Starting stack from scratch..."
docker compose -f $composeFile up -d --force-recreate

# 5) Estado
Write-Host "==> Current status:"
docker compose -f $composeFile ps

# 6) Logs del seeder para confirmar inserción
Write-Host "==> Seeder Basic"
docker compose -f $composeFile logs --no-color mongo-init-data
Write-Host "==> Done."