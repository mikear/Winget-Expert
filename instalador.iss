; Instalador de WinGet Expert (Inno Setup, en español).
; Compilar (tras generar dist\WinGet_Expert_v<version>.exe con PyInstaller):
;   "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" instalador.iss
; Produce dist\WinGet_Expert_Instalador_v<version>.exe
;
; Si ya hay una versión instalada, el asistente muestra una página para
; elegir: actualizar sobre ella, desinstalarla primero o no instalar nada.
; También avisa si la versión instalada es igual o más reciente, y si la
; aplicación está en ejecución.

#define NombreApp "WinGet Expert"
#define VersionApp "3.0"
#define Autor "Diego A. Rábalo"
#define URLRepo "https://github.com/mikear/Winget-Expert"
#define AppId "{8E1F4B7C-9C2A-4E6D-B3F0-WINGETEXPERT}"

[Setup]
AppId={{#AppId}
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
CloseApplications=yes
RestartApplications=no

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

[Code]
// ------------------------------------------------------------------ //
// Detección de versión anterior y página de decisión                 //
// ------------------------------------------------------------------ //

var
  PaginaOpcion: TInputOptionWizardPage;
  VersionAnterior: String;
  DesinstaladorAnterior: String;
  DirAnterior: String;
  RaizAnterior: Integer;
  ClaveAnterior: String;
  CasoAnterior: Integer;
  // 0 = sin versión previa, 1 = actualizar, 2 = misma versión,
  // 3 = instalada más reciente (retroceso)

const
  ClaveDesinstalacion = '{#AppId}_is1';
  SubclaveUninstall = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\';

function ExtraerRuta(const S: String): String;
// Toma la ruta del ejecutable de un valor UninstallString tipo
// "C:\...\unins000.exe" (con comillas y, a veces, argumentos).
var
  T: String;
  P: Integer;
begin
  T := Trim(S);
  if (Length(T) > 1) and (T[1] = '"') then begin
    P := Pos('"', Copy(T, 2, Length(T) - 1));
    if P > 0 then
      Result := Copy(T, 2, P - 1)
    else
      Result := T;
  end else
    Result := T;
end;

function AppEnEjecucion(): Boolean;
begin
  Result := FindWindowByWindowName('{#NombreApp}') <> 0;
end;

function CompararVersiones(const A, B: String): Integer;
// Devuelve <0 si A es anterior, 0 si son iguales y >0 si A es más nueva.
// ComparePackedVersion recibe Int64 (no String): pasarle texto compila pero
// revienta en tiempo de ejecución con "Type Mismatch". Si alguna versión no
// se puede analizar (p. ej. "Unknown"), se asume -1 para ofrecer actualizar.
var
  VA, VB: Int64;
begin
  Result := -1;
  if not StrToVersion(A, VA) then
    Exit;
  if not StrToVersion(B, VB) then
    Exit;
  Result := ComparePackedVersion(VA, VB);
end;

procedure DetectarVersionAnterior();
var
  Version, Desinst, Dir: String;
  Raiz, Comparacion: Integer;
begin
  CasoAnterior := 0;
  RaizAnterior := 0;
  Raiz := 0;
  if RegQueryStringValue(HKLM64, SubclaveUninstall + ClaveDesinstalacion, 'DisplayVersion', Version) then
    Raiz := HKLM64
  else if RegQueryStringValue(HKLM32, SubclaveUninstall + ClaveDesinstalacion, 'DisplayVersion', Version) then
    Raiz := HKLM32
  else if RegQueryStringValue(HKCU32, SubclaveUninstall + ClaveDesinstalacion, 'DisplayVersion', Version) then
    Raiz := HKCU32
  else if RegQueryStringValue(HKCU64, SubclaveUninstall + ClaveDesinstalacion, 'DisplayVersion', Version) then
    Raiz := HKCU64;

  if Raiz <> 0 then begin
    RaizAnterior := Raiz;
    VersionAnterior := Version;
    ClaveAnterior := SubclaveUninstall + ClaveDesinstalacion;

    Desinst := '';
    RegQueryStringValue(RaizAnterior, ClaveAnterior, 'UninstallString', Desinst);
    DesinstaladorAnterior := ExtraerRuta(Desinst);

    Dir := '';
    RegQueryStringValue(RaizAnterior, ClaveAnterior, 'InstallLocation', Dir);
    DirAnterior := Dir;

    Comparacion := CompararVersiones(VersionAnterior, '{#VersionApp}');
    if Comparacion > 0 then
      CasoAnterior := 3
    else if Comparacion = 0 then
      CasoAnterior := 2
    else
      CasoAnterior := 1;
  end;
end;

function DesinstalarAnterior(): Boolean;
var
  Rc: Integer;
  Intentos: Integer;
begin
  Result := False;
  if DesinstaladorAnterior = '' then
    Exit;
  Exec(DesinstaladorAnterior, '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART',
       '', SW_SHOW, ewWaitUntilTerminated, Rc);
  // El desinstalador se relanza desde una copia temporal y el proceso
  // original termina antes: esperar de verdad a que la clave desaparezca.
  for Intentos := 1 to 60 do begin
    if (RaizAnterior = 0) or (not RegKeyExists(RaizAnterior, ClaveAnterior)) then begin
      Result := True;
      Break;
    end;
    Sleep(500);
  end;
end;

function InitializeSetup(): Boolean;
begin
  DetectarVersionAnterior();
  Result := True;
end;

procedure InitializeWizard();
begin
  if CasoAnterior = 0 then
    Exit;

  if CasoAnterior = 2 then
    PaginaOpcion := CreateInputOptionPage(wpWelcome,
      'La versión {#VersionApp} ya está instalada',
      'WinGet Expert {#VersionApp} está instalado en este equipo. Puedes reinstalarlo para reparar archivos dañados. Tus ajustes y tu historial se conservan.',
      'Elija cómo continuar:', True, False)
  else if CasoAnterior = 3 then
    PaginaOpcion := CreateInputOptionPage(wpWelcome,
      'Hay una versión más reciente instalada',
      'Se encontró WinGet Expert versión ' + VersionAnterior + ', más reciente que la {#VersionApp} que va a instalar. Si continúa, la reemplazará por la versión anterior.',
      'Elija cómo continuar:', True, False)
  else
    PaginaOpcion := CreateInputOptionPage(wpWelcome,
      'Ya hay una versión anterior instalada',
      'Se encontró WinGet Expert versión ' + VersionAnterior + ' en este equipo. Puede actualizarla a la versión {#VersionApp}. Tus ajustes y tu historial se conservan.',
      'Elija cómo continuar:', True, False);

  case CasoAnterior of
    2: begin
      PaginaOpcion.Add('Reinstalar la versión {#VersionApp} (repara los archivos)');
      PaginaOpcion.Add('Desinstalar primero y luego reinstalar');
    end;
    3: begin
      PaginaOpcion.Add('Reemplazar la versión ' + VersionAnterior + ' por la {#VersionApp} (retroceder de versión)');
      PaginaOpcion.Add('Desinstalar la versión ' + VersionAnterior + ' primero y luego instalar la {#VersionApp}');
    end;
    else begin
      PaginaOpcion.Add('Actualizar sobre la versión ' + VersionAnterior + ' (recomendado)');
      PaginaOpcion.Add('Desinstalar primero la versión ' + VersionAnterior + ' y luego instalar la {#VersionApp}');
    end;
  end;
  PaginaOpcion.Add('No instalar nada');
  PaginaOpcion.Values[0] := True;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if (PaginaOpcion <> nil) and (PageID = PaginaOpcion.ID) then
    Result := (CasoAnterior = 0);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (PaginaOpcion <> nil) and (CurPageID = PaginaOpcion.ID) then begin
    if AppEnEjecucion() then begin
      MsgBox('WinGet Expert está en ejecución. Cierra la aplicación y vuelve a intentarlo.',
             mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if PaginaOpcion.Values[1] then begin
      if not DesinstalarAnterior() then
        MsgBox('No se pudo desinstalar la versión anterior; la instalación continuará sobre ella.',
               mbError, MB_OK);
    end else if PaginaOpcion.Values[2] then begin
      // "No instalar nada": no avanzar de página, solo pedir confirmación de salida
      Result := False;
      WizardForm.Close;
    end;
  end;
end;
