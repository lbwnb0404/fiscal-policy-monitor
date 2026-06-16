@echo off
chcp 65001 >nul
title Fiscal Monitor
set PYTHONPATH=C:\Users\jjt\Desktop\财政政策舆情监测\py_deps_new
set MPLCONFIGDIR=C:\Users\jjt\Desktop\财政政策舆情监测\output\tmp
start /B "" "C:\Users\jjt\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m streamlit run "C:\Users\jjt\Desktop\财政政策舆情监测\streamlit_app.py" --global.developmentMode false --server.port 8501
ping 127.0.0.1 -n 6 >nul
start http://localhost:8501