Dim strDir
strDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

Dim strPython
strPython = strDir & "\.venv\Scripts\python.exe"

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = strDir
WshShell.Run """" & strPython & """ """ & strDir & "\auction_automator.py""", 0, False
