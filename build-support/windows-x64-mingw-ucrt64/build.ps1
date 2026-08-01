# SPDX-License-Identifier: BSD-2-Clause

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$BuildId
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 3.0

$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$script:ExpectedArchiveSha256 = (
    '8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e'
)
$script:ExpectedGccSha256 = (
    'f96a3bdb1d3a3967b309d75c7413399391e857b5be4cb17162572ed66f6772a0'
)
$script:ExpectedLdSha256 = (
    'fb152d34cf00bf66fc57a66522806a4e64914654d8c1ab8cdd0a1d78283ec215'
)
$script:ExpectedBashSha256 = (
    '41b09f0a9c1c68fd65253a7e8087b3775f0af245b729ade74ca4425d14392c2d'
)
$script:ExpectedPacmanSha256 = (
    '209b2d527f359608cdb092515d3d99f46ac9d2209d130adced81a8cdd79057d8'
)
$script:ExpectedMsysRuntimeSha256 = (
    '0cb645ead21947b7e865448413f3e281236638ed38695b43c2a6d9c06598e046'
)
$script:ExpectedSourceGuardSha256 = (
    '331718ae2b79390b71b8eb935953b7652d5a702a3e56cf1deb6aa51152b88b13'
)
$script:ExpectedPreservationWrapperSha256 = (
    'a8c19981db3fdbcaee380755c29f56975ea1ead3d78976fb90c81c22e438e0f7'
)
$script:ExpectedPreservationVerifierSha256 = (
    '4fbfebcf7a09307dc7314a75fe2789860f243ae60e8b64604125821f729fc658'
)
$script:ExpectedPackages = @(
    'bash 5.3.015-1',
    'pacman 6.1.0-25',
    'msys2-runtime 3.6.10-1',
    'mingw-w64-ucrt-x86_64-gcc 16.1.0-5',
    'make 4.4.1-3',
    'autoconf-wrapper 20260320-1',
    'automake-wrapper 20260320-1',
    'libtool 2.5.4-5',
    'pkgconf 2.5.1-1',
    'mingw-w64-ucrt-x86_64-binutils 2.47-1',
    'mingw-w64-ucrt-x86_64-headers 14.0.0.r220.gd999af622-1',
    'mingw-w64-ucrt-x86_64-crt 14.0.0.r220.gd999af622-1',
    'mingw-w64-ucrt-x86_64-gcc-libs 16.1.0-5'
)
$script:ExpectedIntegrityRecords = @(
    'bash: 215 total files, 0 altered files',
    'pacman: 414 total files, 0 altered files',
    'msys2-runtime: 176 total files, 0 altered files',
    'mingw-w64-ucrt-x86_64-gcc: 1794 total files, 0 altered files',
    'make: 105 total files, 0 altered files',
    'autoconf-wrapper: 9 total files, 0 altered files',
    'automake-wrapper: 4 total files, 0 altered files',
    'libtool: 70 total files, 0 altered files',
    'pkgconf: 35 total files, 0 altered files',
    'mingw-w64-ucrt-x86_64-binutils: 272 total files, 0 altered files',
    'mingw-w64-ucrt-x86_64-headers: 2063 total files, 0 altered files',
    'mingw-w64-ucrt-x86_64-crt: 961 total files, 0 altered files',
    'mingw-w64-ucrt-x86_64-gcc-libs: 14 total files, 0 altered files'
)
$script:SourceDateEpoch = '1701496474'

function Assert-ValidBuildId {
    param(
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string]$Value
    )

    if (
        $Value -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$' -or
        $Value -match '^(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$'
    ) {
        throw 'BuildId must be 1-32 safe ASCII characters and not a reserved Windows device name.'
    }
}

function Get-Sha256 {
    param(
        [Parameter(Mandatory)]
        [string]$LiteralPath
    )

    return (Get-FileHash -Algorithm SHA256 -LiteralPath $LiteralPath).Hash.ToLowerInvariant()
}

function Test-ReparsePoint {
    param(
        [Parameter(Mandatory)]
        [string]$LiteralPath
    )

    $item = Get-Item -LiteralPath $LiteralPath -Force
    return [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
}

function Assert-PlainDirectory {
    param(
        [Parameter(Mandatory)]
        [string]$LiteralPath,

        [Parameter(Mandatory)]
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $LiteralPath -PathType Container)) {
        throw "$Label is not an existing directory."
    }
    if (Test-ReparsePoint -LiteralPath $LiteralPath) {
        throw "$Label must not be a reparse point."
    }
}

function Assert-PlainFile {
    param(
        [Parameter(Mandatory)]
        [string]$LiteralPath,

        [Parameter(Mandatory)]
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $LiteralPath -PathType Leaf)) {
        throw "$Label is not an existing file."
    }
    if (Test-ReparsePoint -LiteralPath $LiteralPath) {
        throw "$Label must not be a reparse point."
    }
}

