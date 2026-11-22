param(
  [string]$OutputDirectory = "$PSScriptRoot\backups"
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
  throw 'Define DATABASE_URL antes de ejecutar este script.'
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outputFile = Join-Path $OutputDirectory "agave_full_$timestamp.dump"

pg_dump --format=custom --no-owner --no-privileges --file $outputFile $env:DATABASE_URL

Write-Host "Respaldo guardado en: $outputFile"

