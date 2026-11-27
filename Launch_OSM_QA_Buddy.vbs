Option Explicit

Dim shell, fso, repoDir, bootstrapPath, command, rc
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

repoDir = fso.GetParentFolderName(WScript.ScriptFullName)
bootstrapPath = fso.BuildPath(repoDir, "bootstrap.ps1")

If Not fso.FileExists(bootstrapPath) Then
    MsgBox "bootstrap.ps1 was not found in:" & vbCrLf & repoDir, vbCritical, "OSM QA Buddy"
    WScript.Quit 1
End If

' Keep setup visible: first launch may download and install several components.
command = "powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File " & Chr(34) & bootstrapPath & Chr(34)
rc = shell.Run(command, 1, True)

If rc <> 0 Then
    MsgBox "OSM QA Buddy setup did not complete. Read the PowerShell window for the error details, then click the launcher again after correcting the issue.", vbExclamation, "OSM QA Buddy"
    WScript.Quit rc
End If

Set shell = Nothing
Set fso = Nothing
