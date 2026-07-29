# SPDX-License-Identifier: BSD-2-Clause

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$')]
    [string]$BuildId
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 3.0

$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$script:SourceNames = @(
    'calculations.c',
    'geometry.c',
    'input.c',
    'matrix.c',
    'network.c',
    'shared.c',
    'fields.c',
    'ground.c',
    'main.c',
    'misc.c',
    'radiation.c',
    'somnec.c'
)

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

function Invoke-CapturedProcess {
    param(
        [Parameter(Mandatory)]
        [string]$Executable,

        [Parameter(Mandatory)]
        [string[]]$Arguments,

        [Parameter(Mandatory)]
        [string]$WorkingDirectory,

        [Parameter(Mandatory)]
        [hashtable]$Environment,

        [Parameter(Mandatory)]
        [string]$StdoutPath,

        [Parameter(Mandatory)]
        [string]$StderrPath,

        [int]$TimeoutSeconds = 120
    )

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $Executable
    $startInfo.Arguments = (($Arguments | ForEach-Object {
                ConvertTo-WindowsCommandLineArgument -Value $_
            }) -join ' ')
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.EnvironmentVariables.Clear()
    foreach ($name in ($Environment.Keys | Sort-Object)) {
        $startInfo.EnvironmentVariables[$name] = [string]$Environment[$name]
    }

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    if (-not $process.Start()) {
        throw "Process could not start: $Executable"
    }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $completed = $process.WaitForExit($TimeoutSeconds * 1000)
    if (-not $completed) {
        try {
            $process.Kill()
        }
        catch {
            # The timeout result remains authoritative even if termination races process exit.
        }
        $process.WaitForExit()
    }
    $stdout = $stdoutTask.Result
    $stderr = $stderrTask.Result
    $stopwatch.Stop()
    [System.IO.File]::WriteAllText($StdoutPath, $stdout, $script:Utf8NoBom)
    [System.IO.File]::WriteAllText($StderrPath, $stderr, $script:Utf8NoBom)

    return [pscustomobject][ordered]@{
        ExitCode = if ($completed) { $process.ExitCode } else { $null }
        TimedOut = -not $completed
        DurationMilliseconds = $stopwatch.ElapsedMilliseconds
        Stdout = $stdout
        Stderr = $stderr
    }
}

function Get-PythonInvocation {
    $launcher = Get-Command -Name 'py.exe' -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -ne $launcher) {
        return [pscustomobject]@{
            Executable = $launcher.Source
            Prefix = @('-3', '-I')
        }
    }
    $launcher = Get-Command -Name 'python.exe' -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -ne $launcher) {
        return [pscustomobject]@{
            Executable = $launcher.Source
            Prefix = @('-I')
        }
    }
    throw 'Python 3 is required for authenticated source extraction.'
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

    $python = Get-PythonInvocation
    $helper = Join-Path $PSScriptRoot 'source_guard.py'
    $arguments = @($python.Prefix) + @(
        $helper,
        $Operation,
        '--repository-root',
        $RepositoryRoot,
        '--source-root',
        $SourceRoot
    )
    & $python.Executable @arguments
    $guardExit = $LASTEXITCODE
    if ($guardExit -ne 0) {
        throw "Source guard failed during $Operation with exit code $guardExit."
    }
}

