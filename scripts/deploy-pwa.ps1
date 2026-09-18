# Deploy gate for contexia-app -> repo-root build artifact -> Vercel.
#
# Exists because the same 3 bugs hit production 4 times on 2026-09-17
# (f6ac8bc, 5d82e8d, 1a5d219 in git log; 531690b is the follow-up fix):
#   1. app/ (build artifact) synced but _next/static/<hash>/ chunks left
#      untracked -> pages ship with 404-ing JS/CSS.
#   2. New -v2/-named routes have no matching rewrite in vercel.json ->
#      catch-all /app/:path* -> /404.html.
#   3. sw.js CACHE_VERSION never bumped even though the build changed
#      cached assets -> returning visitors keep serving the old shell.
# This script makes (1) and (3) impossible to skip by accident, and
# forces a `git status` review before anything is committed. It does NOT
# commit or push for you -- you still choose what to stage.
#
# Usage:
#   pwsh scripts/deploy-pwa.ps1                  # build, bump, sync, review
#   pwsh scripts/deploy-pwa.ps1 -SkipBuild        # already built, just sync
#   pwsh scripts/deploy-pwa.ps1 -SkipBump         # you bumped CACHE_VERSION yourself

param(
    [switch]$SkipBuild,
    [switch]$SkipBump
)

$ErrorActionPreference = "Stop"
$repoRoot = "C:\Users\contexia\Projects\antigravity-app"
$appDir = Join-Path $repoRoot "contexia-app"

function Fail($msg) {
    Write-Host "FAIL: $msg" -ForegroundColor Red
    exit 1
}

function Build {
    Write-Host "==> npm run build (contexia-app)" -ForegroundColor Cyan
    Push-Location $appDir
    npm run build
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) { Fail "npm run build exited $code" }
}

if (-not $SkipBuild) { Build }

$bumped = $false
if (-not $SkipBump) {
    $swSource = Join-Path $appDir "public\sw.js"
    if (-not (Test-Path $swSource)) { Fail "Not found: $swSource" }
    $content = Get-Content $swSource -Raw
    if ($content -notmatch 'CACHE_VERSION\s*=\s*"v(\d+)-') {
        Fail "Could not find CACHE_VERSION in $swSource -- bump it manually and re-run with -SkipBump"
    }
    $currentNum = [int]$Matches[1]
    $nextNum = $currentNum + 1
    $today = Get-Date -Format "yyyy-MM-dd"
    $newVersion = "v$nextNum-$today"
    $replacement = 'CACHE_VERSION = "' + $newVersion + '"'
    $updated = $content -replace 'CACHE_VERSION\s*=\s*"[^"]+"', $replacement
    Set-Content -Path $swSource -Value $updated -NoNewline -Encoding UTF8
    Write-Host "==> sw.js CACHE_VERSION bumped to $newVersion" -ForegroundColor Cyan
    $bumped = $true
}

if ($bumped -and -not $SkipBuild) {
    Write-Host "==> Rebuilding so the export picks up the new CACHE_VERSION" -ForegroundColor Cyan
    Build
}

Write-Host "==> Syncing contexia-app/out/* -> repo root" -ForegroundColor Cyan
if (-not (Test-Path (Join-Path $appDir "out"))) { Fail "contexia-app/out not found -- did the build run?" }
Copy-Item -Path (Join-Path $appDir "out\*") -Destination $repoRoot -Recurse -Force

Push-Location $repoRoot

$untrackedNext = git status --porcelain -- _next/ | Where-Object { $_ -match '^\?\?' }
if ($untrackedNext) {
    Write-Host "==> New _next/ chunk files found -- staging them (this is the bug that bit us 3 times):" -ForegroundColor Yellow
    git add _next/
    $untrackedNext | ForEach-Object { Write-Host "    $_" }
}

Write-Host ""
Write-Host "==> git status (review before committing anything else)" -ForegroundColor Cyan
git status --short

Pop-Location

Write-Host ""
Write-Host "Build + sync done. _next/ is staged if it changed; nothing else was committed." -ForegroundColor Green
Write-Host "Next: stage the rest of what you actually changed, commit, push, then run:" -ForegroundColor Green
Write-Host "  pwsh scripts/verify-deploy.ps1 -Routes /app/your-new-route" -ForegroundColor Green
