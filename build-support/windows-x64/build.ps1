# SPDX-License-Identifier: BSD-2-Clause

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$BuildId
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 3.0

$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$script:ExpectedVisualStudioInstallationVersion = '16.11.36128.20'
$script:ExpectedVisualStudioProductVersion = '16.11.48'
$script:ExpectedVisualStudioProductId = 'Microsoft.VisualStudio.Product.BuildTools'
$script:ExpectedVcToolsVersion = '14.29.30133'
$script:ExpectedWindowsSdkVersion = '10.0.19041.0'
$script:ExpectedCompilerVersion = '19.29.30159.0'
$script:ExpectedLinkerVersion = '14.29.30159.0'
$script:ExpectedDumpbinVersion = '14.29.30159.0'
$script:ExpectedA2NormalizedStdoutBytes = 1694
$script:ExpectedA2NormalizedStdoutSha256 = (
    '3ac5a36f556c88b7f538d1e4ef899b34b44bf00c82e774dd4530ac169223ab91'
)
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

function Get-NumericFileVersion {
    param(
        [Parameter(Mandatory)]
        [string]$LiteralPath
    )

    $version = (Get-Item -LiteralPath $LiteralPath -Force).VersionInfo
    return '{0}.{1}.{2}.{3}' -f @(
        $version.FileMajorPart,
        $version.FileMinorPart,
        $version.FileBuildPart,
        $version.FilePrivatePart
    )
}

