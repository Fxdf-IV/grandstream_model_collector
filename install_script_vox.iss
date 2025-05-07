[Setup]
AppName=Script Model Collector
AppVersion=1.0
DefaultDirName={pf}\ScriptModelCollector
DefaultGroupName=Script Vox
OutputDir=.
OutputBaseFilename=ScriptVoxSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\script_model_collector.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\ms-playwright\*"; DestDir: "{app}\ms-playwright"; Flags: recursesubdirs ignoreversion
Source: "icon\\logoRedimensionado.e19fa7071f43c3c19d41.ico"; DestDir: "{app}\\icon"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Script Model Collector"; Filename: "{app}\script_model_collector.exe"
Name: "{group}\Desinstalar Script Vox"; Filename: "{uninstallexe}"