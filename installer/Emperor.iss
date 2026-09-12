#define MyAppName "امپراتور"
#define MyAppVersion "1.0.0"
#define MyAppExeName "Emperator.exe"
[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\Emperator
DefaultGroupName={#MyAppName}
OutputBaseFilename=EmperatorSetup
Compression=lzma
SolidCompression=yes
[Files]
Source: "..\dist\Emperator\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "اجرای امپراتور"; Flags: nowait postinstall skipifsilent