function Assert-DriverRuntime {
    if (
        $PSVersionTable.PSEdition -ne 'Desktop' -or
        -not [Environment]::Is64BitProcess -or
        $env:OS -ne 'Windows_NT'
    ) {
        throw 'The A2 driver requires 64-bit Windows PowerShell Desktop.'
    }
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

function Stop-ProcessTree {
    param(
        [Parameter(Mandatory)]
        [System.Diagnostics.Process]$Process,

        [int]$TimeoutMilliseconds = 10000
    )

    if ($Process.HasExited) {
        return
    }

    $systemRoot = $env:SystemRoot
    if ([string]::IsNullOrWhiteSpace($systemRoot)) {
        throw 'SystemRoot is unavailable for bounded process-tree termination.'
    }
    $taskkillPath = Join-Path $systemRoot 'System32\taskkill.exe'
    Assert-PlainFile -LiteralPath $taskkillPath -Label 'system taskkill'

    $killInfo = New-Object System.Diagnostics.ProcessStartInfo
    $killInfo.FileName = $taskkillPath
    $killInfo.Arguments = "/PID $($Process.Id) /T /F"
    $killInfo.UseShellExecute = $false
    $killInfo.CreateNoWindow = $true
    $killInfo.RedirectStandardOutput = $true
    $killInfo.RedirectStandardError = $true
    $killProcess = New-Object System.Diagnostics.Process
    $killProcess.StartInfo = $killInfo
    $taskkillFailure = $null
    try {
        if ($killProcess.Start()) {
            if (-not $killProcess.WaitForExit($TimeoutMilliseconds)) {
                try {
                    $killProcess.Kill()
                }
                catch {
                    # The bounded failure below remains authoritative.
                }
                throw 'taskkill did not complete within the termination timeout.'
            }
            $taskkillStdout = $killProcess.StandardOutput.ReadToEnd()
            $taskkillStderr = $killProcess.StandardError.ReadToEnd()
            if ($killProcess.ExitCode -ne 0) {
                $taskkillFailure = (
                    "taskkill failed with exit code $($killProcess.ExitCode): " +
                    ($taskkillStdout + $taskkillStderr).Trim()
                )
            }
        }
        else {
            $taskkillFailure = 'taskkill could not start.'
        }
    }
    finally {
        $killProcess.Dispose()
    }

    if (-not $Process.HasExited) {
        try {
            $Process.Kill()
        }
        catch {
            # The bounded wait below determines whether termination succeeded.
        }
    }
    if (-not $Process.WaitForExit($TimeoutMilliseconds)) {
        throw 'Timed-out process tree could not be terminated within the bounded grace period.'
    }
    if (-not [string]::IsNullOrEmpty($taskkillFailure)) {
        throw $taskkillFailure
    }
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

        [AllowNull()]
        [string]$StdoutPath,

        [AllowNull()]
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
    $started = $false
    try {
        $started = $process.Start()
        if (-not $started) {
            throw "Process could not start: $Executable"
        }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        $completed = $process.WaitForExit($TimeoutSeconds * 1000)
        if (-not $completed) {
            Stop-ProcessTree -Process $process
        }
        if (
            -not $stdoutTask.Wait(10000) -or
            -not $stderrTask.Wait(10000)
        ) {
            throw 'Captured process streams did not close within the bounded drain period.'
        }
        $stdout = $stdoutTask.Result
        $stderr = $stderrTask.Result
        $stopwatch.Stop()
        if (-not [string]::IsNullOrEmpty($StdoutPath)) {
            [System.IO.File]::WriteAllText($StdoutPath, $stdout, $script:Utf8NoBom)
        }
        if (-not [string]::IsNullOrEmpty($StderrPath)) {
            [System.IO.File]::WriteAllText($StderrPath, $stderr, $script:Utf8NoBom)
        }
        return [pscustomobject][ordered]@{
            ExitCode = if ($completed) { $process.ExitCode } else { $null }
            TimedOut = -not $completed
            DurationMilliseconds = $stopwatch.ElapsedMilliseconds
            Stdout = $stdout
            Stderr = $stderr
        }
    }
    finally {
        if ($stopwatch.IsRunning) {
            $stopwatch.Stop()
        }
        if ($started -and -not $process.HasExited) {
            try {
                Stop-ProcessTree -Process $process
            }
            catch {
                # The original invocation failure remains authoritative.
            }
        }
        $process.Dispose()
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

function Get-ControlledHelperEnvironment {
    param(
        [Parameter(Mandatory)]
        [string]$TemporaryDirectory
    )

    $systemRoot = $env:SystemRoot
    $comSpec = $env:ComSpec
    if ([string]::IsNullOrWhiteSpace($systemRoot) -or [string]::IsNullOrWhiteSpace($comSpec)) {
        throw 'Required Windows helper environment values are unavailable.'
    }
    if ([string]::IsNullOrWhiteSpace($env:ProgramData)) {
        throw 'ProgramData is unavailable for controlled Visual Studio discovery.'
    }
    return @{
        'ComSpec' = $comSpec
        'LANG' = 'C'
        'LANGUAGE' = 'C'
        'LC_ALL' = 'C'
        'PATH' = "$systemRoot\System32;$systemRoot"
        'PATHEXT' = '.COM;.EXE;.BAT;.CMD'
        'ProgramData' = $env:ProgramData
        'SystemRoot' = $systemRoot
        'TEMP' = $TemporaryDirectory
        'TMP' = $TemporaryDirectory
        'TZ' = 'UTC'
        'VSLANG' = '1033'
        'windir' = $systemRoot
    }
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
    $result = Invoke-CapturedProcess -Executable $python.Executable `
        -Arguments $arguments -WorkingDirectory $RepositoryRoot `
        -Environment (Get-ControlledHelperEnvironment -TemporaryDirectory (
            Join-Path $RepositoryRoot '.build-temp'
        )) -TimeoutSeconds 120
    if (-not [string]::IsNullOrEmpty($result.Stdout)) {
        [Console]::Out.Write($result.Stdout)
    }
    if (-not [string]::IsNullOrEmpty($result.Stderr)) {
        [Console]::Error.Write($result.Stderr)
    }
    if ($result.TimedOut) {
        throw "Source guard timed out during $Operation."
    }
    if ($result.ExitCode -ne 0) {
        throw "Source guard failed during $Operation with exit code $($result.ExitCode)."
    }
}

function Invoke-PreservationVerifier {
    param(
        [Parameter(Mandatory)]
        [string]$RepositoryRoot
    )

    $verifier = Join-Path $RepositoryRoot 'verify-preservation.ps1'
    $windowsPowerShell = Join-Path $PSHOME 'powershell.exe'
    Assert-PlainFile -LiteralPath $windowsPowerShell -Label 'Windows PowerShell'
    $result = Invoke-CapturedProcess -Executable $windowsPowerShell -Arguments @(
        '-NoLogo',
        '-NoProfile',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        $verifier,
        '-RepositoryRoot',
        $RepositoryRoot
    ) -WorkingDirectory $RepositoryRoot `
        -Environment (Get-ControlledHelperEnvironment -TemporaryDirectory (
            Join-Path $RepositoryRoot '.build-temp'
        )) -TimeoutSeconds 120
    if (-not [string]::IsNullOrEmpty($result.Stdout)) {
        [Console]::Out.Write($result.Stdout)
    }
    if (-not [string]::IsNullOrEmpty($result.Stderr)) {
        [Console]::Error.Write($result.Stderr)
    }
    if ($result.TimedOut) {
        throw 'Preservation verifier timed out.'
    }
    if ($result.ExitCode -ne 0) {
        throw "Preservation verifier failed with exit code $($result.ExitCode)."
    }
}

function Get-MsvcToolchain {
    param(
        [Parameter(Mandatory)]
        [string]$TemporaryDirectory
    )

    $programFilesX86 = ${env:ProgramFiles(x86)}
    if ([string]::IsNullOrWhiteSpace($programFilesX86)) {
        throw 'ProgramFiles(x86) is unavailable.'
    }
    $vswhere = Join-Path $programFilesX86 'Microsoft Visual Studio\Installer\vswhere.exe'
    Assert-PlainFile -LiteralPath $vswhere -Label 'Visual Studio locator'
    $vswhereResult = Invoke-CapturedProcess -Executable $vswhere -Arguments @(
        '-all',
        '-products',
        '*',
        '-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
        '-format',
        'json',
        '-utf8'
    ) -WorkingDirectory $programFilesX86 `
        -Environment (Get-ControlledHelperEnvironment -TemporaryDirectory $TemporaryDirectory) `
        -TimeoutSeconds 30
    if ($vswhereResult.TimedOut -or $vswhereResult.ExitCode -ne 0) {
        throw 'Visual Studio locator failed.'
    }
    try {
        $parsedInstallations = $vswhereResult.Stdout | ConvertFrom-Json
        $installations = @()
        foreach ($parsedInstallation in $parsedInstallations) {
            $installations += $parsedInstallation
        }
    }
    catch {
        throw 'Visual Studio locator returned invalid JSON.'
    }
    $matches = @($installations | Where-Object {
            $_.installationVersion -eq $script:ExpectedVisualStudioInstallationVersion -and
            $_.productId -eq $script:ExpectedVisualStudioProductId
        })
    if ($matches.Count -ne 1) {
        throw (
            'The pinned Visual Studio Build Tools installation is unavailable or ambiguous: ' +
            $script:ExpectedVisualStudioInstallationVersion
        )
    }
    $installation = $matches[0]
    $installationRoot = [string]$installation.installationPath
    Assert-PlainDirectory -LiteralPath $installationRoot -Label 'Visual Studio installation'
    $productVersion = [string]$installation.catalog.productDisplayVersion
    if ($productVersion -ne $script:ExpectedVisualStudioProductVersion) {
        throw 'The pinned Visual Studio product version does not match.'
    }

    $vcToolsRoot = Join-Path (
        Join-Path $installationRoot 'VC\Tools\MSVC'
    ) $script:ExpectedVcToolsVersion
    Assert-PlainDirectory -LiteralPath $vcToolsRoot -Label 'pinned Visual C++ toolset'
    $binaryRoot = Join-Path $vcToolsRoot 'bin\Hostx64\x64'
    Assert-PlainDirectory -LiteralPath $binaryRoot -Label 'pinned Visual C++ x64 tools'
    $cl = Join-Path $binaryRoot 'cl.exe'
    $link = Join-Path $binaryRoot 'link.exe'
    $dumpbin = Join-Path $binaryRoot 'dumpbin.exe'
    Assert-PlainFile -LiteralPath $cl -Label 'pinned x64 C compiler'
    $compilerVersion = Get-NumericFileVersion -LiteralPath $cl
    if ($compilerVersion -ne $script:ExpectedCompilerVersion) {
        throw 'The pinned x64 C compiler version does not match.'
    }

    $sdkRoot = Join-Path $programFilesX86 'Windows Kits\10'
    $sdkVersion = $script:ExpectedWindowsSdkVersion
    $sdkVersionRoot = Join-Path (Join-Path $sdkRoot 'Include') $sdkVersion
    $sdkLibRoot = Join-Path (Join-Path $sdkRoot 'Lib') $sdkVersion
    foreach ($required in @(
            (Join-Path $vcToolsRoot 'include'),
            (Join-Path $sdkVersionRoot 'ucrt'),
            (Join-Path $sdkVersionRoot 'shared'),
            (Join-Path $sdkVersionRoot 'um'),
            (Join-Path $sdkVersionRoot 'winrt')
        )) {
        Assert-PlainDirectory -LiteralPath $required -Label 'pinned compiler include directory'
    }

    return [pscustomobject][ordered]@{
        InstallationRoot = $installationRoot
        VisualStudioInstallationVersion = [string]$installation.installationVersion
        VisualStudioProductId = [string]$installation.productId
        VisualStudioProductVersion = $productVersion
        VcToolsRoot = $vcToolsRoot
        VcToolsVersion = $script:ExpectedVcToolsVersion
        SdkRoot = $sdkRoot
        SdkVersion = $sdkVersion
        Cl = $cl
        Link = $link
        Dumpbin = $dumpbin
        CompilerVersion = $compilerVersion
        CompilerBytes = (Get-Item -LiteralPath $cl -Force).Length
        CompilerSha256 = Get-Sha256 -LiteralPath $cl
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

function Assert-LinkToolchain {
    param(
        [Parameter(Mandatory)]
        [pscustomobject]$Toolchain
    )

    Assert-PlainFile -LiteralPath $Toolchain.Link -Label 'pinned x64 linker'
    if (
        (Get-NumericFileVersion -LiteralPath $Toolchain.Link) -ne
        $script:ExpectedLinkerVersion
    ) {
        throw 'The pinned x64 linker version does not match.'
    }
    foreach ($required in @(
            (Join-Path $Toolchain.VcToolsRoot 'lib\x64'),
            (Join-Path (Join-Path $Toolchain.SdkRoot 'Lib') (
                Join-Path $Toolchain.SdkVersion 'ucrt\x64'
            )),
            (Join-Path (Join-Path $Toolchain.SdkRoot 'Lib') (
                Join-Path $Toolchain.SdkVersion 'um\x64'
            ))
        )) {
        Assert-PlainDirectory -LiteralPath $required -Label 'pinned linker library directory'
    }
    return [pscustomobject][ordered]@{
        LinkerVersion = Get-NumericFileVersion -LiteralPath $Toolchain.Link
        LinkerBytes = (Get-Item -LiteralPath $Toolchain.Link -Force).Length
        LinkerSha256 = Get-Sha256 -LiteralPath $Toolchain.Link
    }
}

function Assert-DumpbinTool {
    param(
        [Parameter(Mandatory)]
        [pscustomobject]$Toolchain
    )

    Assert-PlainFile -LiteralPath $Toolchain.Dumpbin -Label 'pinned PE inspector'
    if (
        (Get-NumericFileVersion -LiteralPath $Toolchain.Dumpbin) -ne
        $script:ExpectedDumpbinVersion
    ) {
        throw 'The pinned PE inspector version does not match.'
    }
    return [pscustomobject][ordered]@{
        DumpbinVersion = Get-NumericFileVersion -LiteralPath $Toolchain.Dumpbin
        DumpbinBytes = (Get-Item -LiteralPath $Toolchain.Dumpbin -Force).Length
        DumpbinSha256 = Get-Sha256 -LiteralPath $Toolchain.Dumpbin
    }
}

function Get-ControlledEnvironment {
    param(
        [Parameter(Mandatory)]
        [pscustomobject]$Toolchain,

        [Parameter(Mandatory)]
        [string]$TemporaryDirectory,

        [switch]$ForLink
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
        'LIB' = if ($ForLink) { $Toolchain.Lib } else { '' }
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

function Get-DiagnosticReplacementMap {
    param(
        [Parameter(Mandatory)]
        [string]$RepositoryRoot,

        [Parameter(Mandatory)]
        [string]$AttemptRoot,

        [AllowNull()]
        [pscustomobject]$Toolchain
    )

    $replacements = @{}
    $replacements[$AttemptRoot] = '${ATTEMPT_ROOT}'
    $replacements[$RepositoryRoot] = '${REPOSITORY_ROOT}'
    if ($null -ne $Toolchain) {
        $replacements[$Toolchain.InstallationRoot] = '${VISUAL_STUDIO_ROOT}'
        $replacements[$Toolchain.SdkRoot] = '${WINDOWS_SDK_ROOT}'
    }
    if (-not [string]::IsNullOrWhiteSpace(${env:ProgramFiles(x86)})) {
        $replacements[${env:ProgramFiles(x86)}] = '${PROGRAM_FILES_X86}'
    }
    if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        $replacements[$env:USERPROFILE] = '${USER_PROFILE}'
    }
    if (-not [string]::IsNullOrWhiteSpace($env:SystemRoot)) {
        $replacements[$env:SystemRoot] = '${SYSTEM_ROOT}'
    }
    return $replacements
}

function Replace-OrdinalPath {
    param(
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string]$Text,

        [Parameter(Mandatory)]
        [string]$OldValue,

        [Parameter(Mandatory)]
        [string]$NewValue
    )

    $pattern = [regex]::Escape($OldValue)
    $evaluator = [System.Text.RegularExpressions.MatchEvaluator] {
        param($match)
        return $NewValue
    }
    return [regex]::Replace(
        $Text,
        $pattern,
        $evaluator,
        (
            [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor
            [System.Text.RegularExpressions.RegexOptions]::CultureInvariant
        )
    )
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
            $replacement = [string]$ReplacementMap[$key]
            $normalized = Replace-OrdinalPath -Text $normalized -OldValue $key `
                -NewValue $replacement
            $forwardPath = $key.Replace('\', '/')
            if ($forwardPath -ne $key) {
                $normalized = Replace-OrdinalPath -Text $normalized `
                    -OldValue $forwardPath -NewValue $replacement
            }
        }
    }
    return $normalized
}

function Get-BuildProductInventory {
    param(
        [Parameter(Mandatory)]
        [string]$BuildRoot,

        [Parameter(Mandatory)]
        [string]$TemporaryDirectory
    )

    return @(
        Get-ChildItem -LiteralPath $BuildRoot -Recurse -Force -File |
            Where-Object {
                -not $_.FullName.StartsWith(
                    ($TemporaryDirectory.TrimEnd('\') + '\'),
                    [StringComparison]::OrdinalIgnoreCase
                )
            } |
            Sort-Object -Property FullName |
            ForEach-Object {
                [pscustomobject][ordered]@{
                    Path = $_.FullName.Substring($BuildRoot.Length + 1).Replace('\', '/')
                    ByteCount = $_.Length
                    Sha256 = Get-Sha256 -LiteralPath $_.FullName
                }
            }
    )
}

function Get-ExpectedA2NormalizedStdout {
    $diagnostic = (
        '${ATTEMPT_ROOT}\source\nec2c-1.3.1\nec2c.h(9): fatal error C1083: ' +
        "Cannot open include file: 'unistd.h': No such file or directory"
    )
    $lines = @()
    foreach ($sourceName in $script:SourceNames) {
        $lines += $sourceName
        $lines += $diagnostic
    }
    $lines += 'Generating Code...'
    return (($lines -join "`n") + "`n")
}

function Get-BuildDefinitionIdentity {
    param(
        [Parameter(Mandatory)]
        [string]$RepositoryRoot
    )

    $driverPath = $PSCommandPath
    $sourceGuardPath = Join-Path $PSScriptRoot 'source_guard.py'
    return [pscustomobject][ordered]@{
        BuildDriverBytes = (Get-Item -LiteralPath $driverPath -Force).Length
        BuildDriverSha256 = Get-Sha256 -LiteralPath $driverPath
        SourceGuardBytes = (Get-Item -LiteralPath $sourceGuardPath -Force).Length
        SourceGuardSha256 = Get-Sha256 -LiteralPath $sourceGuardPath
    }
}

function Assert-BuildDefinitionIdentity {
    param(
        [Parameter(Mandatory)]
        [string]$RepositoryRoot,

        [Parameter(Mandatory)]
        [pscustomobject]$Identity
    )

    $manifestPath = Join-Path $RepositoryRoot (
        'manifests\windows-x64-unmodified-build-v1.json'
    )
    Assert-PlainFile -LiteralPath $manifestPath -Label 'Windows x64 build manifest'
    try {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 |
            ConvertFrom-Json
    }
    catch {
        throw 'Windows x64 build manifest is invalid JSON.'
    }
    $driver = $manifest.build_definition.build_driver
    $guard = $manifest.build_definition.source_guard
    if (
        [int64]$driver.byte_count -ne $Identity.BuildDriverBytes -or
        [string]$driver.sha256 -ne $Identity.BuildDriverSha256 -or
        [int64]$guard.byte_count -ne $Identity.SourceGuardBytes -or
        [string]$guard.sha256 -ne $Identity.SourceGuardSha256
    ) {
        throw 'Build driver or source guard identity differs from the versioned manifest.'
    }
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
$buildTempRoot = Join-Path $repositoryRoot '.build-temp'
$buildOutputRoot = Join-Path $repositoryRoot '.build-output'
try {
    Assert-DriverRuntime
    Assert-PlainDirectory -LiteralPath $repositoryRoot -Label 'repository root'
    foreach ($root in @($buildTempRoot, $buildOutputRoot)) {
        if (-not (Test-Path -LiteralPath $root)) {
            [void](New-Item -ItemType Directory -Path $root)
        }
        Assert-PlainDirectory -LiteralPath $root -Label (Split-Path -Leaf $root)
    }
    Assert-ValidBuildId -Value $BuildId
    $attemptRoot = Join-Path $buildTempRoot $BuildId
    $attemptOutput = Join-Path $buildOutputRoot $BuildId
    foreach ($freshPath in @($attemptRoot, $attemptOutput)) {
        if (Test-Path -LiteralPath $freshPath) {
            throw "Fresh build path already exists: $(Split-Path -Leaf $freshPath)"
        }
    }
    [void](New-Item -ItemType Directory -Path $attemptOutput)
    try {
        [void](New-Item -ItemType Directory -Path $attemptRoot)
    }
    catch {
        if (
            (Test-Path -LiteralPath $attemptOutput -PathType Container) -and
            @(Get-ChildItem -LiteralPath $attemptOutput -Force).Count -eq 0
        ) {
            Remove-Item -LiteralPath $attemptOutput
        }
        throw
    }
}
catch {
    $setupError = $_.Exception.Message
    try {
        if (Test-Path -LiteralPath $repositoryRoot -PathType Container) {
            Invoke-PreservationVerifier -RepositoryRoot $repositoryRoot
        }
    }
    catch {
        $setupError += "; final preservation check failed: $($_.Exception.Message)"
    }
    [Console]::Error.WriteLine("A2 setup refused: $setupError")
    exit 20
}

$sourceRoot = Join-Path $attemptRoot 'source'
$buildRoot = Join-Path $attemptRoot 'build'
$temporaryRoot = Join-Path $buildRoot 'tmp'
$logRoot = Join-Path $attemptOutput 'logs'

$attemptStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$attempt = [ordered]@{
    Schema = 'org.sutherlandryan.hf-nec2c.windows-x64-local-attempt.v2'
    BuildId = $BuildId
    Outcome = 'validation_failed'
    FailingStage = 'pre_build_validation'
    ExpectedA2BlockerObserved = $false
    SourceAuthenticationBeforeBuild = $false
    SourceAuthenticationAfterBuild = $false
    PreservationBeforeBuild = $false
    PreservationAfterBuild = $false
    BuildDefinition = $null
    Toolchain = $null
    DriverRuntime = [ordered]@{
        PowerShell = (
            "$($PSVersionTable.PSEdition) PowerShell $($PSVersionTable.PSVersion); " +
            '64-bit process'
        )
        Python = $null
    }
    CompileArguments = $null
    CompilerExitCode = $null
    LinkerExitCode = $null
    BuildProductsAfterCompile = @()
    BuildProductsAfterLink = @()
    Executable = $null
    Smoke = $null
    CompileDiagnostics = $null
    LinkDiagnostics = $null
    DriverError = $null
    PostBuildErrors = @()
    DurationMilliseconds = $null
    DriverExitCode = $null
}
$exitCode = 20
$toolchain = $null

try {
    foreach ($directory in @($buildRoot, $temporaryRoot, $logRoot)) {
        [void](New-Item -ItemType Directory -Path $directory)
        Assert-PlainDirectory -LiteralPath $directory -Label (
            Split-Path -Leaf $directory
        )
    }
    Invoke-PreservationVerifier -RepositoryRoot $repositoryRoot
    $attempt.PreservationBeforeBuild = $true
    $buildDefinition = Get-BuildDefinitionIdentity -RepositoryRoot $repositoryRoot
    Assert-BuildDefinitionIdentity -RepositoryRoot $repositoryRoot `
        -Identity $buildDefinition
    $attempt.BuildDefinition = $buildDefinition

    $python = Get-PythonInvocation
    $pythonVersion = Invoke-CapturedProcess -Executable $python.Executable `
        -Arguments (@($python.Prefix) + @('--version')) `
        -WorkingDirectory $repositoryRoot `
        -Environment (Get-ControlledHelperEnvironment -TemporaryDirectory $temporaryRoot) `
        -TimeoutSeconds 30
    if ($pythonVersion.TimedOut -or $pythonVersion.ExitCode -ne 0) {
        throw 'Python runtime identity probe failed.'
    }
    $pythonVersionText = (
        $pythonVersion.Stdout + $pythonVersion.Stderr
    ).Trim()
    $attempt.DriverRuntime.Python = (
        "$pythonVersionText via $([System.IO.Path]::GetFileName($python.Executable)) " +
        ($python.Prefix -join ' ')
    ).Trim()

    Invoke-SourceGuard -Operation extract -RepositoryRoot $repositoryRoot `
        -SourceRoot $sourceRoot
    Invoke-SourceGuard -Operation verify -RepositoryRoot $repositoryRoot `
        -SourceRoot $sourceRoot
    $attempt.SourceAuthenticationBeforeBuild = $true

    $toolchain = Get-MsvcToolchain -TemporaryDirectory $temporaryRoot
    $attempt.Toolchain = [ordered]@{
        VisualStudioInstallationVersion = $toolchain.VisualStudioInstallationVersion
        VisualStudioProductId = $toolchain.VisualStudioProductId
        VisualStudioProductVersion = $toolchain.VisualStudioProductVersion
        VcToolsVersion = $toolchain.VcToolsVersion
        WindowsSdkVersion = $toolchain.SdkVersion
        CompilerVersion = $toolchain.CompilerVersion
        CompilerBytes = $toolchain.CompilerBytes
        CompilerSha256 = $toolchain.CompilerSha256
        LinkerVersion = $null
        LinkerBytes = $null
        LinkerSha256 = $null
        DumpbinVersion = $null
        DumpbinBytes = $null
        DumpbinSha256 = $null
        HostArchitecture = 'Hostx64'
        TargetArchitecture = 'x64'
    }
    $sourceDirectory = Join-Path $sourceRoot 'nec2c-1.3.1'
    $environment = Get-ControlledEnvironment -Toolchain $toolchain `
        -TemporaryDirectory $temporaryRoot
    if (@(Get-BuildProductInventory -BuildRoot $buildRoot `
                -TemporaryDirectory $temporaryRoot).Count -ne 0) {
        throw 'Fresh build root contains a pre-compile build product.'
    }
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
    $attempt.CompileArguments = $compileArguments
    $compileStdout = Join-Path $logRoot 'compile.stdout.raw.log'
    $compileStderr = Join-Path $logRoot 'compile.stderr.raw.log'
    $compile = Invoke-CapturedProcess -Executable $toolchain.Cl `
        -Arguments $compileArguments -WorkingDirectory $sourceDirectory `
        -Environment $environment -StdoutPath $compileStdout `
        -StderrPath $compileStderr -TimeoutSeconds 300
    $attempt.CompilerExitCode = $compile.ExitCode

    $replacements = Get-DiagnosticReplacementMap -RepositoryRoot $repositoryRoot `
        -AttemptRoot $attemptRoot -Toolchain $toolchain
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
    $buildProductsAfterCompile = @(
        Get-BuildProductInventory -BuildRoot $buildRoot `
            -TemporaryDirectory $temporaryRoot
    )
    $attempt.BuildProductsAfterCompile = $buildProductsAfterCompile
    $attempt.ExpectedA2BlockerObserved = (
        -not $compile.TimedOut -and
        $compile.ExitCode -eq 2 -and
        $normalizedStdout -ceq (Get-ExpectedA2NormalizedStdout) -and
        $attempt.CompileDiagnostics.NormalizedStdoutBytes -eq
        $script:ExpectedA2NormalizedStdoutBytes -and
        $attempt.CompileDiagnostics.NormalizedStdoutSha256 -eq
        $script:ExpectedA2NormalizedStdoutSha256 -and
        $normalizedStderr -ceq '' -and
        $buildProductsAfterCompile.Count -eq 0
    )

    if ($compile.TimedOut) {
        throw 'Compiler timeout is not canonical A2 failure evidence.'
    }
    elseif ($compile.ExitCode -ne 0) {
        $attempt.Outcome = if ($attempt.ExpectedA2BlockerObserved) {
            'unmodified_source_build_failed'
        }
        else {
            'unexpected_unmodified_source_build_failure'
        }
        $attempt.FailingStage = 'compile'
        $exitCode = 10
    }
    else {
        $expectedObjectPaths = @($script:SourceNames | ForEach-Object {
                "$([System.IO.Path]::GetFileNameWithoutExtension($_)).obj"
            })
        $actualObjectPaths = @($buildProductsAfterCompile | ForEach-Object {
                $_.Path
            })
        if (
            $buildProductsAfterCompile.Count -ne $expectedObjectPaths.Count -or
            (Compare-Object -ReferenceObject $expectedObjectPaths `
                    -DifferenceObject $actualObjectPaths)
        ) {
            throw 'Successful compilation did not produce exactly twelve fresh object files.'
        }
        $linkToolchain = Assert-LinkToolchain -Toolchain $toolchain
        $attempt.Toolchain.LinkerVersion = $linkToolchain.LinkerVersion
        $attempt.Toolchain.LinkerBytes = $linkToolchain.LinkerBytes
        $attempt.Toolchain.LinkerSha256 = $linkToolchain.LinkerSha256
        $environment = Get-ControlledEnvironment -Toolchain $toolchain `
            -TemporaryDirectory $temporaryRoot -ForLink
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
        $attempt.BuildProductsAfterLink = @(
            Get-BuildProductInventory -BuildRoot $buildRoot `
                -TemporaryDirectory $temporaryRoot
        )
        if ($link.TimedOut) {
            throw 'Linker timeout is not canonical build-failure evidence.'
        }
        elseif ($link.ExitCode -ne 0) {
            $attempt.Outcome = 'unmodified_source_build_failed'
            $attempt.FailingStage = 'link'
            $exitCode = 10
        }
        else {
            $dumpbinTool = Assert-DumpbinTool -Toolchain $toolchain
            $attempt.Toolchain.DumpbinVersion = $dumpbinTool.DumpbinVersion
            $attempt.Toolchain.DumpbinBytes = $dumpbinTool.DumpbinBytes
            $attempt.Toolchain.DumpbinSha256 = $dumpbinTool.DumpbinSha256
            $executable = Join-Path $buildRoot 'nec2c.exe'
            $peFacts = Get-PeFacts -ExecutablePath $executable
            $binaryBytes = [System.IO.File]::ReadAllBytes($executable)
            $ascii = [System.Text.Encoding]::ASCII.GetString($binaryBytes)
            $unicode = [System.Text.Encoding]::Unicode.GetString($binaryBytes)
            foreach ($forbidden in @(
                    $repositoryRoot,
                    $attemptRoot,
                    $env:USERPROFILE
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
    if (
        $attempt.Outcome -notin @(
            'unmodified_source_build_failed',
            'unexpected_unmodified_source_build_failure'
        )
    ) {
        $attempt.Outcome = 'validation_failed'
        $attempt.FailingStage = 'build_driver'
        $attempt.DriverError = Normalize-Diagnostics -Text $_.Exception.Message `
            -ReplacementMap (Get-DiagnosticReplacementMap `
                -RepositoryRoot $repositoryRoot -AttemptRoot $attemptRoot `
                -Toolchain $toolchain)
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
            (Normalize-Diagnostics -Text $_.Exception.Message `
                -ReplacementMap (Get-DiagnosticReplacementMap `
                    -RepositoryRoot $repositoryRoot -AttemptRoot $attemptRoot `
                    -Toolchain $toolchain))
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
            (Normalize-Diagnostics -Text $_.Exception.Message `
                -ReplacementMap (Get-DiagnosticReplacementMap `
                    -RepositoryRoot $repositoryRoot -AttemptRoot $attemptRoot `
                    -Toolchain $toolchain))
        )
        $exitCode = 20
    }

    $attemptStopwatch.Stop()
    $attempt.DurationMilliseconds = $attemptStopwatch.ElapsedMilliseconds
    $attempt.DriverExitCode = $exitCode
    $attemptRecord = Join-Path $attemptOutput 'attempt-result.json'
    $attemptRecordTemporary = "$attemptRecord.tmp"
    $attemptRecordWritten = $false
    try {
        if (
            (Test-Path -LiteralPath $attemptRecord) -or
            (Test-Path -LiteralPath $attemptRecordTemporary)
        ) {
            throw 'Fresh attempt-record path unexpectedly already exists.'
        }
        $attemptJson = $attempt | ConvertTo-Json -Depth 12
        [System.IO.File]::WriteAllText(
            $attemptRecordTemporary,
            ($attemptJson + "`n"),
            $script:Utf8NoBom
        )
        Move-Item -LiteralPath $attemptRecordTemporary -Destination $attemptRecord
        $attemptRecordWritten = $true
    }
    catch {
        $exitCode = 20
        if (Test-Path -LiteralPath $attemptRecordTemporary -PathType Leaf) {
            try {
                Remove-Item -LiteralPath $attemptRecordTemporary -Force
            }
            catch {
                # The evidence-write failure remains authoritative.
            }
        }
        [Console]::Error.WriteLine(
            "A2 attempt record could not be written atomically: $($_.Exception.Message)"
        )
    }
    if ($attemptRecordWritten) {
        try {
            Write-Output "A2 attempt outcome: $($attempt.Outcome)"
            Write-Output "A2 attempt stage: $($attempt.FailingStage)"
            Write-Output "A2 attempt record: .build-output/$BuildId/attempt-result.json"
        }
        catch {
            # The written evidence and selected driver exit remain authoritative.
        }
    }
}

exit $exitCode
