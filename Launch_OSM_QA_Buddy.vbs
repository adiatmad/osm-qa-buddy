Option Explicit

Dim shell, fso, repoDir, guiPath, pythonw, exec, line, rc
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

repoDir = fso.GetParentFolderName(WScript.ScriptFullName)
guiPath = fso.BuildPath(repoDir, "OSM_QA_Buddy_GUI.pyw")

If Not fso.FileExists(guiPath) Then
    MsgBox "OSM_QA_Buddy_GUI.pyw was not found in:" & vbCrLf & repoDir, vbCritical, "OSM QA Buddy"
    WScript.Quit 1
End If

' Find pythonw.exe without opening a console window.
On Error Resume Next
Set exec = shell.Exec("cmd /c where pythonw.exe")
pythonw = ""
Do While Not exec.StdOut.AtEndOfStream
    line = Trim(exec.StdOut.ReadLine)
    If line <> "" And fso.FileExists(line) Then
        pythonw = line
        Exit Do
    End If
Loop
On Error GoTo 0

If pythonw = "" Then
    MsgBox "pythonw.exe was not found." & vbCrLf & vbCrLf & _
           "Please make sure Python 3.12+ is installed and available in PATH.", _
           vbCritical, "OSM QA Buddy"
    WScript.Quit 1
End If

shell.CurrentDirectory = repoDir
rc = shell.Run(Chr(34) & pythonw & Chr(34) & " " & Chr(34) & guiPath & Chr(34), 0, False)

Set exec = Nothing
Set shell = Nothing
Set fso = Nothing
