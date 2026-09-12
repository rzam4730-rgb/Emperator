#define MyAppName "امپراتور V2"
#define MyAppVersion "2.0.0"
#define MyAppExeName "Emperator.exe"
[Setup]
AppId={{A7B9F22E-3C91-4D6B-8F11-2026EMPV2}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\EmperatorV2
DefaultGroupName={#MyAppName}
OutputBaseFilename=EmperatorSetup-V2-DarkUI
Compression=lzma
SolidCompression=yes
[Files]
Source: "..\dist\Emperator\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "اجرای امپراتور V2"; Flags: nowait postinstall skipifsilent