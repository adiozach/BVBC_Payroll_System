' BVBC_Payroll.vbs
' Double-click this file to launch the system with ZERO console window.
' Works on all Windows versions. No CMD flash at all.

Dim objShell, strPath
Set objShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
objShell.Run "pythonw """ & strPath & "\run.pyw""", 0, False
Set objShell = Nothing
