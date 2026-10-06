$ErrorActionPreference = 'Stop'
foreach ($Name in @('SmartLinuxInstaller', 'SmartWindowsDriver')) {
    $Setup = Join-Path $PSScriptRoot "..\dist\setup\$Name-0.3.0-Setup.exe"
    $Destination = Join-Path $env:RUNNER_TEMP "SmartOS-Setup-Test\$Name"
    $Arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', "/DIR=`"$Destination`"")
    $Process = Start-Process $Setup -ArgumentList $Arguments -Wait -PassThru
    if ($Process.ExitCode -ne 0) { throw "$Name installation failed with $($Process.ExitCode)" }
    $Executable = Join-Path $Destination "$Name.exe"
    if (!(Test-Path $Executable)) { throw "$Name executable missing after setup" }
    $Process = Start-Process $Executable -ArgumentList '--self-check' -Wait -PassThru
    if ($Process.ExitCode -ne 0) { throw "$Name installed app smoke check failed" }
    if ($Name -eq 'SmartWindowsDriver') {
        $HelperTest = Start-Process $Executable -ArgumentList '--privilege-self-check' -Wait -PassThru
        if ($HelperTest.ExitCode -ne 0) { throw 'Installed privilege helper check failed' }
    }
    $Process = Start-Process (Join-Path $Destination 'unins000.exe') -ArgumentList '/VERYSILENT', '/NORESTART' -Wait -PassThru
    if ($Process.ExitCode -ne 0) { throw "$Name uninstall failed" }
    Write-Host "${Name}: setup install, launch and uninstall passed"
}
