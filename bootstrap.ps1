$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeRoot = Join-Path $RepoRoot ".qabot-runtime"
$CondaRoot = Join-Path $RuntimeRoot "miniforge"
$EnvPrefix = Join-Path $RuntimeRoot "env"
$Installer = Join-Path $env:TEMP "Miniforge3-Windows-x86_64.exe"
$CondaExe = Join-Path $CondaRoot "Scripts\conda.exe"
$PythonExe = Join-Path $EnvPrefix "python.exe"
$PythonwExe = Join-Path $EnvPrefix "pythonw.exe"
$OsmiumExe = Join-Path $EnvPrefix "Library\bin\osmium.exe"
$JosmJar = Join-Path $RepoRoot "tools\josm-19613.jar"

function Invoke-Checked {
    param([string]$FilePath, [string[]]$Arguments, [string]$Step)
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed (exit code $LASTEXITCODE)."
    }
}

function Install-Miniforge {
    Write-Host "Downloading the official Miniforge Windows installer..." -ForegroundColor Cyan
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/conda-forge/miniforge/releases/latest" -Headers @{ "Accept" = "application/vnd.github+json" }
    $asset = $release.assets | Where-Object { $_.name -eq "Miniforge3-Windows-x86_64.exe" } | Select-Object -First 1
    if (-not $asset -or $asset.digest -notmatch "^sha256:([0-9a-fA-F]{64})$") {
        throw "GitHub did not provide a SHA-256 digest for the Miniforge installer. Refusing to run an unverified installer."
    }

    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $Installer -UseBasicParsing
    $actualHash = (Get-FileHash -Path $Installer -Algorithm SHA256).Hash.ToLowerInvariant()
    $expectedHash = $Matches[1].ToLowerInvariant()
    if ($actualHash -ne $expectedHash) {
        Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
        throw "Miniforge installer SHA-256 verification failed. The installer was not executed."
    }

    Write-Host "Installing Miniforge privately for this QA Buddy checkout..." -ForegroundColor Cyan
    $arguments = "/InstallationType=JustMe /RegisterPython=0 /AddToPath=0 /S /D=$CondaRoot"
    $process = Start-Process -FilePath $Installer -ArgumentList $arguments -Wait -PassThru
    if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $CondaExe)) {
        throw "Miniforge installation failed (exit code $($process.ExitCode))."
    }
    Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
}

function Test-Runtime {
    if (-not (Test-Path -LiteralPath $PythonExe) -or
        -not (Test-Path -LiteralPath $OsmiumExe) -or
        -not (Test-Path -LiteralPath (Join-Path $EnvPrefix "Library\bin\java.exe"))) {
        return $false
    }

    $oldPath = $env:PATH
    $env:PATH = "$EnvPrefix;$EnvPrefix\Scripts;$EnvPrefix\Library\bin;$EnvPrefix\Library\usr\bin;$oldPath"
    try {
        & $PythonExe -c "import sys, shapely; assert sys.version_info >= (3, 12); print('Python', sys.version.split()[0], '| Shapely', shapely.__version__)" *> $null
        if ($LASTEXITCODE -ne 0) { return $false }
        & $OsmiumExe --version *> $null
        if ($LASTEXITCODE -ne 0) { return $false }
        & (Join-Path $EnvPrefix "Library\bin\java.exe") -version *> $null
        if ($LASTEXITCODE -ne 0) { return $false }
        return $true
    }
    finally {
        $env:PATH = $oldPath
    }
}

try {
    if (-not (Test-Path -LiteralPath $CondaExe)) {
        if (Test-Path -LiteralPath $CondaRoot) {
            throw "A partial Miniforge folder exists at '$CondaRoot'. Remove only that incomplete .qabot-runtime\miniforge folder, then click the launcher again."
        }
        New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null
        Install-Miniforge
    }

    if (-not (Test-Runtime)) {
        Write-Host "Preparing the private Python, Shapely, Osmium Tool and Java runtime..." -ForegroundColor Cyan
        New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null
        if (Test-Path -LiteralPath (Join-Path $EnvPrefix "conda-meta")) {
            Invoke-Checked $CondaExe @("install", "--yes", "--prefix", $EnvPrefix, "--override-channels", "-c", "conda-forge", "python=3.12", "shapely=2.1.2", "osmium-tool", "openjdk=21") "Runtime repair"
        }
        else {
            Invoke-Checked $CondaExe @("create", "--yes", "--prefix", $EnvPrefix, "--override-channels", "-c", "conda-forge", "python=3.12", "shapely=2.1.2", "osmium-tool", "openjdk=21") "Runtime installation"
        }
    }

    $env:CONDA_PREFIX = $EnvPrefix
    $env:OSMIUM_EXE = $OsmiumExe
    $env:PATH = "$EnvPrefix;$EnvPrefix\Scripts;$EnvPrefix\Library\bin;$EnvPrefix\Library\usr\bin;$env:PATH"

    if (-not (Test-Runtime)) {
        throw "The private runtime did not pass verification. Check the installation output above; the GUI was not started."
    }

    Write-Host "Preparing and verifying JOSM..." -ForegroundColor Cyan
    Invoke-Checked $PythonExe @((Join-Path $RepoRoot "setup_native.py"), "--gui-only") "JOSM setup"
    if (-not (Test-Path -LiteralPath $JosmJar)) {
        throw "JOSM setup finished without creating $JosmJar."
    }

    Write-Host "All prerequisites are ready. Starting OSM QA Buddy..." -ForegroundColor Green
    Start-Process -FilePath $PythonwExe -ArgumentList ('"{0}"' -f (Join-Path $RepoRoot "OSM_QA_Buddy_GUI.pyw")) -WorkingDirectory $RepoRoot
    exit 0
}
catch {
    Write-Host ""
    Write-Host "OSM QA Buddy could not finish setup:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "No global Python, Java, or PATH settings were changed."
    Read-Host "Press Enter to close this window"
    exit 1
}
