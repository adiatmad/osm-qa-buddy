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
$RequirementsFile = Join-Path $RepoRoot "requirements.txt"

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
    $digestMatch = [regex]::Match([string]$asset.digest, "^sha256:([0-9a-fA-F]{64})$")
    if (-not $asset -or -not $digestMatch.Success) {
        throw "GitHub did not provide a SHA-256 digest for the Miniforge installer. Refusing to run an unverified installer."
    }
    $expectedHash = $digestMatch.Groups[1].Value.ToLowerInvariant()

    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $Installer -UseBasicParsing
    $actualHash = (Get-FileHash -Path $Installer -Algorithm SHA256).Hash.ToLowerInvariant()
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
        -not (Test-Path -LiteralPath $PythonwExe) -or
        -not (Test-Path -LiteralPath $OsmiumExe)) {
        return $false
    }

    $oldPath = $env:PATH
    $env:PATH = "$EnvPrefix;$EnvPrefix\Scripts;$EnvPrefix\Library\bin;$EnvPrefix\Library\usr\bin;$oldPath"
    try {
        & $PythonExe -c "import sys, shapely, tkinter; print('Python:', sys.version.split()[0]); print('Shapely:', shapely.__version__); print('Tkinter: OK'); sys.exit(0 if sys.version_info[:2] == (3, 12) and shapely.__version__ == '2.1.2' else 1)"
        if ($LASTEXITCODE -ne 0) { return $false }
        & $OsmiumExe --version *> $null
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
            Write-Host "Removing an incomplete app-managed Miniforge installation..." -ForegroundColor Yellow
            Remove-Item -LiteralPath $CondaRoot -Recurse -Force
        }
        New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null
        Install-Miniforge
    }
    else {
        & $CondaExe --version *> $null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Repairing the incomplete app-managed Miniforge installation..." -ForegroundColor Yellow
            Remove-Item -LiteralPath $CondaRoot -Recurse -Force
            Install-Miniforge
        }
    }

    if (-not (Test-Runtime)) {
        Write-Host "Preparing the private Python, Shapely and Osmium Tool runtime..." -ForegroundColor Cyan
        New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null
        if (Test-Path -LiteralPath (Join-Path $EnvPrefix "conda-meta")) {
            Invoke-Checked $CondaExe @("install", "--yes", "--prefix", $EnvPrefix, "--override-channels", "-c", "conda-forge", "python=3.12", "pip", "tk", "osmium-tool") "Runtime repair"
        }
        else {
            Invoke-Checked $CondaExe @("create", "--yes", "--prefix", $EnvPrefix, "--override-channels", "-c", "conda-forge", "python=3.12", "pip", "tk", "osmium-tool") "Runtime installation"
        }
    }

    # Install the project-pinned Shapely from its official Windows wheel.
    # The conda-forge Windows build may lag behind the exact version in requirements.txt.
    Write-Host "Installing and verifying the Python requirements..." -ForegroundColor Cyan
    Invoke-Checked $PythonExe @("-m", "pip", "install", "--disable-pip-version-check", "--only-binary=:all:", "-r", $RequirementsFile) "Python dependency installation"

    $env:CONDA_PREFIX = $EnvPrefix
    $env:OSMIUM_EXE = $OsmiumExe
    $env:PATH = "$EnvPrefix;$EnvPrefix\Scripts;$EnvPrefix\Library\bin;$EnvPrefix\Library\usr\bin;$env:PATH"

    if (-not (Test-Runtime)) {
        throw "The private runtime did not pass verification. Check the installation output above; the GUI was not started."
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
    Write-Host "No global Python or PATH settings were changed."
    Read-Host "Press Enter to close this window"
    exit 1
}
