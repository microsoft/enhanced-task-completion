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

# Extract only the deploy/ and sample/solution/ subtrees (everything deploy.mjs
# needs), stripping the top "<repo>-<ref>/" folder. Entries are written through
# \\?\ extended-length paths so Windows PowerShell 5.1 does not trip over the
# 260-char MAX_PATH limit on the deeply nested solution component files -- plain
# Expand-Archive fails there and masks it with a misleading Remove-Item error.
function Expand-DeployAssets {
  param(
    [Parameter(Mandatory)][string] $ZipPath,
    [Parameter(Mandatory)][string] $Destination,
    [Parameter(Mandatory)][string] $Ref
  )
  if (-not ('System.IO.Compression.ZipFile' -as [type])) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
  }
  $dest = [System.IO.Path]::GetFullPath($Destination).TrimEnd('\')
  $top  = "new-copilot-studio-tech-guide-$Ref/"
  $want = @("${top}deploy/", "${top}sample/solution/")
  $archive = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
  try {
    foreach ($entry in $archive.Entries) {
      $name = $entry.FullName
      if (-not ($want | Where-Object { $name.StartsWith($_, [System.StringComparison]::Ordinal) })) { continue }
      $rel = $name.Substring($top.Length) -replace '/', '\'
      if ([string]::IsNullOrEmpty($rel)) { continue }
      $target = "$dest\$rel"
      if ([string]::IsNullOrEmpty($entry.Name)) {
        [void][System.IO.Directory]::CreateDirectory("\\?\$($target.TrimEnd('\'))")
        continue
      }
      [void][System.IO.Directory]::CreateDirectory("\\?\$([System.IO.Path]::GetDirectoryName($target))")
      [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, "\\?\$target", $true)
    }
  }
  finally { $archive.Dispose() }
}

# Best-effort recursive delete that also copes with >260-char paths.
function Remove-TreeLongPath {
  param([Parameter(Mandatory)][string] $Path)
  if (-not (Test-Path -LiteralPath $Path)) { return }
  $full = [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
  try { [System.IO.Directory]::Delete("\\?\$full", $true) }
  catch { Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue }
}

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
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("bb-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
  $zip = Join-Path $tmp 'src.zip'
  Info "Downloading the sample ($repo@$ref)..."
  Invoke-WebRequest -Uri "https://codeload.github.com/$repo/zip/refs/heads/$ref" -OutFile $zip -UseBasicParsing

  Info 'Extracting the deploy assets...'
  # Mirrors install.sh: only deploy/ + sample/solution/, top folder stripped, so
  # $tmp becomes REPO_ROOT (deploy.mjs resolves REPO_ROOT as deploy/..).
  Expand-DeployAssets -ZipPath $zip -Destination $tmp -Ref $ref
  $root = $tmp
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
  Remove-TreeLongPath -Path $tmp
}
