[Setup]
AppName=CongregationToolsApp
AppVersion=1.0.2
DefaultDirName={pf}\CongregationToolsApp
DefaultGroupName=CongregationToolsApp
PrivilegesRequired=admin 
AllowNoIcons=yes
OutputDir=output
OutputBaseFilename=CongregationToolsAppInstaller
Compression=lzma
SolidCompression=yes

[Files]
; Copia tutti i file generati da PyInstaller
Source: "build\exe.win-amd64-3.12\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Assicurati di includere l'icona
Source: ".\icon.ico"; DestDir: "{app}"
Source: ".\dropbox_icon.png"; DestDir: "{app}"
Source: ".\logout_icon.png"; DestDir: "{app}"
Source: ".\load_data_icon.png"; DestDir: "{app}"

[UninstallDelete]

; Elimina la directory ScreenMonitorApp in AppData (solo se vuota)
Type: dirifempty; Name: "{userappdata}\CongregationToolsApp"

; Elimina la directory ScreenMonitorApp in Program Files (solo se vuota)
Type: dirifempty; Name: "{app}\CongregationToolsApp"

[Icons]
Name: "{group}\CongregationToolsApp"; Filename: "{app}\CongregationToolsApp.exe"; IconFilename: "{app}\icon.ico"
Name: "{userdesktop}\CongregationToolsApp"; Filename: "{app}\CongregationToolsApp.exe"; IconFilename: "{app}\icon.ico"


[Run]
Filename: "{app}\CongregationToolsApp.exe"; Description: "Avvia CongregationToolsApp"; Flags: nowait postinstall skipifsilent

