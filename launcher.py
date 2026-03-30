import threading
import time
import webbrowser
import sys
import signal
import atexit
import logging
from werkzeug.serving import make_server
from app import app
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global shutdown flag and server reference
SHUTDOWN_REQUESTED = False
server = None
server_thread = None
monitor_thread = None
HEALTH_CHECK_FAIL_COUNT = 0
HEALTH_CHECK_FAIL_THRESHOLD = 3  # Fail 3 times before assuming browser is closed


def check_browser_heartbeat() -> bool:
    """
    Check if the browser has sent a heartbeat recently (within 4 seconds).
    Returns True if browser is active, False if heartbeat is stale.
    """
    try:
        response = requests.get(
            'http://127.0.0.1:8050/last_heartbeat',
            timeout=2
        )
        data = response.json()
        seconds_since_heartbeat = data.get('seconds_since_heartbeat', 999)
        # Browser should send heartbeat every 2 seconds, so if > 4 seconds, something is wrong
        return seconds_since_heartbeat < 4
    except (requests.ConnectionError, requests.Timeout):
        return False
    except Exception as e:
        logger.debug(f"Heartbeat check error: {e}")
        return False


def monitor_browser() -> None:
    """
    Monitor browser connection by checking if heartbeats are being received.
    Browser sends heartbeat via /heartbeat endpoint every 2 seconds.
    If 3 consecutive heartbeat checks fail, assume browser is closed → shutdown.
    """
    global SHUTDOWN_REQUESTED, HEALTH_CHECK_FAIL_COUNT
    
    logger.info("Browser heartbeat monitor started (checking every 3 seconds)")
    
    # Initial delay to let server fully start
    time.sleep(2)
    
    while not SHUTDOWN_REQUESTED and server_thread.is_alive():
        try:
            if check_browser_heartbeat():
                HEALTH_CHECK_FAIL_COUNT = 0  # Reset counter on successful heartbeat
                logger.debug("Browser heartbeat received")
            else:
                HEALTH_CHECK_FAIL_COUNT += 1
                logger.info(f"Browser heartbeat stale ({HEALTH_CHECK_FAIL_COUNT}/{HEALTH_CHECK_FAIL_THRESHOLD})")
                
                if HEALTH_CHECK_FAIL_COUNT >= HEALTH_CHECK_FAIL_THRESHOLD:
                    logger.info("Browser heartbeat lost - initiating graceful shutdown")
                    graceful_shutdown()
                    break
            
            time.sleep(3)  # Check every 3 seconds
        
        except Exception as e:
            logger.error(f"Error in browser monitor: {e}")
            time.sleep(3)
    
    logger.info("Browser heartbeat monitor stopped")


def graceful_shutdown(signum=None, frame=None) -> None:
    """
    Gracefully shutdown the server and exit the application.
    Can be called from signal handlers or explicitly.
    """
    global SHUTDOWN_REQUESTED, server, server_thread, monitor_thread
    
    if SHUTDOWN_REQUESTED:
        # Already shutting down, avoid recursive calls
        return
    
    SHUTDOWN_REQUESTED = True
    logger.info("Shutdown signal received, initiating graceful shutdown...")
    
    if server is not None:
        logger.info("Stopping Dash server...")
        try:
            server.shutdown()
            logger.info("Server shutdown complete")
        except Exception as e:
            logger.error(f"Error during server shutdown: {e}")
    
    # Wait for server thread to finish (with timeout)
    if server_thread is not None and server_thread.is_alive():
        logger.info("Waiting for server thread to finish (timeout: 5 seconds)...")
        server_thread.join(timeout=5)
        if server_thread.is_alive():
            logger.warning("Server thread did not finish gracefully within timeout")
    
    # Wait for monitor thread to finish
    if monitor_thread is not None and monitor_thread.is_alive():
        monitor_thread.join(timeout=2)
    
    logger.info("Application shutdown complete")
    sys.exit(0)


def run_server() -> None:
    """Run the Dash server using Werkzeug."""
    global server
    
    try:
        logger.info("Starting Dash server on http://127.0.0.1:8050...")
        server = make_server('127.0.0.1', 8050, app, threaded=True)
        logger.info("Server started successfully")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Error running server: {e}")
        raise
    finally:
        logger.info("Server thread exiting")


if __name__ == '__main__':
    # Required for PyInstaller (especially on Windows/Mac)
    import multiprocessing
    multiprocessing.freeze_support()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)   # Ctrl+C
    signal.signal(signal.SIGTERM, graceful_shutdown)  # Container/system termination
    signal.signal(signal.SIGABRT, graceful_shutdown)  # Abort signal
    atexit.register(graceful_shutdown)                # Fallback on exit

    # Start Dash in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Start browser health monitor in a separate thread
    monitor_thread = threading.Thread(target=monitor_browser, daemon=True)
    monitor_thread.start()

    # Wait for server to boot
    time.sleep(3)

    # Open browser
    logger.info("Opening browser at http://127.0.0.1:8050...")
    webbrowser.open('http://127.0.0.1:8050')

    # Keep main thread alive until shutdown is requested
    while not SHUTDOWN_REQUESTED and server_thread.is_alive():
        try:
            server_thread.join(1)
        except KeyboardInterrupt:
            graceful_shutdown()
