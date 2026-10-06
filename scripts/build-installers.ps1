$ErrorActionPreference = 'Stop'
$Compiler = Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'
if (!(Test-Path $Compiler)) { throw 'Inno Setup 6 is required to build the two separate Setup EXEs.' }
& $Compiler "$PSScriptRoot\installers\linux-installer.iss"
if ($LASTEXITCODE -ne 0) { throw 'Linux Installer Setup build failed' }
& $Compiler "$PSScriptRoot\installers\windows-driver.iss"
if ($LASTEXITCODE -ne 0) { throw 'Windows Driver Setup build failed' }
