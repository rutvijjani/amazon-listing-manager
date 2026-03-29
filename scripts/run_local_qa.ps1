param(
    [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot "venv\Scripts\python.exe"

Write-Host "Running local smoke QA from $repoRoot"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Missing virtualenv interpreter at $pythonExe. Create the venv first."
}

try {
    $versionOutput = & $pythonExe -c "import sys; print(sys.version)" 2>&1
    if ($LASTEXITCODE -ne 0 -or ($versionOutput | Out-String) -match "Unable to create process") {
        throw "Broken virtualenv interpreter"
    }
} catch {
    Write-Host ""
    Write-Host "Local Python environment is broken." -ForegroundColor Red
    Write-Host "Expected interpreter: $pythonExe"
    Write-Host "This usually means the base Python used to create the venv was removed."
    Write-Host ""
    Write-Host "Quick fix:"
    Write-Host "1. Install Python 3.12"
    Write-Host "2. Recreate the venv: py -3.12 -m venv venv"
    Write-Host "3. Reinstall deps: .\venv\Scripts\python.exe -m pip install -r requirements.txt"
    Write-Host "4. Re-run: powershell -ExecutionPolicy Bypass -File .\scripts\run_local_qa.ps1"
    exit 1
}

$unittestArgs = @("-m", "unittest", "tests.test_smoke_unittest", "-v")

if ($VerboseOutput) {
    Write-Host "Command: $pythonExe $($unittestArgs -join ' ')"
}

& $pythonExe @unittestArgs
exit $LASTEXITCODE
