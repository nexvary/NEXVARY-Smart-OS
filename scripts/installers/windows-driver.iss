[Setup]
AppId=NEXVARY.SmartWindowsDriver
AppName=Smart Windows Driver
AppVersion=0.4.0
AppPublisher=NEXVARY
SetupIconFile=..\..\ui\assets\smart-windows-driver.ico
AppPublisherURL=https://nexvary.com
DefaultDirName={localappdata}\Programs\NEXVARY\SmartWindowsDriver
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist\setup
OutputBaseFilename=SmartWindowsDriver-0.4.0-Setup
Compression=lzma2
SolidCompression=yes
[Files]
Source: "..\..\dist\SmartWindowsDriver\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{userprograms}\Smart Windows Driver"; Filename: "{app}\SmartWindowsDriver.exe"
[Run]
Filename: "{app}\SmartWindowsDriver.exe"; Description: "Open Smart Windows Driver"; Flags: nowait postinstall skipifsilent
