param(
    [string]$PostgresBin,
    [string]$Profile
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

if (-not $PostgresBin) {
    $postgresCandidates = @(
        (Join-Path $projectRoot '.runtime\desktop-vendor\postgresql\pgsql\bin'),
        'C:\Program Files\PostgreSQL\18\bin'
    )
    $PostgresBin = $postgresCandidates | Where-Object {
        Test-Path -LiteralPath (Join-Path $_ 'initdb.exe')
    } | Select-Object -First 1
}
if (
    -not $PostgresBin -or
    -not (Test-Path -LiteralPath (Join-Path $PostgresBin 'initdb.exe'))
) {
    throw 'Provide the PostgreSQL bin directory with -PostgresBin.'
}
if (-not $Profile) {
    $Profile = Join-Path $projectRoot '.local\desktop-preview'
}

$pythonCandidates = @(
    (Join-Path $projectRoot '.runtime\desktop-python\python.exe'),
    (Join-Path $projectRoot '.venv\Scripts\python.exe')
)
$python = $pythonCandidates | Where-Object {
    Test-Path -LiteralPath $_
} | Select-Object -First 1
if (-not $python) {
    $python = (Get-Command python -ErrorAction Stop).Source
}

& $python (Join-Path $projectRoot 'desktop.py') --profile $Profile --postgres $PostgresBin
exit $LASTEXITCODE
