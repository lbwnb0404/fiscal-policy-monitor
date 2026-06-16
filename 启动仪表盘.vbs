' 财政政策舆情监测 - 一键启动
' 无黑窗口启动 Streamlit 并打开浏览器
Dim shell, pythonExe, scriptPath
Set shell = CreateObject("WScript.Shell")
pythonExe = "C:\Users\jjt\AppData\Local\Python\pythoncore-3.14-64\python.exe"
scriptPath = "C:\Users\jjt\Desktop\财政政策舆情监测\启动仪表盘.py"
shell.Run """" & pythonExe & """ """ & scriptPath & """", 1, False
