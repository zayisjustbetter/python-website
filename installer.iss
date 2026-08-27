[Setup]
AppName=Python in Practice
AppVersion=1.0.0
DefaultDirName={autopf}\Python in Practice
DefaultGroupName=Python in Practice
OutputDir=installer-output
OutputBaseFilename=PythonInPractice-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\PythonInPractice\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Python in Practice"; Filename: "{app}\PythonInPractice.exe"
Name: "{autodesktop}\Python in Practice"; Filename: "{app}\PythonInPractice.exe"

[Run]
Filename: "{app}\PythonInPractice.exe"; Description: "Launch Python in Practice"; Flags: nowait postinstall skipifsilent