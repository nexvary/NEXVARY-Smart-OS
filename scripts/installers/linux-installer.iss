[Setup]
AppId=NEXVARY.SmartLinuxInstaller
AppName=Smart Linux Installer
AppVersion=0.2.0
AppPublisher=NEXVARY
SetupIconFile=..\..\ui\assets\smart-linux-installer.ico
AppPublisherURL=https://nexvary.com
DefaultDirName={localappdata}\Programs\NEXVARY\SmartLinuxInstaller
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist\setup
OutputBaseFilename=SmartLinuxInstaller-0.2.0-Setup
Compression=lzma2
SolidCompression=yes
[Files]
Source: "..\..\dist\SmartLinuxInstaller\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{userprograms}\Smart Linux Installer"; Filename: "{app}\SmartLinuxInstaller.exe"
[Run]
Filename: "{app}\SmartLinuxInstaller.exe"; Description: "Open Smart Linux Installer"; Flags: nowait postinstall skipifsilent