function Invoke-PreservationVerifier {
    param(
        [Parameter(Mandatory)]
        [string]$RepositoryRoot
    )

    $verifier = Join-Path $RepositoryRoot 'verify-preservation.ps1'
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $verifier `
        -RepositoryRoot $RepositoryRoot
    $verifierExit = $LASTEXITCODE
    if ($verifierExit -ne 0) {
        throw "Preservation verifier failed with exit code $verifierExit."
    }
}

function Get-LatestVersionDirectory {
    param(
        [Parameter(Mandatory)]
        [string]$LiteralPath
    )

    $candidates = @(Get-ChildItem -LiteralPath $LiteralPath -Directory -ErrorAction Stop |
            ForEach-Object {
                try {
                    [pscustomobject]@{
                        Item = $_
                        Version = [Version]$_.Name
                    }
                }
                catch {
                    $null
                }
            } |
            Where-Object { $null -ne $_ } |
            Sort-Object -Property Version -Descending)
    if ($candidates.Count -eq 0) {
        throw "No versioned directory exists below the selected tool root."
    }
    return $candidates[0].Item.FullName
}

function Get-MsvcToolchain {
    $programFilesX86 = ${env:ProgramFiles(x86)}
    if ([string]::IsNullOrWhiteSpace($programFilesX86)) {
        throw 'ProgramFiles(x86) is unavailable.'
    }
    $vswhere = Join-Path $programFilesX86 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (-not (Test-Path -LiteralPath $vswhere -PathType Leaf)) {
        throw 'Visual Studio locator is unavailable.'
    }
    $installationRoot = (& $vswhere -latest -products '*' `
            -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
            -property installationPath | Select-Object -First 1)
    $vswhereExit = $LASTEXITCODE
    if ($vswhereExit -ne 0 -or [string]::IsNullOrWhiteSpace($installationRoot)) {
        throw 'No Visual C++ x64 toolset is installed.'
    }

    $vcToolsRoot = Get-LatestVersionDirectory -LiteralPath (
        Join-Path $installationRoot 'VC\Tools\MSVC'
    )
    $binaryRoot = Join-Path $vcToolsRoot 'bin\Hostx64\x64'
    $cl = Join-Path $binaryRoot 'cl.exe'
    $link = Join-Path $binaryRoot 'link.exe'
    $dumpbin = Join-Path $binaryRoot 'dumpbin.exe'
    foreach ($tool in @($cl, $link, $dumpbin)) {
        if (-not (Test-Path -LiteralPath $tool -PathType Leaf)) {
            throw 'The selected Visual C++ x64 toolset is incomplete.'
        }
    }

    $sdkRoot = Join-Path $programFilesX86 'Windows Kits\10'
    $sdkVersionRoot = Get-LatestVersionDirectory -LiteralPath (
        Join-Path $sdkRoot 'Include'
    )
    $sdkVersion = Split-Path -Leaf $sdkVersionRoot
    $sdkLibRoot = Join-Path (Join-Path $sdkRoot 'Lib') $sdkVersion
    foreach ($required in @(
            (Join-Path $vcToolsRoot 'include'),
            (Join-Path $vcToolsRoot 'lib\x64'),
            (Join-Path $sdkVersionRoot 'ucrt'),
            (Join-Path $sdkVersionRoot 'shared'),
            (Join-Path $sdkVersionRoot 'um'),
            (Join-Path $sdkLibRoot 'ucrt\x64'),
            (Join-Path $sdkLibRoot 'um\x64')
        )) {
        if (-not (Test-Path -LiteralPath $required -PathType Container)) {
            throw 'The selected Visual C++ or Windows SDK installation is incomplete.'
        }
    }

    return [pscustomobject][ordered]@{
        InstallationRoot = $installationRoot
        VcToolsRoot = $vcToolsRoot
        SdkRoot = $sdkRoot
        SdkVersion = $sdkVersion
        Cl = $cl
        Link = $link
        Dumpbin = $dumpbin
        CompilerVersion = (Get-Item -LiteralPath $cl).VersionInfo.FileVersion
        LinkerVersion = (Get-Item -LiteralPath $link).VersionInfo.FileVersion
        Include = (@(
                (Join-Path $vcToolsRoot 'include'),
                (Join-Path $sdkVersionRoot 'ucrt'),
                (Join-Path $sdkVersionRoot 'shared'),
                (Join-Path $sdkVersionRoot 'um'),
                (Join-Path $sdkVersionRoot 'winrt')
            ) -join ';')
        Lib = (@(
                (Join-Path $vcToolsRoot 'lib\x64'),
                (Join-Path $sdkLibRoot 'ucrt\x64'),
                (Join-Path $sdkLibRoot 'um\x64')
            ) -join ';')
    }
}

