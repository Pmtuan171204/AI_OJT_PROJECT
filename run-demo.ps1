$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if ($pythonCommand) {
        $pythonExecutable = $pythonCommand.Source
    } elseif (Test-Path -LiteralPath $bundledPython) {
        $pythonExecutable = $bundledPython
    } else {
        throw 'Python 3.10+ is required. Install Python and add it to PATH.'
    }
    & $pythonExecutable -m ojt_risk --data tests/fixtures/demo --evaluation-term 2026_HK1 --target-term 2026_HK2 --output output/report.json
    if ($LASTEXITCODE -ne 0) { throw 'Demo failed.' }
} finally {
    Pop-Location
}
