; Inno Setup script — Befund-Automat Setup.exe (per-user, no admin).
; Mirrors offerten-generator/installer/juglans.iss.
;
; Build: Inno Setup 6 on the Windows build machine, after PyInstaller:
;   iscc befund.iss
; Input:  ..\dist\BefundAutomat\   (PyInstaller onedir output)
; Output: BefundAutomat-Setup.exe
;
; Design decisions (see decisions/log.md):
;   - PrivilegesRequired=lowest + {localappdata} install dir: no admin needed,
;     works on a locked-down practice PC.
;   - {userstartup} shortcut IS the autostart mechanism (tray app in the
;     interactive session; toast + clipboard need it).
;   - CloseApplications=yes so an update-Setup.exe can replace a running app.
;   - State/config/logs live in {localappdata}\BefundAutomat (config.data_dir()),
;     NOT under {app} -> reinstall = update, state preserved.

[Setup]
AppName=Befund-Automat
AppVersion=0.1.0
AppPublisher=Automatisierbar
DefaultDirName={localappdata}\Programs\BefundAutomat
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=BefundAutomat-Setup
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
ShowLanguageDialog=no

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Files]
Source: "..\dist\BefundAutomat\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{userstartup}\Befund-Automat"; Filename: "{app}\BefundAutomat.exe"
Name: "{userdesktop}\Befund-Automat"; Filename: "{app}\BefundAutomat.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Desktop-Symbol erstellen"; GroupDescription: "Zusätzlich:"

[Run]
Filename: "{app}\BefundAutomat.exe"; Description: "Befund-Automat jetzt starten"; Flags: nowait postinstall skipifsilent
