; Instalador de WinGet Expert (Inno Setup, en español).
; Compilar (tras generar dist\WinGet_Expert_v<version>.exe con PyInstaller):
;   "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" instalador.iss
; Produce dist\WinGet_Expert_Instalador_v<version>.exe

#define NombreApp "WinGet Expert"
#define VersionApp "3.0"
#define Autor "Diego A. Rábalo"
#define URLRepo "https://github.com/mikear/Winget-Expert"

[Setup]
AppId={{8E1F4B7C-9C2A-4E6D-B3F0-WINGETEXPERT}
AppName={#NombreApp}
AppVersion={#VersionApp}
AppVerName={#NombreApp} {#VersionApp}
AppPublisher={#Autor}
AppPublisherURL={#URLRepo}
AppSupportURL={#URLRepo}/issues
DefaultDirName={autopf}\{#NombreApp}
DefaultGroupName={#NombreApp}
UninstallDisplayName={#NombreApp}
UninstallDisplayIcon={app}\WinGet_Expert.exe
OutputDir=dist
OutputBaseFilename=WinGet_Expert_Instalador_v{#VersionApp}
SetupIconFile=assets\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
LicenseFile=LICENSE

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "iconoescritorio"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"
Name: "iniciarmenu"; Description: "Crear acceso en el menú Inicio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Files]
; El binario distribuido lleva la versión en el nombre; instalado queda fijo
; para que los accesos directos sobrevivan a actualizaciones.
Source: "dist\WinGet_Expert_v{#VersionApp}.exe"; DestDir: "{app}"; DestName: "WinGet_Expert.exe"; Flags: ignoreversion

[Icons]
Name: "{group}\{#NombreApp}"; Filename: "{app}\WinGet_Expert.exe"; Tasks: iniciarmenu
Name: "{group}\Desinstalar {#NombreApp}"; Filename: "{uninstallexe}"; Tasks: iniciarmenu
Name: "{autodesktop}\{#NombreApp}"; Filename: "{app}\WinGet_Expert.exe"; Tasks: iconoescritorio

[Run]
Filename: "{app}\WinGet_Expert.exe"; Description: "Iniciar {#NombreApp}"; Flags: nowait postinstall skipifsilent

[Messages]
WelcomeLabel2=Este asistente instalará [name/ver] en su equipo.%n%nSe recomienda cerrar las demás aplicaciones antes de continuar.
