# Testing & Verification Guide: Graceful Server Shutdown

## Phase 4: Manual Testing Instructions

This guide walks through testing the graceful server shutdown implementation on macOS and Windows.

---

## Test Environment Setup

### Prerequisites
- Python 3.11+ with virtual environment activated
- PyInstaller installed (`pip install -r requirements.txt` should include it)
- Administrator access (Windows: UAC may prompt during process inspection)

### Quick Test (Development Mode)

Run the app in development mode to test shutdown behavior:

```bash
cd /Users/matteopozzi/code/conto
python launcher.py
```

Expected output:
```
2026-03-30 11:17:54,507 - __main__ - INFO - Starting Dash server on http://127.0.0.1:8050...
2026-03-30 11:17:54,507 - __main__ - INFO - Browser health monitor started (checking every 2 seconds)
2026-03-30 11:17:54,520 - __main__ - INFO - Server started successfully
2026-03-30 11:17:57,512 - __main__ - INFO - Opening browser at http://127.0.0.1:8050...
```

---

## Test Case 1: Normal Shutdown via Timeout

**What we're testing**: The 10-second timeout in the test should trigger graceful shutdown.

**Steps**:
1. Run: `timeout 10 python launcher.py`
2. Observe logs
3. Wait for timeout

**Expected behavior**:
- ✅ Server starts normally
- ✅ Health check pings succeed (every 2 seconds)
- ✅ Browser opens automatically
- ✅ After ~8-10 seconds, timeout triggers graceful shutdown
- ✅ Logs show: `"Shutdown signal received, initiating graceful shutdown..."`
- ✅ Server thread exits cleanly
- ✅ No zombie processes remain

**Verification**:
```bash
# After test completes, verify no leftover processes:
lsof -i :8050           # Should show nothing
ps aux | grep python    # Should not show launcher.py
```

---

## Test Case 2: Manual Ctrl+C Shutdown

**What we're testing**: SIGINT handling (Ctrl+C).

**Steps**:
1. Run: `python launcher.py`
2. Wait 5 seconds for server to start
3. Press `Ctrl+C` in the terminal
4. Observe shutdown logs

**Expected behavior**:
- ✅ Server receives SIGINT signal
- ✅ Logs show: `"Shutdown signal received, initiating graceful shutdown..."`
- ✅ Server shuts down gracefully within 5 seconds
- ✅ All threads terminate
- ✅ No exceptions in logs
- ✅ Process exits with code 0

**Verification**:
```bash
# After Ctrl+C:
echo $?  # Should print 0 (successful exit)
lsof -i :8050  # Should show nothing
```

---

## Test Case 3: Browser Window Closure Detection

**What we're testing**: Heartbeat monitoring detects when browser is closed.

**How it works**:
1. Browser sends heartbeat via JavaScript every 2 seconds (POST /heartbeat)
2. Launcher checks heartbeat freshness every 3 seconds (GET /last_heartbeat)
3. If no heartbeat for >4 seconds, counts as 1 strike
4. After 3 consecutive strikes (6+ seconds), triggers graceful shutdown

**macOS Instructions**:
1. Run: `python launcher.py`
2. Wait for browser to open (Chrome, Safari, etc.)
3. Watch terminal logs for: `Browser heartbeat monitor started`
4. You should see logs: `POST /heartbeat HTTP/1.1` every ~2 seconds
5. Close the browser window (⌘W or red close button)
6. Watch terminal for shutdown logs:
   - `Browser heartbeat stale (1/3)` — First stale check
   - `Browser heartbeat stale (2/3)` — Second stale check
   - `Browser heartbeat stale (3/3)` — Third stale check hits threshold
   - `Browser heartbeat lost - initiating graceful shutdown` — Shutdown triggered
7. App should exit within 10 seconds of closing browser

**Windows Instructions**:
1. Run: `python launcher.py`
2. Wait for browser to open (Edge, Chrome, etc.)
3. Watch terminal for: `Browser heartbeat monitor started`
4. You should see logs: `POST /heartbeat HTTP/1.1` every ~2 seconds
5. Close the browser window (Alt+F4 or close button)
6. Watch for same shutdown sequence as macOS above
7. App should exit within 10 seconds of closing browser

**Expected behavior**:
- ✅ While browser is open: heartbeats logged every ~2 seconds
- ✅ After closing browser: heartbeat logs stop
- ✅ Launcher logs: `Browser heartbeat stale (1/3)`, `(2/3)`, `(3/3)`
- ✅ On 3rd stale: `Browser heartbeat lost - initiating graceful shutdown`
- ✅ Server gracefully shuts down
- ✅ App closes within 6-10 seconds of browser close

