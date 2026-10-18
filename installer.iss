#ifndef MyAppVersion
  #define MyAppVersion "2.1.1"
#endif
#define MyAppName "UYAP Evrak Asistanı"
#define MyAppExe "UYAP_Evrak_Asistani.exe"
#define MyPublisher "Alperen İVAK"
#define MyURL "https://github.com/alperenivak/uyap-evrak-asistani"

[Setup]
AppId={{A0D06691-339F-4BEB-943C-9060985D544B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyPublisher}
AppPublisherURL=https://github.com/alperenivak
AppSupportURL={#MyURL}/issues
AppUpdatesURL={#MyURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Yönetici yetkisi gerekmez: varsayılan olarak kullanıcıya özel kurulur (ofis bilgisayarlarında sorunsuz).
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist
OutputBaseFilename=UYAP_Evrak_Asistani_Kurulum
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\{#MyAppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyPublisher}
VersionInfoDescription={#MyAppName} Kurulum
VersionInfoCopyright=© 2026 Alperen İVAK

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek simgeler:"

[Files]
Source: "dist\{#MyAppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
