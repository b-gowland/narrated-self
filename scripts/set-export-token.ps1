# Creates the EXPORT_TOKEN secret shared by the Worker and the nightly GitHub Action.
# The token is generated here and passed straight to both places; it is never printed or saved to disk.
# Run once, after `npx.cmd wrangler login` and with the GitHub CLI logged in, from any folder:
#   powershell -ExecutionPolicy Bypass -File C:/dev/narrated-self/scripts/set-export-token.ps1

$ErrorActionPreference = "Stop"
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$token = -join ($bytes | ForEach-Object { $_.ToString("x2") })

Push-Location (Join-Path $PSScriptRoot "..\worker")
try {
    $token | npx.cmd wrangler secret put EXPORT_TOKEN | Out-Null
    Write-Host "Set EXPORT_TOKEN on the Cloudflare Worker."
} finally {
    Pop-Location
}
$token | gh secret set EXPORT_TOKEN --repo b-gowland/narrated-self
Write-Host "Set EXPORT_TOKEN as a GitHub Actions secret."
Remove-Variable token, bytes
