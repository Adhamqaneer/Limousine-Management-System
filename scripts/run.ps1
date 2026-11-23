param(
    [ValidateSet(
        'runserver',
        'check',
        'test',
        'migrate'
    )]
    [string]$Command = 'runserver',
    [int]$Port = 8000
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonCandidates = @(
    (Join-Path $projectRoot '.venv\Scripts\python.exe'),
    (Join-Path $projectRoot '.runtime\python\python.exe')
)
$pythonExecutable = $null
foreach ($candidate in $pythonCandidates) {
    if (Test-Path -LiteralPath $candidate) {
        $pythonExecutable = $candidate
        break
    }
}
if (-not $pythonExecutable) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw 'Install Python 3.12+ and follow README.md.'
    }
    $pythonExecutable = $pythonCommand.Source
}
[string[]]$commandArguments = if ($Command -eq 'runserver') {
    @(
        'runserver',
        "127.0.0.1:$Port"
    )
} else {
    @($Command)
}
Push-Location $projectRoot
try {
    & $pythonExecutable (Join-Path $projectRoot 'manage.py') @commandArguments
    $commandExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $commandExitCode