**Verification**:
```bash
# While browser is open (in another terminal):
curl -s http://127.0.0.1:8050/last_heartbeat | jq .

# Should show seconds_since_heartbeat < 4 (heartbeat is fresh)
# Example: {"seconds_since_heartbeat": 1.23}

# After closing browser:
curl -s http://127.0.0.1:8050/last_heartbeat | jq .

# Should show rapidly increasing values (no new heartbeats)
# Example: {"seconds_since_heartbeat": 8.5}
```

**Automated test**:
```bash
# Run integration test (simulates heartbeat checks)
python tests/test_heartbeat_integration.py

# Run shutdown simulation test
python tests/test_shutdown_simulation.py
```

---

## Test Case 4: Force Kill from Task Manager/Activity Monitor

**What we're testing**: SIGTERM handling (system/process manager termination).

**macOS Instructions**:
1. Run: `python launcher.py`
2. Open Activity Monitor
3. Find the Python process running the launcher
4. Right-click → "Terminate"
5. Observe terminal output (may be interrupted by termination)

**Windows Instructions**:
1. Run: `python launcher.py`
2. Open Task Manager (Ctrl+Shift+Esc)
3. Find "Python" process in the list
4. Right-click → "End Task"
5. Observe terminal output (may be interrupted by termination)

**Expected behavior**:
- ✅ Process receives SIGTERM signal
- ✅ Logs show graceful shutdown attempt (or none if killed too quickly)
- ✅ Server thread shuts down
- ✅ No zombie processes remain
- ✅ Port 8050 is released immediately

**Verification**:
```bash
# After force-kill:
sleep 2
lsof -i :8050  # Should show nothing
netstat -an | grep 8050  # Windows: netstat -ano | findstr :8050 (should be empty)
```

---

## Test Case 5: Rapid Close (Double-Click Close Button)

**What we're testing**: Signal handling under rapid, repeated signals.

**Steps**:
1. Run: `python launcher.py`
2. Wait for server to start
3. Rapidly click the close button multiple times
4. Observe for any errors or corruption

**Expected behavior**:
- ✅ First close signal initiates shutdown
- ✅ Subsequent signals are ignored (SHUTDOWN_REQUESTED check)
- ✅ No exceptions or crashes
- ✅ Clean exit within 5 seconds

**Verification**:
```bash
# After rapid close:
echo $?  # Should be 0
ps aux | grep launcher  # Should be gone
```

---

## Test Case 6: Port Release on Restart

**What we're testing**: Graceful port release (prevents EADDRINUSE errors).

**Steps**:
1. Run: `python launcher.py`
2. Wait for server to start fully
3. Press Ctrl+C to shut down
4. Immediately (within 1 second) run: `python launcher.py` again
5. Verify app starts without port error

**Expected behavior**:
- ✅ First app shuts down gracefully
- ✅ Port 8050 is immediately released
- ✅ Second app starts on port 8050 without error
- ✅ No "Address already in use" error

**Error (means graceful shutdown failed)**:
```
Address [8050] already in use! Please try a different port
error
```

---

## PyInstaller Build Testing

Once development testing is passed, test with PyInstaller builds.

### macOS Build & Test

```bash
# 1. Build the app as .app bundle
pyinstaller launcher.py --windowed --name BankStatementApp \
  --add-data "assets:assets" --add-data "pages:pages" --add-data "utils:utils" \
  --hidden-import dash_pages --hidden-import dash_bootstrap_components \
  --hidden-import plotly.io._renderers

# 2. Run the app
open dist/BankStatementApp.app

# 3. Check console logs
log stream --predicate 'eventMessage contains[c] "launcher"' --level debug

# 4. Verify process in Activity Monitor
Activity Monitor → Python → (check for launcher process)

# 5. From Activity Monitor: right-click → Quit
# (OR click close button in browser)
# Verify process disappears within 5 seconds
```

### Windows Build & Test

```bash
# 1. Build the .exe
pyinstaller launcher.py --onefile --windowed --name BankStatementApp ^
  --add-data "assets;assets" --add-data "pages;pages" --add-data "utils;utils" ^
  --hidden-import dash_pages --hidden-import dash_bootstrap_components ^
  --hidden-import plotly.io._renderers

# 2. Run the app
dist\BankStatementApp.exe

# 3. Check process in Task Manager
tasklist | findstr python    # Should show BankStatementApp.exe

# 4. Close the window (or use Task Manager "End Task")
# Verify no orphaned python.exe processes remain

# 5. Verify port release
netstat -ano | findstr :8050  # Should be empty after exit
```