function Get-ControlledEnvironment {
    param(
        [Parameter(Mandatory)]
        [pscustomobject]$Toolchain,

        [Parameter(Mandatory)]
        [string]$TemporaryDirectory
    )

    $systemRoot = $env:SystemRoot
    $comSpec = $env:ComSpec
    if ([string]::IsNullOrWhiteSpace($systemRoot) -or [string]::IsNullOrWhiteSpace($comSpec)) {
        throw 'Required Windows process environment values are unavailable.'
    }
    $binaryRoot = Split-Path -Parent $Toolchain.Cl
    return @{
        'CL' = ''
        '_CL_' = ''
        'ComSpec' = $comSpec
        'INCLUDE' = $Toolchain.Include
        'LANG' = 'C'
        'LANGUAGE' = 'C'
        'LC_ALL' = 'C'
        'LIB' = $Toolchain.Lib
        'LIBPATH' = ''
        'LINK' = ''
        '_LINK_' = ''
        'PATH' = "$binaryRoot;$systemRoot\System32;$systemRoot"
        'PATHEXT' = '.COM;.EXE;.BAT;.CMD'
        'SOURCE_DATE_EPOCH' = '1701496474'
        'SystemRoot' = $systemRoot
        'TEMP' = $TemporaryDirectory
        'TMP' = $TemporaryDirectory
        'TZ' = 'UTC'
        'VSLANG' = '1033'
        'windir' = $systemRoot
    }
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
    $keys = @($ReplacementMap.Keys | Sort-Object -Property Length -Descending)
    foreach ($key in $keys) {
        if (-not [string]::IsNullOrEmpty($key)) {
            $normalized = $normalized.Replace($key, [string]$ReplacementMap[$key])
            $normalized = $normalized.Replace(
                $key.Replace('\', '/'),
                [string]$ReplacementMap[$key]
            )
        }
    }
    return $normalized
}

function Get-PeFacts {
    param(
        [Parameter(Mandatory)]
        [string]$ExecutablePath
    )

    $bytes = [System.IO.File]::ReadAllBytes($ExecutablePath)
    if ($bytes.Length -lt 256 -or $bytes[0] -ne 0x4d -or $bytes[1] -ne 0x5a) {
        throw 'Output is not an MZ executable.'
    }
    $peOffset = [BitConverter]::ToInt32($bytes, 0x3c)
    if (
        $peOffset -lt 64 -or
        $peOffset + 24 -gt $bytes.Length -or
        $bytes[$peOffset] -ne 0x50 -or
        $bytes[$peOffset + 1] -ne 0x45 -or
        $bytes[$peOffset + 2] -ne 0 -or
        $bytes[$peOffset + 3] -ne 0
    ) {
        throw 'Output has an invalid PE signature.'
    }
    $machine = [BitConverter]::ToUInt16($bytes, $peOffset + 4)
    $sectionCount = [BitConverter]::ToUInt16($bytes, $peOffset + 6)
    $timestamp = [BitConverter]::ToUInt32($bytes, $peOffset + 8)
    $optionalHeaderBytes = [BitConverter]::ToUInt16($bytes, $peOffset + 20)
    $optionalMagic = [BitConverter]::ToUInt16($bytes, $peOffset + 24)
    if ($machine -ne 0x8664 -or $optionalMagic -ne 0x020b) {
        throw 'Output is not a PE32+ AMD64 executable.'
    }
    $sectionTableOffset = $peOffset + 24 + $optionalHeaderBytes
    if ($sectionTableOffset + (40 * $sectionCount) -gt $bytes.Length) {
        throw 'PE section table extends beyond the executable.'
    }
    $sections = @(
        for ($index = 0; $index -lt $sectionCount; $index += 1) {
            $offset = $sectionTableOffset + (40 * $index)
            $name = [System.Text.Encoding]::ASCII.GetString($bytes, $offset, 8).Trim([char]0)
            $rawBytes = [BitConverter]::ToUInt32($bytes, $offset + 16)
            $rawOffset = [BitConverter]::ToUInt32($bytes, $offset + 20)
            if ($rawBytes -gt 0 -and $rawOffset + $rawBytes -gt $bytes.Length) {
                throw "PE section $name extends beyond the executable."
            }
            [pscustomobject][ordered]@{
                Name = $name
                VirtualBytes = [BitConverter]::ToUInt32($bytes, $offset + 8)
                VirtualAddress = [BitConverter]::ToUInt32($bytes, $offset + 12)
                RawBytes = $rawBytes
                RawOffset = $rawOffset
                Characteristics = ('0x{0:x8}' -f (
                        [BitConverter]::ToUInt32($bytes, $offset + 36)
                    ))
            }
        }
    )
    return [pscustomobject][ordered]@{
        Machine = '0x8664'
        Format = 'PE32+'
        SectionCount = $sectionCount
        Sections = $sections
        CoffTimestamp = $timestamp
        ByteCount = $bytes.Length
        Sha256 = Get-Sha256 -LiteralPath $ExecutablePath
    }
}

function Invoke-SmokeCase {
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [string]$Executable,

        [Parameter(Mandatory)]
        [string[]]$Arguments,

        [Parameter(Mandatory)]
        [string]$WorkingDirectory,

        [Parameter(Mandatory)]
        [hashtable]$Environment,

        [Parameter(Mandatory)]
        [string]$LogDirectory,

        [string]$OutputName
    )

    $stdoutPath = Join-Path $LogDirectory "$Name.stdout.log"
    $stderrPath = Join-Path $LogDirectory "$Name.stderr.log"
    $result = Invoke-CapturedProcess -Executable $Executable -Arguments $Arguments `
        -WorkingDirectory $WorkingDirectory -Environment $Environment `
        -StdoutPath $stdoutPath -StderrPath $stderrPath -TimeoutSeconds 30
    $outputPath = if ([string]::IsNullOrWhiteSpace($OutputName)) {
        $null
    }
    else {
        Join-Path $WorkingDirectory $OutputName
    }
    return [pscustomobject][ordered]@{
        Name = $Name
        ExitCode = $result.ExitCode
        TimedOut = $result.TimedOut
        DurationMilliseconds = $result.DurationMilliseconds
        StdoutBytes = (Get-Item -LiteralPath $stdoutPath).Length
        StdoutSha256 = Get-Sha256 -LiteralPath $stdoutPath
        StderrBytes = (Get-Item -LiteralPath $stderrPath).Length
        StderrSha256 = Get-Sha256 -LiteralPath $stderrPath
        OutputCreated = $null -ne $outputPath -and (Test-Path -LiteralPath $outputPath -PathType Leaf)
        OutputBytes = if ($null -ne $outputPath -and (Test-Path -LiteralPath $outputPath -PathType Leaf)) {
            (Get-Item -LiteralPath $outputPath).Length
        }
        else {
            $null
        }
        OutputSha256 = if ($null -ne $outputPath -and (Test-Path -LiteralPath $outputPath -PathType Leaf)) {
            Get-Sha256 -LiteralPath $outputPath
        }
        else {
            $null
        }
    }
}

