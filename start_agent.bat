@echo off
start /B python -m streamlit run app.py --server.port 8501 --server.headless true
timeout /t 5
start /B C:\"Program Files"\cloudflared\cloudflared.exe tunnel --url http://localhost:8501