---

## Endpoint Verification Checklist

### /heartbeat Endpoint (Browser → Server)
- [ ] Browser sends POST requests every 2 seconds
- [ ] Server responds with HTTP 200 OK
- [ ] Returns JSON: `{"status": "heartbeat_received"}`
- [ ] Closes when browser tab/window is closed
- [ ] Can be verified in browser DevTools → Network tab

### /last_heartbeat Endpoint (Launcher → Server)
- [ ] Returns HTTP 200 OK while server is running
- [ ] Returns JSON: `{"seconds_since_heartbeat": <number>}`
- [ ] Returns < 4 seconds when browser is actively sending heartbeats
- [ ] Returns > 4 seconds after browser is closed (for >6 seconds, triggers shutdown)
- [ ] Launcher calls this every 3 seconds

### /health Endpoint (Server status, not used for shutdown)
- [ ] Returns HTTP 200 OK while server is running
- [ ] Returns JSON: `{"status": "ok", "service": "conto"}`
- [ ] Always responds (good for general server health checks)
- [ ] NOT used for browser disconnect detection (heartbeat is used instead)

### /shutdown Endpoint (Emergency shutdown)
- [ ] Accepts POST requests
- [ ] Returns HTTP 200 OK before shutdown
- [ ] Returns JSON: `{"message": "Server shutting down"}`
- [ ] Actually stops the server after returning response
- [ ] Can be called multiple times without error

**Test with curl**:
```bash
# Check server health (always works if server running)
curl -s http://127.0.0.1:8050/health | jq .

# Check browser heartbeat freshness (key indicator)
curl -s http://127.0.0.1:8050/last_heartbeat | jq .
# While browser open: ~1-2 seconds since heartbeat
# After browser closed: >6 seconds since heartbeat

# Trigger explicit shutdown (useful for testing)
curl -X POST http://127.0.0.1:8050/shutdown | jq .
```

---

## Logging & Debugging

All lifecycle events are logged. Check for these patterns:

**Normal startup with active browser**:
```
Starting Dash server on http://127.0.0.1:8050...
Browser heartbeat monitor started (checking every 3 seconds)
Server started successfully
Opening browser at http://127.0.0.1:8050...
2026-03-30 11:30:27,107 - werkzeug - INFO - 127.0.0.1 - - "POST /heartbeat HTTP/1.1" 200 -
2026-03-30 11:30:27,961 - werkzeug - INFO - 127.0.0.1 - - "POST /heartbeat HTTP/1.1" 200 -
2026-03-30 11:30:28,498 - werkzeug - INFO - 127.0.0.1 - - "GET /last_heartbeat HTTP/1.1" 200 -
```

**Browser actively sending heartbeats**:
```
werkzeug - INFO - 127.0.0.1 - - "POST /heartbeat HTTP/1.1" 200 -   [every ~2 seconds]
__main__ - DEBUG - Browser heartbeat received                       [healthy status]
```

**Browser closes (heartbeat stops)**:
```
__main__ - INFO - Browser heartbeat stale (1/3)                   [First miss]
__main__ - INFO - Browser heartbeat stale (2/3)                   [Second miss]
__main__ - INFO - Browser heartbeat stale (3/3)                   [Third miss - threshold hit]
__main__ - INFO - Browser heartbeat lost - initiating graceful shutdown
```

**Graceful shutdown**:
```
Shutdown signal received, initiating graceful shutdown...
Stopping Dash server...
Server shutdown complete
Waiting for server thread to finish (timeout: 5 seconds)...
Browser heartbeat monitor stopped
Application shutdown complete
```

**Enable detailed logging** (for debugging):
```python
# In launcher.py, change:
logging.basicConfig(level=logging.INFO, ...)
# To:
logging.basicConfig(level=logging.DEBUG, ...)
```

This will show every heartbeat check with timestamps.

---

## Success Criteria

All of the following must be true for full verification:

