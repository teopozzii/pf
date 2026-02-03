import webbrowser
import threading
import time
import subprocess
import sys
import os

if getattr(sys, 'frozen', False):
    # Running as .exe - use bundled assets
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# Start your Dash app in a subprocess
proc = subprocess.Popen([sys.executable, "app.py"])

# Wait 3 seconds for server to start
time.sleep(3)

# Open browser to localhost:8050
webbrowser.open('http://127.0.0.1:8050')

# Keep launcher alive
proc.wait()