@echo off
setlocal
cd /d "%~dp0"
"C:\Users\Harikumar\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true --server.showEmailPrompt false --browser.gatherUsageStats false
