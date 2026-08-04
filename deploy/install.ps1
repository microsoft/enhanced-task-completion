<#
  install.ps1 - no-clone bootstrap for the BlastBox Omega sample (Windows).

  Downloads the deploy assets straight from GitHub and runs the guided
  deploy (deploy/deploy.mjs). Nothing is left behind except the solutions
  and connectors it imports into your Power Platform environment.

    irm https://raw.githubusercontent.com/microsoft/new-copilot-studio-tech-guide/main/deploy/install.ps1 | iex

  Set $env:BLASTBOX_REF to deploy from a specific branch or tag (default: main).
#>
#requires -Version 5.1
$ErrorActionPreference = 'Stop'

$repo = 'microsoft/new-copilot-studio-tech-guide'
$ref  = if ($env:BLASTBOX_REF) { $env:BLASTBOX_REF } else { 'main' }

function Info($m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "WARNING: $m" -ForegroundColor Yellow }

# --- preflight ---------------------------------------------------------------
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  throw 'Node.js 18+ is required but was not found. Install it from https://nodejs.org and re-run.'
}
$nodeMajor = [int](node -p "process.versions.node.split('.')[0]")
if ($nodeMajor -lt 18) { throw "Node.js 18+ is required (found $(node -v))." }
if (-not (Get-Command pac -ErrorAction SilentlyContinue)) {
  Warn 'pac CLI not found on PATH. The deploy needs it signed in (pac auth create). See deploy/README.md.'
}
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
  Warn 'az CLI not found on PATH. The deploy uses it for the connection REST calls. See deploy/README.md.'
}

# --- download ----------------------------------------------------------------
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("blastbox-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmp | Out-Null
try {
  $zip = Join-Path $tmp 'src.zip'
  Info "Downloading the sample ($repo@$ref)..."
  Invoke-WebRequest -Uri "https://codeload.github.com/$repo/zip/refs/heads/$ref" -OutFile $zip -UseBasicParsing

  Info 'Extracting the deploy assets...'
  Expand-Archive -Path $zip -DestinationPath $tmp -Force
  $root = Join-Path $tmp "new-copilot-studio-tech-guide-$ref"
  if (-not (Test-Path (Join-Path $root 'deploy\deploy.mjs'))) {
    throw 'deploy/deploy.mjs is missing after extract.'
  }

  # --- run -------------------------------------------------------------------
  # deploy.mjs is interactive; running under 'irm | iex' inherits the console
  # so its prompts work without any redirection.
  Push-Location $root
  try {
    Info 'Starting the guided deploy...'
    & node 'deploy/deploy.mjs' @args
  }
  finally { Pop-Location }
}
finally {
  Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}
