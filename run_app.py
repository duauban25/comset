import subprocess
import os
import webbrowser
import time
import sys

# Path ke folder project kamu
project_dir = "/Users/baktanarta/Documents/compbaru"

proc = subprocess.Popen([
    sys.executable,
    "-m", "streamlit", "run", "app.py",
    "--server.headless=false",
    "--server.port=8501"
], cwd=project_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Tunggu sebentar agar server siap
time.sleep(3)

# Buka otomatis di browser default
webbrowser.open("http://localhost:8501")
