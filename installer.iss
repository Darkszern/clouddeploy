; =============================================================================
; LXCC Cloud Deploy Tool - Inno Setup Installer Script
; =============================================================================
; Generates a professional installer EXE with:
;   - Welcome screen, license, directory selection
;   - Progress bar during installation
;   - Desktop + Start Menu shortcuts
;   - Full uninstaller (Add/Remove Programs)
;   - Repair / Reinstall / Uninstall support
;
; Build: Run build_installer.bat (builds EXE first, then compiles this)
; Requires: Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
; =============================================================================

#define MyAppName "LXCC Cloud Deploy"
#define MyAppVersion "1.21.0"
#define MyAppPublisher "LXCC"
#define MyAppExeName "DeployTool.exe"
#define MyAppIcon "LXCCLOGO.ico"

[Setup]
; Unique App ID - do NOT change after first release
AppId={{B8F3A2E1-7D4C-4E5A-9F1B-3C6D8E2A4F7B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\LXCC Cloud Deploy
DefaultGroupName={#MyAppName}
; Allow user to choose "no Start Menu group"
AllowNoIcons=yes
; Output installer EXE
OutputDir=dist_installer
OutputBaseFilename=LXCC_CloudDeploy_Setup_v{#MyAppVersion}
; Use the app icon for the installer
SetupIconFile=LXCCLOGO.ico
; Compression
Compression=lzma2/max
SolidCompression=yes
; Modern look
WizardStyle=modern
WizardSizePercent=110
; Require admin for Program Files
PrivilegesRequired=admin
; Uninstall icon
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
; Minimum Windows version
MinVersion=10.0
; Show "install for all users" option
PrivilegesRequiredOverridesAllowed=dialog
; License file (optional - remove if not needed)
; LicenseFile=LICENSE.txt
; Archive format
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[CustomMessages]
english.LaunchApp=Launch %1 now
german.LaunchApp=%1 jetzt starten
english.DesktopIcon=Create a &desktop shortcut
german.DesktopIcon=&Desktop-Verknüpfung erstellen
english.InstallingApp=Installing LXCC Cloud Deploy...
german.InstallingApp=LXCC Cloud Deploy wird installiert...

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce
Name: "startmenuicon"; Description: "Create Start Menu entry"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
; Main application EXE (built by PyInstaller before running this script)
Source: "dist\DeployTool.exe"; DestDir: "{app}"; Flags: ignoreversion
; Application icon
Source: "LXCCLOGO.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Desktop shortcut
Name: "{autodesktop}\DeployTool"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIcon}"; Tasks: desktopicon
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIcon}"; Tasks: startmenuicon
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; Tasks: startmenuicon

[Run]
; Option to launch app after interactive install (user gets checkbox)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchApp,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
; Auto-launch app after silent update (no checkbox needed)
Filename: "{app}\{#MyAppExeName}"; Flags: nowait; Check: WizardSilent

[UninstallDelete]
; Clean up leftover files on uninstall
Type: files; Name: "{app}\LXCCLOGO.ico"
Type: files; Name: "{app}\DeployTool.exe.update"
Type: files; Name: "{app}\_update.bat"
Type: dirifempty; Name: "{app}"
; Config is now stored in %APPDATA%\LXCC Cloud Deploy
Type: files; Name: "{userappdata}\LXCC Cloud Deploy\config.json"
Type: dirifempty; Name: "{userappdata}\LXCC Cloud Deploy"

[Code]
// ==========================================================================
// Pascal Script for custom installer logic
// ==========================================================================

var
  ProgressPage: TOutputProgressWizardPage;
  IsReinstall: Boolean;

// Check if the application is already installed
function IsAppInstalled: Boolean;
begin
  Result := RegKeyExists(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B8F3A2E1-7D4C-4E5A-9F1B-3C6D8E2A4F7B}_is1') or
            RegKeyExists(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B8F3A2E1-7D4C-4E5A-9F1B-3C6D8E2A4F7B}_is1');
end;

// Called when the installer initializes
function InitializeSetup: Boolean;
var
  ResultCode: Integer;
  UninstallString: String;
begin
  Result := True;

  // Check if already installed
  if IsAppInstalled then
  begin
    // In silent/verysilent mode (auto-update), skip the dialog and auto-reinstall
    if WizardSilent then
    begin
      IsReinstall := True;
      Result := True;
      Exit;
    end;

    case MsgBox(
      'LXCC Cloud Deploy is already installed.' + #13#10 + #13#10 +
      'What would you like to do?' + #13#10 + #13#10 +
      'Yes = Reinstall / Update' + #13#10 +
      'No = Uninstall' + #13#10 +
      'Cancel = Exit',
      mbConfirmation, MB_YESNOCANCEL) of

      IDYES:
        begin
          // User wants to reinstall / update
          IsReinstall := True;
          Result := True;
        end;

      IDNO:
        begin
          // User wants to uninstall - run the existing uninstaller
          if RegQueryStringValue(HKLM,
            'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B8F3A2E1-7D4C-4E5A-9F1B-3C6D8E2A4F7B}_is1',
            'UninstallString', UninstallString) then
          begin
            Exec(RemoveQuotes(UninstallString), '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
          end
          else if RegQueryStringValue(HKCU,
            'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B8F3A2E1-7D4C-4E5A-9F1B-3C6D8E2A4F7B}_is1',
            'UninstallString', UninstallString) then
          begin
            Exec(RemoveQuotes(UninstallString), '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
          end;
          MsgBox('LXCC Cloud Deploy has been uninstalled.', mbInformation, MB_OK);
          Result := False; // Don't continue with installation
        end;

      IDCANCEL:
        begin
          Result := False; // User cancelled
        end;
    end;
  end;
end;

// Add a custom progress page
procedure InitializeWizard;
begin
  ProgressPage := CreateOutputProgressPage(
    'Installing',
    'Please wait while LXCC Cloud Deploy is being installed...'
  );
end;

// Show progress during file extraction
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    ProgressPage.Show;
    try
      ProgressPage.SetText('Preparing installation...', '');
      ProgressPage.SetProgress(0, 100);
      Sleep(300);

      ProgressPage.SetText('Copying DeployTool.exe...', 'Main application');
      ProgressPage.SetProgress(20, 100);
      Sleep(500);

      ProgressPage.SetText('Copying icon files...', 'LXCCLOGO.ico');
      ProgressPage.SetProgress(50, 100);
      Sleep(300);

      ProgressPage.SetText('Creating shortcuts...', 'Desktop and Start Menu');
      ProgressPage.SetProgress(70, 100);
      Sleep(300);

      ProgressPage.SetText('Registering application...', 'Add/Remove Programs');
      ProgressPage.SetProgress(90, 100);
      Sleep(300);

      ProgressPage.SetText('Installation complete!', '');
      ProgressPage.SetProgress(100, 100);
      Sleep(500);
    finally
      ProgressPage.Hide;
    end;
  end;
end;

// Custom uninstall: ask if config should be kept
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ConfigPath: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    ConfigPath := ExpandConstant('{userappdata}\LXCC Cloud Deploy\config.json');
    if FileExists(ConfigPath) then
    begin
      if MsgBox(
        'Do you want to keep your configuration (server IP and password)?' + #13#10 +
        'Click Yes to keep, No to delete.',
        mbConfirmation, MB_YESNO) = IDNO then
      begin
        DeleteFile(ConfigPath);
      end;
    end;
  end;
end;

var
  UninstallString: String;
