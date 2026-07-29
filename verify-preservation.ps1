# SPDX-License-Identifier: BSD-2-Clause

[CmdletBinding()]
param(
    [Parameter()]
    [string]$RepositoryRoot
)

$ErrorActionPreference = 'Stop'
$verifier = Join-Path -Path $PSScriptRoot -ChildPath 'tools\verify_preservation.py'
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = $PSScriptRoot
}

function Invoke-PreservationVerifier {
    param(
        [Parameter(Mandatory)]
        [string]$Executable,

        [Parameter(Mandatory)]
        [string[]]$Arguments
    )

    try {
        & $Executable @Arguments
        $childExit = $LASTEXITCODE
    }
    catch {
        [Console]::Error.WriteLine("ERROR: Python launcher failed: $($_.Exception.Message)")
        exit 2
    }

    if ($childExit -notin 0, 1, 2) {
        [Console]::Error.WriteLine(
            "ERROR: Python launcher returned unexpected exit code $childExit."
        )
        exit 2
    }
    exit $childExit
}

if (-not (Test-Path -LiteralPath $verifier -PathType Leaf)) {
    [Console]::Error.WriteLine("ERROR: verifier not found: $verifier")
    exit 2
}

$launcher = Get-Command -Name 'py.exe' -CommandType Application -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($null -ne $launcher) {
    Invoke-PreservationVerifier -Executable $launcher.Source -Arguments @(
        '-3', '-I', $verifier, '--repository-root', $RepositoryRoot
    )
}

$launcher = Get-Command -Name 'python.exe' -CommandType Application -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($null -ne $launcher) {
    Invoke-PreservationVerifier -Executable $launcher.Source -Arguments @(
        '-I', $verifier, '--repository-root', $RepositoryRoot
    )
}

[Console]::Error.WriteLine('ERROR: Python 3 is required to run preservation verification.')
exit 2