$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
Assert-PlainDirectory -LiteralPath $repositoryRoot -Label 'repository root'

$buildTempRoot = Join-Path $repositoryRoot '.build-temp'
$buildOutputRoot = Join-Path $repositoryRoot '.build-output'
foreach ($root in @($buildTempRoot, $buildOutputRoot)) {
    if (-not (Test-Path -LiteralPath $root)) {
        [void](New-Item -ItemType Directory -Path $root)
    }
    Assert-PlainDirectory -LiteralPath $root -Label (Split-Path -Leaf $root)
}

$attemptRoot = Join-Path $buildTempRoot $BuildId
$attemptOutput = Join-Path $buildOutputRoot $BuildId
foreach ($freshPath in @($attemptRoot, $attemptOutput)) {
    if (Test-Path -LiteralPath $freshPath) {
        throw "Fresh build path already exists: $(Split-Path -Leaf $freshPath)"
    }
}
[void](New-Item -ItemType Directory -Path $attemptRoot)
[void](New-Item -ItemType Directory -Path $attemptOutput)
$sourceRoot = Join-Path $attemptRoot 'source'
$buildRoot = Join-Path $attemptRoot 'build'
$temporaryRoot = Join-Path $buildRoot 'tmp'
$logRoot = Join-Path $attemptOutput 'logs'
foreach ($directory in @($buildRoot, $temporaryRoot, $logRoot)) {
    [void](New-Item -ItemType Directory -Path $directory)
}

$attemptStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$attempt = [ordered]@{
    Schema = 'org.sutherlandryan.hf-nec2c.windows-x64-local-attempt.v1'
    BuildId = $BuildId
    Outcome = 'validation_failed'
    FailingStage = 'pre_build_validation'
    SourceAuthenticationBeforeBuild = $false
    SourceAuthenticationAfterBuild = $false
    PreservationBeforeBuild = $false
    PreservationAfterBuild = $false
    CompilerExitCode = $null
    LinkerExitCode = $null
    Executable = $null
    Smoke = $null
    CompileDiagnostics = $null
    LinkDiagnostics = $null
    DriverError = $null
    PostBuildErrors = @()
    DurationMilliseconds = $null
}
$exitCode = 20
$toolchain = $null

