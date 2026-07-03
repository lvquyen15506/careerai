<#
Simple PowerShell helper to create a local `.env` from `.env.example`.
Usage: Open PowerShell in repo root and run: `.	emplates\init-env.ps1` or `./scripts/init-env.ps1`
#>
Param()

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$example = Join-Path $repoRoot ".env.example"
$target = Join-Path $repoRoot ".env"

if (-not (Test-Path $example)) {
    Write-Error ".env.example not found in $repoRoot"
    exit 1
}

if (Test-Path $target) {
    $bak = "$target.bak_$(Get-Date -Format yyyyMMddHHmmss)"
    Write-Host ".env already exists — backing up to $bak"
    Copy-Item -Path $target -Destination $bak -Force
}

Copy-Item -Path $example -Destination $target -Force

# Generate a strong Django secret key and replace placeholder if present
try {
    $secret = & python -c "import secrets;print(secrets.token_hex(32))"
} catch {
    Write-Warning "Python not found or failed to generate secret; please edit .env and set DJANGO_SECRET_KEY yourself."
    exit 0
}

(Get-Content $target) -replace 'DJANGO_SECRET_KEY=.+','DJANGO_SECRET_KEY=' + $secret | Set-Content $target -Force

Write-Host "Created $target (DJANGO_SECRET_KEY set). Edit to fill DB and other secrets."