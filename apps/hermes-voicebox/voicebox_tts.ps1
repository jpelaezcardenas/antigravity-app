<#
.SYNOPSIS
    Hermes TTS command-provider wrapper for the local VoiceBox server.

.DESCRIPTION
    Hermes supports user-declared TTS backends via `tts.providers.<name>: {type: command}` (see
    tools/tts_tool.py). Hermes writes the text to a temp UTF-8 file, runs this script with
    {input_path} and {output_path} substituted, and reads back whatever audio the script wrote.
    That contract means no Python plugin and no Hermes code change is needed.

    A raw curl one-liner cannot fill this role, for two reasons:

    1. `POST /generate` does NOT return audio. It answers with JSON (GenerationResponse) carrying
       an `id`, a `status` and an `error`; the bytes come from a second call, GET /audio/{id}.
       Verified against the live server's OpenAPI document on 2026-09-08.
    2. The request body has to be built as JSON with the text embedded, and two of VoiceBox's own
       defaults are wrong for Contexia: `language` defaults to "en", and `model_size` defaults to
       "1.7B" - the model Phase 0 measured at 30-60 minutes per phrase on CPU.

    Status: this ships INERT. Hermes' `tts.provider` stays `edge` until the inference node exists;
    switching it is a migration-day action, because with no VoiceBox running every call would fail.

.PARAMETER InputPath
    UTF-8 file containing the text to speak. Hermes substitutes {input_path}.

.PARAMETER OutputPath
    Where to write the audio. Hermes substitutes {output_path}.

.NOTES
    Configuration comes from the environment, never from arguments or a versioned constant:
      VOICEBOX_URL         (default http://127.0.0.1:17493)
      VOICEBOX_PROFILE_ID  (required - no default; a guessed id speaks in the wrong voice)
      VOICEBOX_ENGINE      (default qwen)
      VOICEBOX_MODEL_SIZE  (default 0.6B)
      VOICEBOX_LANGUAGE    (default es)
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $InputPath,
    [Parameter(Mandatory = $true)] [string] $OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-EnvOrDefault {
    param([string] $Name, [string] $Default)
    $value = [Environment]::GetEnvironmentVariable($Name)
    if ([string]::IsNullOrWhiteSpace($value)) { return $Default }
    return $value
}

$baseUrl   = (Get-EnvOrDefault 'VOICEBOX_URL' 'http://127.0.0.1:17493').TrimEnd('/')
$profileId = [Environment]::GetEnvironmentVariable('VOICEBOX_PROFILE_ID')
$engine    = Get-EnvOrDefault 'VOICEBOX_ENGINE'     'qwen'
$modelSize = Get-EnvOrDefault 'VOICEBOX_MODEL_SIZE' '0.6B'
$language  = Get-EnvOrDefault 'VOICEBOX_LANGUAGE'   'es'

if ([string]::IsNullOrWhiteSpace($profileId)) {
    # Fail loudly rather than picking a profile. Speaking in the wrong voice is worse than silence,
    # and Contexia's profile is a clone of a real, named person.
    throw "VOICEBOX_PROFILE_ID is not set. Refusing to guess a voice profile."
}

if (-not (Test-Path -LiteralPath $InputPath)) {
    throw "Input file not found: $InputPath"
}

$text = Get-Content -LiteralPath $InputPath -Raw -Encoding UTF8
if ([string]::IsNullOrWhiteSpace($text)) {
    throw "Input file is empty: $InputPath"
}

$body = @{
    profile_id = $profileId
    text       = $text
    language   = $language      # VoiceBox defaults this to 'en'
    engine     = $engine
    model_size = $modelSize     # VoiceBox defaults this to the unusable '1.7B'
    # An in-character rewrite would change text that was already reviewed. Off, always.
    personality = $false
} | ConvertTo-Json -Depth 4 -Compress

$generation = Invoke-RestMethod -Method Post -Uri "$baseUrl/generate" `
    -ContentType 'application/json; charset=utf-8' `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($body))

# A 200 carrying `error` is a FAILED generation, not a success.
if ($generation.PSObject.Properties.Name -contains 'error' -and $generation.error) {
    throw "VoiceBox generation failed: $($generation.error)"
}
if (-not $generation.id) {
    throw "VoiceBox /generate returned no generation id."
}

Invoke-WebRequest -Method Get -Uri "$baseUrl/audio/$($generation.id)" -OutFile $OutputPath | Out-Null

if (-not (Test-Path -LiteralPath $OutputPath) -or (Get-Item -LiteralPath $OutputPath).Length -eq 0) {
    throw "VoiceBox returned no audio for generation $($generation.id)."
}