try {
    Invoke-PreservationVerifier -RepositoryRoot $repositoryRoot
    $attempt.PreservationBeforeBuild = $true
    Invoke-SourceGuard -Operation extract -RepositoryRoot $repositoryRoot `
        -SourceRoot $sourceRoot
    Invoke-SourceGuard -Operation verify -RepositoryRoot $repositoryRoot `
        -SourceRoot $sourceRoot
    $attempt.SourceAuthenticationBeforeBuild = $true

    $toolchain = Get-MsvcToolchain
    $sourceDirectory = Join-Path $sourceRoot 'nec2c-1.3.1'
    $environment = Get-ControlledEnvironment -Toolchain $toolchain `
        -TemporaryDirectory $temporaryRoot
    $compileArguments = @(
        '/nologo',
        '/TC',
        '/std:c11',
        '/O2',
        '/W4',
        '/MD',
        '/Brepro',
        '/DPACKAGE_STRING="nec2c 1.3.1"',
        '/c'
    ) + $script:SourceNames + @('/Fo..\..\build\')
    $compileStdout = Join-Path $logRoot 'compile.stdout.raw.log'
    $compileStderr = Join-Path $logRoot 'compile.stderr.raw.log'
    $compile = Invoke-CapturedProcess -Executable $toolchain.Cl `
        -Arguments $compileArguments -WorkingDirectory $sourceDirectory `
        -Environment $environment -StdoutPath $compileStdout `
        -StderrPath $compileStderr -TimeoutSeconds 300
    $attempt.CompilerExitCode = $compile.ExitCode

    $replacements = @{
        $repositoryRoot = '${REPOSITORY_ROOT}'
        $attemptRoot = '${ATTEMPT_ROOT}'
        $toolchain.InstallationRoot = '${VISUAL_STUDIO_ROOT}'
        $toolchain.SdkRoot = '${WINDOWS_SDK_ROOT}'
    }
    if (-not [string]::IsNullOrWhiteSpace($env:USERNAME)) {
        $replacements[$env:USERNAME] = '${LOCAL_USER}'
    }
    $normalizedStdout = Normalize-Diagnostics -Text $compile.Stdout `
        -ReplacementMap $replacements
    $normalizedStderr = Normalize-Diagnostics -Text $compile.Stderr `
        -ReplacementMap $replacements
    $normalizedStdoutPath = Join-Path $logRoot 'compile.stdout.normalized.log'
    $normalizedStderrPath = Join-Path $logRoot 'compile.stderr.normalized.log'
    [System.IO.File]::WriteAllText(
        $normalizedStdoutPath,
        $normalizedStdout,
        $script:Utf8NoBom
    )
    [System.IO.File]::WriteAllText(
        $normalizedStderrPath,
        $normalizedStderr,
        $script:Utf8NoBom
    )
    $attempt.CompileDiagnostics = [ordered]@{
        RawStdoutBytes = (Get-Item -LiteralPath $compileStdout).Length
        RawStdoutSha256 = Get-Sha256 -LiteralPath $compileStdout
        RawStderrBytes = (Get-Item -LiteralPath $compileStderr).Length
        RawStderrSha256 = Get-Sha256 -LiteralPath $compileStderr
        NormalizedStdoutBytes = (Get-Item -LiteralPath $normalizedStdoutPath).Length
        NormalizedStdoutSha256 = Get-Sha256 -LiteralPath $normalizedStdoutPath
        NormalizedStderrBytes = (Get-Item -LiteralPath $normalizedStderrPath).Length
        NormalizedStderrSha256 = Get-Sha256 -LiteralPath $normalizedStderrPath
        NormalizedStdout = $normalizedStdout
        NormalizedStderr = $normalizedStderr
    }

    if ($compile.TimedOut) {
        $attempt.Outcome = 'unmodified_source_build_failed'
        $attempt.FailingStage = 'compile_timeout'
        $exitCode = 10
    }
    elseif ($compile.ExitCode -ne 0) {
        $attempt.Outcome = 'unmodified_source_build_failed'
        $attempt.FailingStage = 'compile'
        $exitCode = 10
    }
    else {
        $objectNames = $script:SourceNames | ForEach-Object {
            "..\..\build\$([System.IO.Path]::GetFileNameWithoutExtension($_)).obj"
        }
        $linkArguments = @(
            '/NOLOGO',
            '/OUT:..\..\build\nec2c.exe',
            '/MACHINE:X64',
            '/SUBSYSTEM:CONSOLE',
            '/INCREMENTAL:NO',
            '/BREPRO'
        ) + $objectNames
        $linkStdout = Join-Path $logRoot 'link.stdout.raw.log'
        $linkStderr = Join-Path $logRoot 'link.stderr.raw.log'
        $link = Invoke-CapturedProcess -Executable $toolchain.Link `
            -Arguments $linkArguments -WorkingDirectory $sourceDirectory `
            -Environment $environment -StdoutPath $linkStdout `
            -StderrPath $linkStderr -TimeoutSeconds 300
        $attempt.LinkerExitCode = $link.ExitCode
        $normalizedLinkStdout = Normalize-Diagnostics -Text $link.Stdout `
            -ReplacementMap $replacements
        $normalizedLinkStderr = Normalize-Diagnostics -Text $link.Stderr `
            -ReplacementMap $replacements
        $normalizedLinkStdoutPath = Join-Path $logRoot 'link.stdout.normalized.log'
        $normalizedLinkStderrPath = Join-Path $logRoot 'link.stderr.normalized.log'
        [System.IO.File]::WriteAllText(
            $normalizedLinkStdoutPath,
            $normalizedLinkStdout,
            $script:Utf8NoBom
        )
        [System.IO.File]::WriteAllText(
            $normalizedLinkStderrPath,
            $normalizedLinkStderr,
            $script:Utf8NoBom
        )
        $attempt.LinkDiagnostics = [ordered]@{
            RawStdoutBytes = (Get-Item -LiteralPath $linkStdout).Length
            RawStdoutSha256 = Get-Sha256 -LiteralPath $linkStdout
            RawStderrBytes = (Get-Item -LiteralPath $linkStderr).Length
            RawStderrSha256 = Get-Sha256 -LiteralPath $linkStderr
            NormalizedStdoutBytes = (
                Get-Item -LiteralPath $normalizedLinkStdoutPath
            ).Length
            NormalizedStdoutSha256 = Get-Sha256 -LiteralPath $normalizedLinkStdoutPath
            NormalizedStderrBytes = (
                Get-Item -LiteralPath $normalizedLinkStderrPath
            ).Length
            NormalizedStderrSha256 = Get-Sha256 -LiteralPath $normalizedLinkStderrPath
            NormalizedStdout = $normalizedLinkStdout
            NormalizedStderr = $normalizedLinkStderr
        }
        if ($link.TimedOut -or $link.ExitCode -ne 0) {
            $attempt.Outcome = 'unmodified_source_build_failed'
            $attempt.FailingStage = if ($link.TimedOut) { 'link_timeout' } else { 'link' }
            $exitCode = 10
        }
        else {
            $executable = Join-Path $buildRoot 'nec2c.exe'
            $peFacts = Get-PeFacts -ExecutablePath $executable
            $binaryBytes = [System.IO.File]::ReadAllBytes($executable)
            $ascii = [System.Text.Encoding]::ASCII.GetString($binaryBytes)
            $unicode = [System.Text.Encoding]::Unicode.GetString($binaryBytes)
            foreach ($forbidden in @(
                    $env:USERNAME,
                    $repositoryRoot,
                    $attemptRoot
                )) {
                if (
                    -not [string]::IsNullOrEmpty($forbidden) -and
                    (
                        $ascii.IndexOf($forbidden, [StringComparison]::OrdinalIgnoreCase) -ge 0 -or
                        $unicode.IndexOf($forbidden, [StringComparison]::OrdinalIgnoreCase) -ge 0
                    )
                ) {
                    throw 'Executable contains forbidden machine-local identity data.'
                }
            }
            if ($ascii.IndexOf('.pdb', [StringComparison]::OrdinalIgnoreCase) -ge 0) {
                throw 'Executable contains an embedded PDB path.'
            }

            $inspectStdout = Join-Path $logRoot 'dumpbin.stdout.raw.log'
            $inspectStderr = Join-Path $logRoot 'dumpbin.stderr.raw.log'
            $inspect = Invoke-CapturedProcess -Executable $toolchain.Dumpbin `
                -Arguments @('/HEADERS', '/IMPORTS', '/EXPORTS', $executable) `
                -WorkingDirectory $buildRoot -Environment $environment `
                -StdoutPath $inspectStdout -StderrPath $inspectStderr `
                -TimeoutSeconds 60
            if ($inspect.TimedOut -or $inspect.ExitCode -ne 0) {
                throw 'DUMPBIN inspection failed.'
            }
            $imports = @($inspect.Stdout -split "`r?`n" |
                    ForEach-Object {
                        if ($_ -match '^\s+([A-Za-z0-9_.-]+\.dll)\s*$') {
                            $Matches[1].ToUpperInvariant()
                        }
                    } |
                    Where-Object { $null -ne $_ } |
                    Sort-Object -Unique)
            if ($imports.Count -eq 0) {
                throw 'DUMPBIN reported no imported DLLs.'
            }
            $unexpectedImports = @($imports | Where-Object {
                    $_ -notin @(
                        'KERNEL32.DLL',
                        'UCRTBASE.DLL',
                        'VCRUNTIME140.DLL'
                    ) -and $_ -notlike 'API-MS-WIN-CRT-*.DLL'
                })
            if ($unexpectedImports.Count -gt 0) {
                throw 'Executable imports an unexpected non-system or undeclared DLL.'
            }

            $exportStdout = Join-Path $logRoot 'dumpbin-exports.stdout.raw.log'
            $exportStderr = Join-Path $logRoot 'dumpbin-exports.stderr.raw.log'
            $exportInspection = Invoke-CapturedProcess -Executable $toolchain.Dumpbin `
                -Arguments @('/EXPORTS', $executable) -WorkingDirectory $buildRoot `
                -Environment $environment -StdoutPath $exportStdout `
                -StderrPath $exportStderr -TimeoutSeconds 60
            if ($exportInspection.TimedOut -or $exportInspection.ExitCode -ne 0) {
                throw 'DUMPBIN export inspection failed.'
            }
            $exports = @($exportInspection.Stdout -split "`r?`n" |
                    ForEach-Object {
                        if ($_ -match '^\s+\d+\s+[0-9A-Fa-f]+\s+[0-9A-Fa-f]+\s+(\S+)\s*$') {
                            $Matches[1]
                        }
                    } |
                    Where-Object { $null -ne $_ } |
                    Sort-Object -Unique)

            $smokeRoot = Join-Path $buildRoot 'smoke'
            [void](New-Item -ItemType Directory -Path $smokeRoot)
            $smokeInput = Join-Path $smokeRoot 'input.nec'
            Copy-Item -LiteralPath (
                Join-Path $repositoryRoot 'tests\smoke\minimal-dipole.nec'
            ) -Destination $smokeInput
            $smokeInputHashBefore = Get-Sha256 -LiteralPath $smokeInput
            [System.IO.File]::WriteAllText(
                (Join-Path $smokeRoot 'malformed.nec'),
                "ZZ`n",
                $script:Utf8NoBom
            )
            $smoke = @(
                Invoke-SmokeCase -Name 'no-arguments' -Executable $executable `
                    -Arguments @() -WorkingDirectory $smokeRoot `
                    -Environment $environment -LogDirectory $logRoot
                Invoke-SmokeCase -Name 'missing-input' -Executable $executable `
                    -Arguments @('-imissing.nec', '-omissing.out') `
                    -WorkingDirectory $smokeRoot -Environment $environment `
                    -LogDirectory $logRoot -OutputName 'missing.out'
                Invoke-SmokeCase -Name 'malformed-input' -Executable $executable `
                    -Arguments @('-imalformed.nec', '-omalformed.out') `
                    -WorkingDirectory $smokeRoot -Environment $environment `
                    -LogDirectory $logRoot -OutputName 'malformed.out'
                Invoke-SmokeCase -Name 'valid-run-1' -Executable $executable `
                    -Arguments @('-iinput.nec', '-ovalid-1.out') `
                    -WorkingDirectory $smokeRoot -Environment $environment `
                    -LogDirectory $logRoot -OutputName 'valid-1.out'
                Invoke-SmokeCase -Name 'valid-run-2' -Executable $executable `
                    -Arguments @('-iinput.nec', '-ovalid-2.out') `
                    -WorkingDirectory $smokeRoot -Environment $environment `
                    -LogDirectory $logRoot -OutputName 'valid-2.out'
            )
            if ($smoke | Where-Object { $_.TimedOut }) {
                throw 'One or more smoke cases exceeded the bounded timeout.'
            }
            if (
                $smoke[0].ExitCode -ne -1 -or
                $smoke[0].OutputCreated -or
                $smoke[1].ExitCode -ne -1 -or
                $smoke[1].OutputCreated -or
                $smoke[2].ExitCode -ne -1 -or
                -not $smoke[2].OutputCreated -or
                $smoke[2].OutputBytes -le 0 -or
                $smoke[3].ExitCode -ne 0 -or
                -not $smoke[3].OutputCreated -or
                $smoke[3].OutputBytes -le 0 -or
                $smoke[4].ExitCode -ne 0 -or
                -not $smoke[4].OutputCreated -or
                $smoke[4].OutputBytes -le 0
            ) {
                throw 'Smoke behavior differs from the preserved CLI contract.'
            }
            $smokeRepeatability = (
                $smoke[3].OutputBytes -eq $smoke[4].OutputBytes -and
                $smoke[3].OutputSha256 -eq $smoke[4].OutputSha256
            )
            if (-not $smokeRepeatability) {
                throw 'Repeated minimal-dipole reports are not byte-identical.'
            }
            $smokeInputHashAfter = Get-Sha256 -LiteralPath $smokeInput
            if ($smokeInputHashAfter -ne $smokeInputHashBefore) {
                throw 'Smoke execution changed the immutable input deck.'
            }
            $smokeInventory = @(
                Get-ChildItem -LiteralPath $smokeRoot -File |
                    Sort-Object -Property Name |
                    ForEach-Object { $_.Name }
            )
            $expectedSmokeInventory = @(
                'input.nec',
                'malformed.nec',
                'malformed.out',
                'valid-1.out',
                'valid-2.out'
            )
            if (Compare-Object -ReferenceObject $expectedSmokeInventory `
                    -DifferenceObject $smokeInventory) {
                throw 'Smoke execution created an unexpected file inventory.'
            }
            $attempt.Executable = [ordered]@{
                Pe = $peFacts
                ImportedDlls = $imports
                ExportedSymbols = $exports
                DumpbinHeadersImportsSha256 = Get-Sha256 -LiteralPath $inspectStdout
                DumpbinExportsSha256 = Get-Sha256 -LiteralPath $exportStdout
                ForbiddenIdentityScan = 'pass'
                PdbPathScan = 'pass'
            }
            $attempt.Smoke = [ordered]@{
                Cases = $smoke
                InputUnchanged = $true
                RepeatabilityEqual = $true
            }
            $attempt.Outcome = 'succeeded'
            $attempt.FailingStage = $null
            $exitCode = 0
        }
    }
}
catch {
    if ($attempt.Outcome -ne 'unmodified_source_build_failed') {
        $attempt.Outcome = 'validation_failed'
        $attempt.FailingStage = 'build_driver'
        $attempt.DriverError = $_.Exception.Message
        $exitCode = 20
    }
}
finally {
    try {
        if (Test-Path -LiteralPath $sourceRoot -PathType Container) {
            Invoke-SourceGuard -Operation verify -RepositoryRoot $repositoryRoot `
                -SourceRoot $sourceRoot
            $attempt.SourceAuthenticationAfterBuild = $true
        }
    }
    catch {
        $attempt.Outcome = 'validation_failed'
        $attempt.FailingStage = 'post_build_source_authentication'
        $attempt.PostBuildErrors = @($attempt.PostBuildErrors) + @(
            $_.Exception.Message
        )
        $exitCode = 20
    }
    try {
        Invoke-PreservationVerifier -RepositoryRoot $repositoryRoot
        $attempt.PreservationAfterBuild = $true
    }
    catch {
        $attempt.Outcome = 'validation_failed'
        $attempt.FailingStage = 'post_build_preservation'
        $attempt.PostBuildErrors = @($attempt.PostBuildErrors) + @(
            $_.Exception.Message
        )
        $exitCode = 20
    }

    $attemptStopwatch.Stop()
    $attempt.DurationMilliseconds = $attemptStopwatch.ElapsedMilliseconds
    $attemptRecord = Join-Path $attemptOutput 'attempt-result.json'
    $attemptJson = $attempt | ConvertTo-Json -Depth 12
    [System.IO.File]::WriteAllText(
        $attemptRecord,
        ($attemptJson + "`n"),
        $script:Utf8NoBom
    )
    Write-Output "A2 attempt outcome: $($attempt.Outcome)"
    Write-Output "A2 attempt stage: $($attempt.FailingStage)"
    Write-Output "A2 attempt record: .build-output/$BuildId/attempt-result.json"
}

exit $exitCode