function ConvertTo-WindowsCommandLineArgument {
    param(
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string]$Value
    )

    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') {
        return $Value
    }

    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')
    $backslashes = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq '\') {
            $backslashes += 1
            continue
        }
        if ($character -eq '"') {
            [void]$builder.Append(('\' * (($backslashes * 2) + 1)))
            [void]$builder.Append('"')
            $backslashes = 0
            continue
        }
        if ($backslashes -gt 0) {
            [void]$builder.Append(('\' * $backslashes))
            $backslashes = 0
        }
        [void]$builder.Append($character)
    }
    if ($backslashes -gt 0) {
        [void]$builder.Append(('\' * ($backslashes * 2)))
    }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function ConvertTo-MsysPath {
    param(
        [Parameter(Mandatory)]
        [string]$LiteralPath
    )

    $fullPath = [System.IO.Path]::GetFullPath($LiteralPath)
    $match = [regex]::Match($fullPath, '^([A-Za-z]):\\(.*)$')
    if (-not $match.Success) {
        throw 'A2b requires an ordinary drive-qualified Windows path.'
    }
    $drive = $match.Groups[1].Value.ToLowerInvariant()
    $tail = $match.Groups[2].Value.Replace('\', '/')
    return "/$drive/$tail"
}

function Stop-ProcessTree {
    param(
        [Parameter(Mandatory)]
        [System.Diagnostics.Process]$Process
    )

    if ($Process.HasExited) {
        return
    }
    $taskkill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
    Assert-PlainFile -LiteralPath $taskkill -Label 'system taskkill'
    $killer = Start-Process -FilePath $taskkill -ArgumentList @(
        '/PID',
        $Process.Id.ToString(),
        '/T',
        '/F'
    ) -Wait -PassThru -WindowStyle Hidden
    if ($killer.ExitCode -notin @(0, 128)) {
        throw "taskkill failed with exit $($killer.ExitCode)."
    }
    if (-not $Process.WaitForExit(10000)) {
        throw 'Timed-out process tree did not terminate within ten seconds.'
    }
}

function Invoke-CapturedProcess {
    param(
        [Parameter(Mandatory)]
        [string]$FilePath,

        [string[]]$Arguments = @(),

        [Parameter(Mandatory)]
        [string]$WorkingDirectory,

        [hashtable]$Environment = @{},

        [bool]$ClearEnvironment = $false,

        [int]$TimeoutSeconds = 120
    )

    Assert-PlainFile -LiteralPath $FilePath -Label 'invoked executable'
    Assert-PlainDirectory -LiteralPath $WorkingDirectory -Label 'process working directory'

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FilePath
    $startInfo.Arguments = (
        $Arguments |
            ForEach-Object { ConvertTo-WindowsCommandLineArgument -Value $_ }
    ) -join ' '
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    if ($ClearEnvironment) {
        $startInfo.EnvironmentVariables.Clear()
    }
    foreach ($name in $Environment.Keys) {
        $startInfo.EnvironmentVariables[$name] = [string]$Environment[$name]
    }

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    $started = [DateTime]::UtcNow
    if (-not $process.Start()) {
        throw "Could not start $FilePath."
    }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $timedOut = -not $process.WaitForExit($TimeoutSeconds * 1000)
    if ($timedOut) {
        Stop-ProcessTree -Process $process
    }
    $process.WaitForExit()
    $stdout = $stdoutTask.Result
    $stderr = $stderrTask.Result
    $completed = [DateTime]::UtcNow

    return [pscustomobject][ordered]@{
        Arguments = @($Arguments)
        CompletedUtc = $completed.ToString('o')
        DurationMilliseconds = [long]($completed - $started).TotalMilliseconds
        ExitCode = $process.ExitCode
        FileName = [System.IO.Path]::GetFileName($FilePath)
        StartedUtc = $started.ToString('o')
        Stderr = $stderr
        Stdout = $stdout
        TimedOut = $timedOut
    }
}

function Write-Utf8Text {
    param(
        [Parameter(Mandatory)]
        [string]$LiteralPath,

        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string]$Text
    )

    [System.IO.File]::WriteAllText($LiteralPath, $Text, $script:Utf8NoBom)
}

function Normalize-Diagnostics {
    param(
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string]$Text,

        [Parameter(Mandatory)]
        [hashtable]$ReplacementMap
    )

    $normalized = $Text.Replace("`r`n", "`n").Replace("`r", "`n")
    foreach (
        $source in @(
            $ReplacementMap.Keys |
                Sort-Object { $_.Length } -Descending
        )
    ) {
        $normalized = [regex]::Replace(
            $normalized,
            [regex]::Escape($source),
            [string]$ReplacementMap[$source],
            [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
        )
    }
    return $normalized
}

function Write-CaptureEvidence {
    param(
        [Parameter(Mandatory)]
        [pscustomobject]$Capture,

        [Parameter(Mandatory)]
        [string]$OutputRoot,

        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [hashtable]$ReplacementMap
    )

    $rawStdout = Join-Path $OutputRoot "$Name.stdout.txt"
    $rawStderr = Join-Path $OutputRoot "$Name.stderr.txt"
    $normalizedStdout = Join-Path $OutputRoot "$Name.stdout.normalized.txt"
    $normalizedStderr = Join-Path $OutputRoot "$Name.stderr.normalized.txt"
    Write-Utf8Text -LiteralPath $rawStdout -Text $Capture.Stdout
    Write-Utf8Text -LiteralPath $rawStderr -Text $Capture.Stderr
    Write-Utf8Text -LiteralPath $normalizedStdout -Text (
        Normalize-Diagnostics -Text $Capture.Stdout -ReplacementMap $ReplacementMap
    )
    Write-Utf8Text -LiteralPath $normalizedStderr -Text (
        Normalize-Diagnostics -Text $Capture.Stderr -ReplacementMap $ReplacementMap
    )

    return [ordered]@{
        arguments = @($Capture.Arguments)
        completed_utc = $Capture.CompletedUtc
        duration_milliseconds = $Capture.DurationMilliseconds
        exit_code = $Capture.ExitCode
        executable_name = $Capture.FileName
        normalized_stderr = [ordered]@{
            bytes = (Get-Item -LiteralPath $normalizedStderr).Length
            sha256 = Get-Sha256 -LiteralPath $normalizedStderr
        }
        normalized_stdout = [ordered]@{
            bytes = (Get-Item -LiteralPath $normalizedStdout).Length
            sha256 = Get-Sha256 -LiteralPath $normalizedStdout
        }
        raw_stderr = [ordered]@{
            bytes = (Get-Item -LiteralPath $rawStderr).Length
            sha256 = Get-Sha256 -LiteralPath $rawStderr
        }
        raw_stdout = [ordered]@{
            bytes = (Get-Item -LiteralPath $rawStdout).Length
            sha256 = Get-Sha256 -LiteralPath $rawStdout
        }
        started_utc = $Capture.StartedUtc
        timed_out = $Capture.TimedOut
    }
}

function Invoke-PreservationVerifier {
    param(
        [Parameter(Mandatory)]
        [string]$RepositoryRoot
    )

    $powershell = Join-Path $PSHOME 'powershell.exe'
    $capture = Invoke-CapturedProcess -FilePath $powershell -Arguments @(
        '-NoLogo',
        '-NoProfile',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        (Join-Path $RepositoryRoot 'verify-preservation.ps1')
    ) -WorkingDirectory $RepositoryRoot -TimeoutSeconds 120
    if (
        $capture.TimedOut -or
        $capture.ExitCode -ne 0 -or
        $capture.Stdout -notmatch 'PASS: NEC2C 1\.3\.1 preservation verified'
    ) {
        throw 'Preservation verification failed.'
    }
    return $capture
}

function Invoke-SourceGuard {
    param(
        [Parameter(Mandatory)]
        [ValidateSet('extract', 'verify')]
        [string]$Operation,

        [Parameter(Mandatory)]
        [string]$RepositoryRoot,

        [Parameter(Mandatory)]
        [string]$SourceRoot
    )

    $launcher = (Get-Command py.exe -ErrorAction Stop).Source
    $capture = Invoke-CapturedProcess -FilePath $launcher -Arguments @(
        '-3',
        '-I',
        (Join-Path $RepositoryRoot 'build-support\windows-x64\source_guard.py'),
        $Operation,
        '--repository-root',
        $RepositoryRoot,
        '--source-root',
        $SourceRoot
    ) -WorkingDirectory $RepositoryRoot -TimeoutSeconds 120
    if (
        $capture.TimedOut -or
        $capture.ExitCode -ne 0 -or
        $capture.Stdout -notmatch "PASS: $Operation authenticated 34 original regular files"
    ) {
        throw "Source guard $Operation failed."
    }
    return $capture
}

function Get-BuildInventory {
    param(
        [Parameter(Mandatory)]
        [string]$BuildRoot
    )

    $records = @()
    foreach (
        $item in @(
            Get-ChildItem -LiteralPath $BuildRoot -Recurse -Force |
                Sort-Object -Property FullName
        )
    ) {
        if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            throw 'Build output contains a link or reparse point.'
        }
        if (-not $item.PSIsContainer) {
            $records += [ordered]@{
                bytes = $item.Length
                path = $item.FullName.Substring($BuildRoot.Length + 1).Replace('\', '/')
                sha256 = Get-Sha256 -LiteralPath $item.FullName
            }
        }
    }
    return @($records)
}

Assert-ValidBuildId -Value $BuildId

$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$msysRoot = 'C:\msys64'
$bash = Join-Path $msysRoot 'usr\bin\bash.exe'
$pacman = Join-Path $msysRoot 'usr\bin\pacman.exe'
$msysRuntime = Join-Path $msysRoot 'usr\bin\msys-2.0.dll'
$gcc = Join-Path $msysRoot 'ucrt64\bin\gcc.exe'
$ld = Join-Path $msysRoot 'ucrt64\bin\ld.exe'
$sourceGuard = Join-Path $repositoryRoot 'build-support\windows-x64\source_guard.py'
$preservationWrapper = Join-Path $repositoryRoot 'verify-preservation.ps1'
$preservationVerifier = Join-Path $repositoryRoot 'tools\verify_preservation.py'
$buildTempRoot = Join-Path $repositoryRoot '.build-temp'
$buildOutputRoot = Join-Path $repositoryRoot '.build-output'

Assert-PlainDirectory -LiteralPath $repositoryRoot -Label 'repository root'
Assert-PlainDirectory -LiteralPath $msysRoot -Label 'MSYS2 root'
Assert-PlainFile -LiteralPath $bash -Label 'MSYS2 bash'
Assert-PlainFile -LiteralPath $pacman -Label 'MSYS2 pacman'
Assert-PlainFile -LiteralPath $msysRuntime -Label 'MSYS2 runtime'
Assert-PlainFile -LiteralPath $gcc -Label 'UCRT64 GCC'
Assert-PlainFile -LiteralPath $ld -Label 'UCRT64 linker'
Assert-PlainFile -LiteralPath $sourceGuard -Label 'source guard'
Assert-PlainFile -LiteralPath $preservationWrapper -Label 'preservation wrapper'
Assert-PlainFile -LiteralPath $preservationVerifier -Label 'preservation verifier'
foreach ($identity in @(
    @($bash, $script:ExpectedBashSha256, 'MSYS2 Bash'),
    @($pacman, $script:ExpectedPacmanSha256, 'MSYS2 pacman'),
    @($msysRuntime, $script:ExpectedMsysRuntimeSha256, 'MSYS2 runtime'),
    @($gcc, $script:ExpectedGccSha256, 'UCRT64 GCC'),
    @($ld, $script:ExpectedLdSha256, 'UCRT64 linker'),
    @($sourceGuard, $script:ExpectedSourceGuardSha256, 'source guard'),
    @(
        $preservationWrapper,
        $script:ExpectedPreservationWrapperSha256,
        'preservation wrapper'
    ),
    @(
        $preservationVerifier,
        $script:ExpectedPreservationVerifierSha256,
        'preservation verifier'
    )
)) {
    if ((Get-Sha256 -LiteralPath $identity[0]) -ne $identity[1]) {
        throw "$($identity[2]) identity differs from the pinned A2b definition."
    }
}
$driverSha256 = Get-Sha256 -LiteralPath $PSCommandPath
$sourceGuardSha256 = Get-Sha256 -LiteralPath $sourceGuard
$preservationWrapperSha256 = Get-Sha256 -LiteralPath $preservationWrapper
$preservationVerifierSha256 = Get-Sha256 -LiteralPath $preservationVerifier

foreach ($root in @($buildTempRoot, $buildOutputRoot)) {
    if (-not (Test-Path -LiteralPath $root)) {
        New-Item -ItemType Directory -Path $root | Out-Null
    }
    Assert-PlainDirectory -LiteralPath $root -Label 'ignored build root'
}

$attemptRoot = Join-Path $buildTempRoot $BuildId
$attemptOutput = Join-Path $buildOutputRoot $BuildId
if (
    (Test-Path -LiteralPath $attemptRoot) -or
    (Test-Path -LiteralPath $attemptOutput)
) {
    throw 'BuildId is already used; A2b attempt identifiers are single-use.'
}

New-Item -ItemType Directory -Path $attemptRoot, $attemptOutput | Out-Null
$controlRoot = Join-Path $attemptRoot 'control'
$controlHome = Join-Path $controlRoot 'home'
$controlTemp = Join-Path $controlRoot 'tmp'
New-Item -ItemType Directory -Path $controlRoot, $controlHome, $controlTemp | Out-Null
$controlHomeMsys = ConvertTo-MsysPath -LiteralPath $controlHome
$controlTempMsys = ConvertTo-MsysPath -LiteralPath $controlTemp

$environment = @{
    CHERE_INVOKING = 'yes'
    HOME = $controlHome
    LANG = 'C'
    LANGUAGE = 'C'
    LC_ALL = 'C'
    MSYSTEM = 'UCRT64'
    MSYS2_PATH_TYPE = 'strict'
    PATH = "$msysRoot\ucrt64\bin;$msysRoot\usr\bin;$env:SystemRoot\System32"
    SOURCE_DATE_EPOCH = $script:SourceDateEpoch
    SystemRoot = $env:SystemRoot
    TEMP = $controlTemp
    TMP = $controlTemp
    TZ = 'UTC'
    USERPROFILE = $controlHome
    WINDIR = $env:WINDIR
}

$shellControls = @(
    'set -euo pipefail',
    'export PATH=/ucrt64/bin:/usr/bin',
    "export HOME='$controlHomeMsys'",
    "export TMPDIR='$controlTempMsys'",
    "export TEMP='$controlTempMsys'",
    "export TMP='$controlTempMsys'",
    'export CC=/ucrt64/bin/gcc',
    'export AR=/ucrt64/bin/ar',
    'export LD=/ucrt64/bin/ld',
    'export NM=/ucrt64/bin/nm',
    'export RANLIB=/ucrt64/bin/ranlib',
    'export STRIP=/ucrt64/bin/strip',
    'export CONFIG_SITE=/dev/null',
    (
        'unset ARFLAGS BASH_ENV CDPATH CFLAGS CL COMPILER_PATH CONFIG_SHELL ' +
        'CPATH CPPFLAGS CPLUS_INCLUDE_PATH C_INCLUDE_PATH DEPENDENCIES_OUTPUT ' +
        'ENV GCC_COMPARE_DEBUG GCC_EXEC_PREFIX INCLUDE LIB LIBRARY_PATH ' +
        'LDFLAGS MAKEFLAGS MFLAGS OBJC_INCLUDE_PATH PKG_CONFIG_LIBDIR ' +
        'PKG_CONFIG_PATH PKG_CONFIG_SYSROOT_DIR SUNPRO_DEPENDENCIES _CL_'
    )
) -join '; '

$toolchainCommand = @(
    $shellControls,
    'gcc_path=$(command -v gcc)',
    'make_path=$(command -v make)',
    'ld_path=$(command -v ld)',
    'pacman_path=$(command -v pacman)',
    'test "$gcc_path" = /ucrt64/bin/gcc',
    'test "$make_path" = /usr/bin/make',
    'test "$ld_path" = /ucrt64/bin/ld',
    'test "$pacman_path" = /usr/bin/pacman',
    'printf "RESOLVED_GCC=%s\n" "$gcc_path"',
    'printf "RESOLVED_MAKE=%s\n" "$make_path"',
    'printf "RESOLVED_LD=%s\n" "$ld_path"',
    'printf "RESOLVED_PACMAN=%s\n" "$pacman_path"',
    (
        '/usr/bin/pacman -Q bash pacman msys2-runtime ' +
        'mingw-w64-ucrt-x86_64-gcc make autoconf-wrapper ' +
        'automake-wrapper libtool pkgconf mingw-w64-ucrt-x86_64-binutils ' +
        'mingw-w64-ucrt-x86_64-headers mingw-w64-ucrt-x86_64-crt ' +
        'mingw-w64-ucrt-x86_64-gcc-libs'
    ),
    (
        '/usr/bin/pacman -Qkk bash pacman msys2-runtime ' +
        'mingw-w64-ucrt-x86_64-gcc make autoconf-wrapper ' +
        'automake-wrapper libtool pkgconf mingw-w64-ucrt-x86_64-binutils ' +
        'mingw-w64-ucrt-x86_64-headers mingw-w64-ucrt-x86_64-crt ' +
        'mingw-w64-ucrt-x86_64-gcc-libs'
    ),
    '/ucrt64/bin/gcc -dumpmachine',
    '/ucrt64/bin/gcc --version',
    '/ucrt64/bin/ld --version',
    '/usr/bin/make --version',
    '/usr/bin/autoconf --version',
    '/usr/bin/automake --version'
) -join '; '
$toolchainCapture = Invoke-CapturedProcess -FilePath $bash -Arguments @(
    '--noprofile',
    '--norc',
    '-c',
    $toolchainCommand
) -WorkingDirectory $repositoryRoot -Environment $environment -ClearEnvironment $true `
    -TimeoutSeconds 120
if ($toolchainCapture.TimedOut -or $toolchainCapture.ExitCode -ne 0) {
    throw 'Pinned UCRT64 toolchain inventory or package integrity failed.'
}
foreach ($expected in $script:ExpectedPackages) {
    if (
        $toolchainCapture.Stdout -notmatch (
            "(?m)^$([regex]::Escape($expected))\r?$"
        )
    ) {
        throw "Pinned package identity is missing: $expected"
    }
}
foreach ($expected in $script:ExpectedIntegrityRecords) {
    if (
        $toolchainCapture.Stdout -notmatch (
            "(?m)^$([regex]::Escape($expected))\r?$"
        )
    ) {
        throw "Pinned package integrity result is missing: $expected"
    }
}
foreach ($expected in @(
    'RESOLVED_GCC=/ucrt64/bin/gcc',
    'RESOLVED_MAKE=/usr/bin/make',
    'RESOLVED_LD=/ucrt64/bin/ld',
    'RESOLVED_PACMAN=/usr/bin/pacman'
)) {
    if (
        $toolchainCapture.Stdout -notmatch (
            "(?m)^$([regex]::Escape($expected))\r?$"
        )
    ) {
        throw "Resolved tool identity is missing: $expected"
    }
}
if ($toolchainCapture.Stdout -notmatch '(?m)^x86_64-w64-mingw32\r?$') {
    throw 'GCC target triple is not x86_64-w64-mingw32.'
}
$preservationBefore = Invoke-PreservationVerifier -RepositoryRoot $repositoryRoot
$sourceContainer = Join-Path $attemptRoot 'source'
$buildRoot = Join-Path $attemptRoot 'build\autotools'
$sourceRoot = Join-Path $sourceContainer 'nec2c-1.3.1'
$replacementMap = @{
    (ConvertTo-MsysPath -LiteralPath $attemptRoot) = '<ATTEMPT_ROOT>'
    (ConvertTo-MsysPath -LiteralPath $repositoryRoot) = '<REPOSITORY_ROOT>'
    $attemptRoot.Replace('\', '/') = '<ATTEMPT_ROOT>'
    $repositoryRoot.Replace('\', '/') = '<REPOSITORY_ROOT>'
    $msysRoot.Replace('\', '/') = '<MSYS2_ROOT>'
    $attemptRoot = '<ATTEMPT_ROOT>'
    $repositoryRoot = '<REPOSITORY_ROOT>'
    $msysRoot = '<MSYS2_ROOT>'
}

$attemptStarted = [DateTime]::UtcNow
$exitCode = 20
$attempt = [ordered]@{
    artifacts = @()
    authentication_helpers = [ordered]@{
        preservation_verifier_sha256 = $preservationVerifierSha256
        preservation_wrapper_sha256 = $preservationWrapperSha256
        source_guard_sha256 = $sourceGuardSha256
    }
    autotools = [ordered]@{
        configure = $null
        make = $null
    }
    build_id = $BuildId
    completed_utc = $null
    direct_gcc = [ordered]@{
        reason = (
            'The shipped Autotools route is authoritative. A direct command is not used to ' +
            'bypass a configure, compile, or link result from that route.'
        )
        status = 'not_attempted'
    }
    driver = [ordered]@{
        path = 'build-support/windows-x64-mingw-ucrt64/build.ps1'
        sha256 = $driverSha256
    }
    driver_exit_code = $null
    driver_error = $null
    duration_milliseconds = $null
    environment = [ordered]@{
        AR = '/ucrt64/bin/ar'
        CC = '/ucrt64/bin/gcc'
        CHERE_INVOKING = 'yes'
        CONFIG_SITE = '/dev/null'
        HOME = '<ATTEMPT_ROOT>/control/home'
        LANG = 'C'
        LANGUAGE = 'C'
        LC_ALL = 'C'
        LD = '/ucrt64/bin/ld'
        MSYSTEM = 'UCRT64'
        MSYS2_PATH_TYPE = 'strict'
        NM = '/ucrt64/bin/nm'
        PATH = '/ucrt64/bin:/usr/bin'
        RANLIB = '/ucrt64/bin/ranlib'
        SOURCE_DATE_EPOCH = $script:SourceDateEpoch
        STRIP = '/ucrt64/bin/strip'
        TEMP = '<ATTEMPT_ROOT>/control/tmp'
        TMP = '<ATTEMPT_ROOT>/control/tmp'
        TMPDIR = '<ATTEMPT_ROOT>/control/tmp'
        TZ = 'UTC'
    }
    environment_boundary = [ordered]@{
        arbitrary_parent_variables_inherited = $false
        environment_policy = 'explicit allowlist'
        shell_invocation = 'bash --noprofile --norc -c'
        startup_files_executed = $false
        windows_runtime_variables_copied = @('SystemRoot', 'WINDIR')
    }
    failing_stage = $null
    failure = $null
    outcome = 'validation_failed'
    preservation = [ordered]@{
        after = $null
        before = [ordered]@{
            archive_sha256 = $script:ExpectedArchiveSha256
            passed = $true
            verifier_sha256 = $preservationVerifierSha256
            verifier_stdout_sha256 = $null
            wrapper_sha256 = $preservationWrapperSha256
        }
    }
    schema = 'org.sutherlandryan.hf-nec2c.windows-x64-mingw-ucrt64-attempt.v1'
    source_authentication = [ordered]@{
        after = $false
        before = $false
        file_count = 34
        source_guard_sha256 = $sourceGuardSha256
    }
    started_utc = $attemptStarted.ToString('o')
    toolchain = [ordered]@{
        bash_path = '/usr/bin/bash'
        bash_sha256 = $script:ExpectedBashSha256
        compiler_path = '/ucrt64/bin/gcc'
        gcc_sha256 = $script:ExpectedGccSha256
        integrity = [ordered]@{
            package_count = $script:ExpectedIntegrityRecords.Count
            status = 'pacman-Qkk-zero-altered-files-at-attempt-start'
        }
        inventory_stdout_sha256 = $null
        linker_path = '/ucrt64/bin/ld'
        linker_sha256 = $script:ExpectedLdSha256
        make_path = '/usr/bin/make'
        msys_runtime_path = '/usr/bin/msys-2.0.dll'
        msys_runtime_sha256 = $script:ExpectedMsysRuntimeSha256
        pacman_path = '/usr/bin/pacman'
        pacman_sha256 = $script:ExpectedPacmanSha256
        target = 'x86_64-w64-mingw32'
    }
}

try {
    $preservationBeforePath = Join-Path $attemptOutput 'preservation-before.stdout.txt'
    Write-Utf8Text -LiteralPath $preservationBeforePath -Text $preservationBefore.Stdout
    $attempt.preservation.before.verifier_stdout_sha256 = (
        Get-Sha256 -LiteralPath $preservationBeforePath
    )

    $toolchainPath = Join-Path $attemptOutput 'toolchain.stdout.txt'
    Write-Utf8Text -LiteralPath $toolchainPath -Text $toolchainCapture.Stdout
    Write-Utf8Text -LiteralPath (
        Join-Path $attemptOutput 'toolchain.stderr.txt'
    ) -Text $toolchainCapture.Stderr
    $attempt.toolchain.inventory_stdout_sha256 = Get-Sha256 -LiteralPath $toolchainPath

    [void](Invoke-SourceGuard -Operation extract -RepositoryRoot $repositoryRoot `
        -SourceRoot $sourceContainer)
    [void](Invoke-SourceGuard -Operation verify -RepositoryRoot $repositoryRoot `
        -SourceRoot $sourceContainer)
    $attempt.source_authentication.before = $true
    New-Item -ItemType Directory -Path $buildRoot | Out-Null

    $sourceMsys = ConvertTo-MsysPath -LiteralPath $sourceRoot
    $buildMsys = ConvertTo-MsysPath -LiteralPath $buildRoot
    $flags = (
        "-O2 -fno-ident -ffile-prefix-map=$sourceMsys=/usr/src/nec2c-1.3.1 " +
        "-fdebug-prefix-map=$sourceMsys=/usr/src/nec2c-1.3.1"
    )
    $configureCommand = @(
        $shellControls,
        "export CFLAGS='$flags'",
        "export CPPFLAGS=''",
        "export LDFLAGS='-Wl,--no-insert-timestamp -Wl,--build-id=none'",
        'umask 022',
        "cd '$buildMsys'",
        "'$sourceMsys/configure'"
    ) -join '; '
    $configureCapture = Invoke-CapturedProcess -FilePath $bash -Arguments @(
        '--noprofile',
        '--norc',
        '-c',
        $configureCommand
    ) -WorkingDirectory $repositoryRoot -Environment $environment -ClearEnvironment $true `
        -TimeoutSeconds 120
    $attempt.autotools.configure = Write-CaptureEvidence -Capture $configureCapture `
        -OutputRoot $attemptOutput -Name 'configure' -ReplacementMap $replacementMap

    if ($configureCapture.TimedOut) {
        throw 'Autotools configure timed out.'
    }
    if ($configureCapture.ExitCode -ne 0) {
        $attempt.outcome = 'unmodified_source_build_failed'
        $attempt.failing_stage = 'autotools_configure'
        $attempt.failure = [ordered]@{
            category = 'autotools_configuration_failure'
            diagnostic = 'See normalized configure evidence.'
        }
        $exitCode = 10
    }
    else {
        $makeCapture = Invoke-CapturedProcess -FilePath $bash -Arguments @(
            '--noprofile',
            '--norc',
            '-c',
            "$shellControls; umask 022; cd '$buildMsys'; /usr/bin/make -j1 V=1"
        ) -WorkingDirectory $repositoryRoot -Environment $environment -ClearEnvironment $true `
            -TimeoutSeconds 300
        $attempt.autotools.make = Write-CaptureEvidence -Capture $makeCapture `
            -OutputRoot $attemptOutput -Name 'make' -ReplacementMap $replacementMap
        if ($makeCapture.TimedOut) {
            throw 'GNU make timed out.'
        }
        if ($makeCapture.ExitCode -ne 0) {
            $combined = "$($makeCapture.Stdout)`n$($makeCapture.Stderr)"
            $expectedBlocker = (
                $combined -match 'nec2c\.h:15:10: fatal error: sys/times\.h: No such file or directory'
            )
            $attempt.outcome = 'unmodified_source_build_failed'
            if ($expectedBlocker) {
                $attempt.failing_stage = 'compile'
                $attempt.failure = [ordered]@{
                    category = 'compile_time_header_failure'
                    expected_blocker_matched = $true
                    first_reached_blocker = 'original nec2c.h line 15 requires sys/times.h'
                }
            }
            else {
                $attempt.failing_stage = 'autotools_make'
                $attempt.failure = [ordered]@{
                    category = 'autotools_make_failure'
                    expected_blocker_matched = $false
                    diagnostic = 'See normalized make evidence.'
                }
            }
            $exitCode = 10
        }
        else {
            $attempt.outcome = 'unexpected_build_success_requires_validation'
            $attempt.failing_stage = 'success_only_validation'
            $attempt.failure = [ordered]@{
                category = 'unexpected_success'
                diagnostic = (
                    'A successful link requires two fresh builds, PE/import inspection, ' +
                    'and bounded smoke validation before this driver can return success.'
                )
            }
            $exitCode = 20
        }
    }
    $attempt.artifacts = @(Get-BuildInventory -BuildRoot $buildRoot)
}
catch {
    $attempt.outcome = 'validation_failed'
    $attempt.failing_stage = 'build_driver'
    $attempt.driver_error = Normalize-Diagnostics -Text $_.Exception.Message `
        -ReplacementMap $replacementMap
    $exitCode = 20
}
finally {
    try {
        if (Test-Path -LiteralPath $sourceContainer -PathType Container) {
            [void](Invoke-SourceGuard -Operation verify -RepositoryRoot $repositoryRoot `
                -SourceRoot $sourceContainer)
            $attempt.source_authentication.after = $true
        }
    }
    catch {
        $attempt.outcome = 'validation_failed'
        $attempt.failing_stage = 'post_build_source_authentication'
        $attempt.driver_error = Normalize-Diagnostics -Text $_.Exception.Message `
            -ReplacementMap $replacementMap
        $exitCode = 20
    }
    try {
        $preservationAfter = Invoke-PreservationVerifier -RepositoryRoot $repositoryRoot
        $preservationAfterPath = Join-Path $attemptOutput 'preservation-after.stdout.txt'
        Write-Utf8Text -LiteralPath $preservationAfterPath -Text $preservationAfter.Stdout
        $attempt.preservation.after = [ordered]@{
            archive_sha256 = $script:ExpectedArchiveSha256
            passed = $true
            verifier_sha256 = $preservationVerifierSha256
            verifier_stdout_sha256 = Get-Sha256 -LiteralPath $preservationAfterPath
            wrapper_sha256 = $preservationWrapperSha256
        }
    }
    catch {
        $attempt.outcome = 'validation_failed'
        $attempt.failing_stage = 'post_build_preservation'
        $attempt.driver_error = Normalize-Diagnostics -Text $_.Exception.Message `
            -ReplacementMap $replacementMap
        $exitCode = 20
    }

    $completed = [DateTime]::UtcNow
    $attempt.completed_utc = $completed.ToString('o')
    $attempt.driver_exit_code = $exitCode
    $attempt.duration_milliseconds = [long]($completed - $attemptStarted).TotalMilliseconds
    $recordPath = Join-Path $attemptOutput 'attempt-result.json'
    $temporaryPath = "$recordPath.tmp"
    try {
        if (
            (Test-Path -LiteralPath $recordPath) -or
            (Test-Path -LiteralPath $temporaryPath)
        ) {
            throw 'Fresh attempt-result path unexpectedly already exists.'
        }
        Write-Utf8Text -LiteralPath $temporaryPath -Text (
            ($attempt | ConvertTo-Json -Depth 12) + "`n"
        )
        Move-Item -LiteralPath $temporaryPath -Destination $recordPath
    }
    catch {
        $exitCode = 20
        [Console]::Error.WriteLine(
            "A2b attempt record could not be written atomically: $($_.Exception.Message)"
        )
    }
}

Write-Output "A2b attempt outcome: $($attempt.outcome)"
Write-Output "A2b attempt stage: $($attempt.failing_stage)"
Write-Output "A2b attempt record: .build-output/$BuildId/attempt-result.json"
exit $exitCode
