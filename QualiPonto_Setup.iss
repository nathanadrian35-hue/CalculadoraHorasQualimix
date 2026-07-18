; QualiPonto_Setup.iss
; ---------------------
; Script do Inno Setup para o instalador oficial do QualiPonto.
;
; Empacota o executável já gerado pelo PyInstaller (dist\QualiPonto\,
; --onedir — Python/CustomTkinter/Pandas/OpenPyXL/xlrd/Pillow já
; embutidos, sem exigir instalação manual). Instalação por usuário
; (sem exigir administrador/UAC), porque o QualiPonto lê/grava seus
; dados (dados\, Historico\, Logs\, backup\, assets\) sempre ao lado
; do próprio executável (Cap. 13.1) — instalar em "Arquivos de
; Programas" (que exige admin para gravar) quebraria essa persistência
; para um usuário comum.
;
; O AppId é fixo entre versões de propósito (nunca mudar) — é o que
; permite ao Inno Setup reconhecer uma instalação anterior e fazer
; upgrade no lugar, em vez de criar uma segunda entrada em "Programas
; Instalados". Só AppVersion/OutputBaseFilename mudam a cada versão.
;
; Gera um único arquivo: QualiPonto_Setup_v1.1.1.exe

#define AppName "QualiPonto"
#define AppVersion "1.1.1"
#define AppPublisher "Nathan Adrian"
#define AppExeName "QualiPonto.exe"

[Setup]
AppId={{5A18CD71-7B33-4679-8B51-13F04018D5FF}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=installer_output
OutputBaseFilename=QualiPonto_Setup_v1.1.1
SetupIconFile=assets\icones\app.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableWelcomePage=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na Área de Trabalho"; GroupDescription: "Atalhos adicionais:"

[Files]
Source: "dist\QualiPonto\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Abrir o {#AppName} agora"; Flags: nowait postinstall skipifsilent
