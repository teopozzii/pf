import threading
import time
import webbrowser
import sys
from app import app  # Import your dash app object directly

def run_server():
    # Run the dash app (this blocks)
    app.run(debug=False, port=8050)

if __name__ == '__main__':
    # Required for PyInstaller (especially on Windows/Mac)
    import multiprocessing
    multiprocessing.freeze_support()

    # Start Dash in a separate thread
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()

    # Wait for server to boot
    time.sleep(3)

    # Open browser
    webbrowser.open('http://127.0.0.1:8050')

    # Keep main thread alive
    while t.is_alive():
        try:
            t.join(1)
        except KeyboardInterrupt:
            sys.exit()
