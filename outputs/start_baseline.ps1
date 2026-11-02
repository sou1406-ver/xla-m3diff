param([switch]$Login, [switch]$Download)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
Set-Location -LiteralPath $PSScriptRoot

# Use the Python runtime already present on this PC, with an isolated CLI venv.
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$clientDir = Join-Path $PSScriptRoot '.modal-client'
$clientPython = Join-Path $clientDir 'Scripts\python.exe'
$modalExe = Join-Path $clientDir 'Scripts\modal.exe'
if (-not (Test-Path -LiteralPath $clientPython)) {
    if (Test-Path -LiteralPath $bundledPython) {
        & $bundledPython -m venv $clientDir
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv $clientDir
    } else {
        throw 'Need Python 3.10+. Install Python, then rerun this script.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create Python environment.' }
}
if (-not (Test-Path -LiteralPath $modalExe)) {
    & $clientPython -m pip install modal
    if ($LASTEXITCODE -ne 0) { throw 'Could not install Modal CLI.' }
}
if ($Login) {
    & $modalExe token new
    if ($LASTEXITCODE -ne 0) { throw 'Modal login failed.' }
    Write-Host 'Login complete. Now run this script again without -Login.'
} elseif ($Download) {
    & $modalExe volume get m3diff baseline_reproduction_v1/m3diff_baseline_results.zip .
    if ($LASTEXITCODE -ne 0) { throw 'Results not ready, or wrong Modal workspace/environment.' }
} else {
    & $modalExe run --detach (Join-Path $PSScriptRoot 'run_baseline_modal.py')
    if ($LASTEXITCODE -ne 0) { throw 'Launch failed. Use -Login first if authentication is missing.' }
}