- ✅ **macOS**: App closes completely when window closed or Quit selected
- ✅ **Windows**: App closes completely when close button clicked or closed via Task Manager
- ✅ **Both**: No orphaned Python processes in Activity Monitor / Task Manager
- ✅ **Both**: Port 8050 is immediately released (can restart app without delay)
- ✅ **Both**: Graceful shutdown logs appear in console
- ✅ **Both**: Browser stays open (not killed by app)
- ✅ **Both**: /health endpoint responds while server running
- ✅ **Both**: No EADDRINUSE errors on rapid restart
- ✅ **Both**: PyInstaller builds behave identically to development mode
- ✅ **Both**: Signal handlers work (Ctrl+C, SIGTERM, SIGABRT)

---

## Troubleshooting

### Problem: "curl /health still returns 200 even after closing browser"
**Root cause (ORIGINAL ISSUE)**: 
- Health endpoint checks if the SERVER is running, not if the BROWSER is connected
- Server always responds to local health checks regardless of browser state

**Solution (FIXED)**:
- Use `/last_heartbeat` endpoint instead (returns seconds since last browser heartbeat)
- Browser sends client-side heartbeats via JavaScript (`POST /heartbeat`)
- When browser closes, JavaScript stops, heartbeat stops
- Launcher detects stale heartbeat and triggers shutdown

**Verification**:
```bash
# This will ALWAYS return 200 (not useful for browser detection):
curl -s http://127.0.0.1:8050/health

# This is the KEY metric (will show heartbeat staleness):
curl -s http://127.0.0.1:8050/last_heartbeat | jq .
# Browser open: {"seconds_since_heartbeat": 1.5}
# Browser closed: {"seconds_since_heartbeat": 7.2}
```

### Problem: Server doesn't shut down after timeout
**Solution**: 
- Check if browser window is still making requests
- Increase timeout value in test: `timeout 20 python launcher.py`
- Check logs for "Server shutdown complete" message
- Verify `/last_heartbeat` shows stale heartbeat (> 4 seconds)

### Problem: Port still in use after shutdown
**Possible causes**:
- Graceful shutdown incomplete (check for 5-second Werkzeug drain timeout)
- `TIME_WAIT` state (normal TCP behavior, resolves in 60 seconds)

**Solution**:
```bash
# macOS: Force release port
lsof -ti:8050 | xargs kill -9

# Windows: Force release port
netstat -ano | findstr :8050  # Find PID
taskkill /PID <PID> /F
```

### Problem: Heartbeats not being sent from browser
**Causes**:
- Browser network is blocked (firewall, proxy)
- JavaScript error in dcc.Interval callback
- Browser JavaScript disabled

**Solution**:
- Check browser console (F12) for JavaScript errors
- Verify no firewall blocking POST requests to `/heartbeat`
- Check network tab in DevTools: should show `POST /heartbeat` every 2 seconds
- Verify Dash interval component: `dcc.Interval(id='heartbeat-interval', interval=2000)`

### Problem: "Browser heartbeat stale" logged even with browser open
**Causes**:
- Browser tab is frozen/not responding
- Network connectivity issue
- Server is slow to respond

**Solution**:
- Refresh the browser tab
- Check browser performance (is it frozen?)
- Increase stale threshold in launcher.py: change `< 4` to `< 6` in `check_browser_heartbeat()`
- Check server logs for performance issues

### Problem: Multiple shutdown attempts in logs
**Cause**: Recursive atexit calls

**Solution**: Verify launcher.py has the guard check at start of `graceful_shutdown()`:
```python
if SHUTDOWN_REQUESTED:
    return  # Already shutting down
```

---

## Next Steps After Verification

1. **Code Review**: Commit Changes with message:
   ```
   feat(launcher): implement graceful server shutdown with signal handling
   
   - Add signal handlers (SIGINT, SIGTERM, SIGABRT) for clean shutdown
   - Replace app.run() with make_server() for explicit control
   - Add /health and /shutdown Flask endpoints
   - Implement browser health monitoring (detect window/tab close)
   - Graceful timeout: 5 seconds max for request draining
   - Works on both macOS (.app) and Windows (.exe) with PyInstaller
   
   Closes: <issue-number>
   ```

2. **Update CI/CD**: No changes needed (PyInstaller config unchanged)

3. **Release**: Include in next build with test results attached

4. **Monitor**: Add logging to production deploys to track shutdown behavior

---

## References

- [Werkzeug Server Shutdown](https://werkzeug.palletsprojects.com/en/2.3.x/serving/#running-a-server)
- [Signal Handling in Python](https://docs.python.org/3/library/signal.html)
- [Flask Application Context](https://flask.palletsprojects.com/en/2.3.x/appcontext/)
- [PyInstaller Runtime Information](https://pyinstaller.org/en/stable/runtime-information.html)
