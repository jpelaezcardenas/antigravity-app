<#
.SYNOPSIS
    Deploys repo-canonical skills from ai-specs/skills/ into the local Hermes profile.

.DESCRIPTION
    Hermes reads its skills from %LOCALAPPDATA%\hermes\profiles\<profile>\skills\. That directory
    lives outside this repository, so the skills are deployed as REAL DIRECTORIES, not symlinks.

    This is deliberate. Every existing contexia-* skill in that folder is already a real directory,
    and a symlink pointing outside the repo dangles in exactly the way CLAUDE.md section 8 documents
    for DEPLOYMENT_STAGE/ — a fresh clone, or a machine without this repo checked out, would get a
    broken link instead of a skill.

    The trade-off is drift: the deployed copy can fall behind its canonical source. That is what
    -Check is for. Run it in CI or before a release to fail loudly instead of drifting silently.

    In-repo agent paths (.claude/skills, .cursor/skills) are NOT handled here — those are inside the
    repo, so they use normal symlinks via the sync-agent-symlinks skill (CLAUDE.md section 6).

.PARAMETER Skill
    Sync only this skill. Default: every skill listed in $CanonicalSkills.

.PARAMETER HermesProfile
    Hermes profile name. Defaults to the value in %LOCALAPPDATA%\hermes\active_profile, or
    'contexia' when that file is absent.

.PARAMETER Check
    Compare only; make no changes. Exits 1 if any deployed copy differs from its canonical source.

.EXAMPLE
    pwsh -File scripts/sync_hermes_skills.ps1
    pwsh -File scripts/sync_hermes_skills.ps1 -Check
    pwsh -File scripts/sync_hermes_skills.ps1 -Skill contexia-voice-tts
#>

[CmdletBinding()]
param(
    [string] $Skill,
    [string] $HermesProfile,
    [switch] $Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Skills this repo owns and deploys into Hermes. Hermes has many other skills that are NOT managed
# here; this script must never touch them.
$CanonicalSkills = @(
    'contexia-voice-tts'
)

$RepoRoot     = Split-Path -Parent $PSScriptRoot
$SourceRoot   = Join-Path $RepoRoot 'ai-specs\skills'
$HermesRoot   = Join-Path $env:LOCALAPPDATA 'hermes'

function Resolve-HermesProfile {
    if ($HermesProfile) { return $HermesProfile }
    $activeFile = Join-Path $HermesRoot 'active_profile'
    if (Test-Path -LiteralPath $activeFile) {
        $name = (Get-Content -LiteralPath $activeFile -Raw).Trim()
        if ($name) { return $name }
    }
    return 'contexia'
}

# Content hash of every file in a tree, so a comparison is about content and not timestamps.
function Get-TreeFingerprint {
    param([string] $Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $entries = Get-ChildItem -LiteralPath $Path -Recurse -File |
        Where-Object { $_.FullName -notmatch '\\__pycache__\\' } |
        Sort-Object FullName
    $lines = foreach ($f in $entries) {
        $relative = $f.FullName.Substring($Path.Length).TrimStart('\')
        '{0}:{1}' -f $relative, (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
    }
    return ($lines -join "`n")
}

$profileName = Resolve-HermesProfile
$targetRoot  = Join-Path $HermesRoot "profiles\$profileName\skills"

if (-not (Test-Path -LiteralPath $targetRoot)) {
    throw "Hermes skills directory not found: $targetRoot. Is Hermes installed and is '$profileName' the right profile?"
}

$toSync = if ($Skill) { @($Skill) } else { $CanonicalSkills }
$drifted = @()

foreach ($name in $toSync) {
    $source = Join-Path $SourceRoot $name
    $target = Join-Path $targetRoot $name

    if (-not (Test-Path -LiteralPath $source)) {
        throw "Canonical skill not found: $source"
    }

    $sourcePrint = Get-TreeFingerprint -Path $source
    $targetPrint = Get-TreeFingerprint -Path $target

    if ($sourcePrint -eq $targetPrint) {
        Write-Host "[ok]      $name -> already in sync"
        continue
    }

    if ($Check) {
        $state = if ($null -eq $targetPrint) { 'missing' } else { 'drifted' }
        Write-Host "[$state] $name"
        $drifted += $name
        continue
    }

    # Replace wholesale rather than merging, so a file deleted from the canonical source also
    # disappears from the deployed copy. Only ever touches this one skill's directory.
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
    Copy-Item -LiteralPath $source -Destination $target -Recurse -Force
    Get-ChildItem -LiteralPath $target -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    Write-Host "[synced]  $name -> $target"
}

if ($Check -and $drifted.Count -gt 0) {
    Write-Error "Deployed Hermes skills differ from ai-specs/skills: $($drifted -join ', '). Run this script without -Check to fix."
    exit 1
}
