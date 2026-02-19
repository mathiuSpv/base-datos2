if (Test-Path ".\backend") {
  Set-Location ".\backend"
}

uvicorn edugrade.main:app --reload --app-dir src