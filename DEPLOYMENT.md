# DiskWarden - Service-Driven Disk Health Monitoring

DiskWarden is a self-hosted Flask-based disk health monitoring system with background scanning, persistent state tracking, and optional InfluxDB + Grafana integration.

## Key Improvements Over Previous Version

### ✅ Background Scanning
- **Runs independently** even when UI is closed
- **Configurable interval** via Settings page (default: 60 seconds)
- **Enabled by environment variable** `DISKWARDEN_SCANNER=1` to prevent duplicate scanners in multi-worker setups
- Runs even if no HTTP requests are made to the server

### ✅ Alert Spam Prevention (State Tracking)
- **Persistent state tracking** using SQLite database
- **Alert on transition only**: Alerts sent only when disk health crosses threshold
  - `OK` → `BELOW_THRESHOLD`: Alerts triggered
  - `BELOW_THRESHOLD` → `OK`: Optional recovery alerts
  - No alerts while state unchanged
- **Optional recovery alerts** controlled by `notifyOnRecovery` setting
- **Reminder alerts** (optional) controlled by `alertCooldownMinutes`:
  - `0` or missing: Reminders disabled
  - N > 0: Send reminder alerts every N minutes if disk still below threshold
- **Graceful failure**: If email or Discord fails, scan continues

### ✅ Metrics Storage (Optional)
- **Self-hosted InfluxDB** for time-series metrics
- **Grafana dashboards** for visualization
- **No SaaS, no cloud, no licenses**
- Metrics only written if `influxEnabled: true` in settings
- Captures: health%, performance%, temperature, power-on hours, lifetime days

### ✅ Settings Without Restart
- All changes take effect immediately
- Scan interval dynamically adjusted
- Mail configuration updated live
- InfluxDB settings applied to next scan

### ✅ UI as Dashboard (Read-Only)
- No more auto-refresh fetching fresh scans on page load
- **Manual controls**:
  - "Refresh Disk Health" button: Shows last cached scan data
  - "Scan Now" button: Triggers immediate scan (useful for testing)
- Shows scanner status and next scheduled scan time

---

## Architecture

### Service-Driven Approach

```
┌─────────────────────────────────────────────────────────────┐
│ DiskWarden Container (DISKWARDEN_SCANNER=1)                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Flask Web UI (Port 7500)                                   │
│  ├─ GET  /                    → index.html                  │
│  ├─ GET  /settings            → settings.html               │
│  └─ REST API (see below)                                    │
│                                                               │
│  Background Scheduler (APScheduler)                          │
│  └─ perform_disk_scan() every N seconds                     │
│     ├─ Run HDSentinel                                       │
│     ├─ Check state transitions                              │
│     ├─ Send alerts (Discord, SMTP)                          │
│     └─ Write metrics to InfluxDB (if enabled)               │
│                                                               │
│  State Database (SQLite)                                    │
│  └─ diskwarden_state.db                                    │
│     ├─ disk_state table                                     │
│     ├─ Persistent state tracking                            │
│     └─ Alert cooldown timestamps                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         │
         ├─→ InfluxDB:8086 (optional, if enabled)
         ├─→ Grafana:3000 (optional, if enabled)
         └─→ Discord/SMTP (configured in settings)
```

---

## API Endpoints

### Dashboard & Caching

**GET /api/disk_health**
- Returns last cached scan results
- **Does NOT trigger a new scan**
- Response:
  ```json
  [
    {
      "device": "/dev/sda",
      "model_id": "Samsung SSD 860",
      "serial_no": "ABC123XYZ",
      "health": "95%",
      "performance": "100%",
      "temperature": "45°C",
      ...
    }
  ]
  ```
- Status `503` if no scan data available yet

**POST /api/scan_now**
- Triggers immediate disk scan
- Respects state tracking and alert suppression
- Response:
  ```json
  {
    "message": "Scan completed",
    "last_scan": "2026-01-22T14:30:45.123456",
    "disk_count": 3
  }
  ```

**GET /api/status**
- Scanner status and timing info
- Response:
  ```json
  {
    "last_scan": "2026-01-22T14:30:45.123456",
    "next_scan": "2026-01-22T14:31:45.123456",
    "scan_interval_seconds": 60,
    "disks_below_threshold": 1,
    "scanner_running": true,
    "influx_enabled": true,
    "grafana_url": "http://grafana:3000"
  }
  ```

### Configuration

**GET /api/settings**
- Returns current settings

**POST /api/settings**
- Update any settings (merged with existing)
- Changes take effect immediately
- Example:
  ```json
  {
    "scanIntervalSeconds": 120,
    "notifyOnRecovery": true,
    "alertCooldownMinutes": 30,
    "influxEnabled": true,
    "influxUrl": "http://influxdb:8086"
  }
  ```

**POST /api/email_settings** (backwards compatibility)
- Update email configuration

**POST /api/test_email**
- Send test email with current config

**POST /api/test_message**
- Send test Discord message with webhook URL

---

## State Tracking Logic

### Disk Identification

**Primary Key**: `serial_no`  
**Fallback**: `device` (if serial missing)

### State Machine

```
Initial State: OK

OK → (health < threshold) → BELOW_THRESHOLD
  └─ **Alert sent** (transition alert)

BELOW_THRESHOLD → (health ≥ threshold) → OK
  └─ **Alert sent only if notifyOnRecovery=true** (recovery alert)

BELOW_THRESHOLD (no state change)
  └─ **Reminder alert sent** if:
      - alertCooldownMinutes > 0 AND
      - Last alert time + cooldown minutes elapsed
```

### Example Scenarios

**Scenario 1: Disk degradation with no recovery alert**
```
00:00 - Disk health 95% → State: OK
00:01 - Disk health 85% → State: BELOW_THRESHOLD (threshold 90%)
        Alert sent: "⚠️ Disk Health Alert"
00:02 - Disk health 84% → State: BELOW_THRESHOLD (no change)
        No alert (same state)
00:03 - Disk health 92% → State: OK (recovered)
        No alert sent (notifyOnRecovery=false by default)
```

**Scenario 2: With recovery alerts and reminders**
```
Settings: healthThreshold=90, notifyOnRecovery=true, alertCooldownMinutes=30

00:00 - Disk health 95% → State: OK
00:01 - Disk health 85% → State: BELOW_THRESHOLD
        Alert: "⚠️ Disk Health Alert"
00:31 - (no state change, cooldown elapsed)
        Alert: "🔔 Disk Health Reminder: still at 85%"
01:01 - (no state change, cooldown elapsed again)
        Alert: "🔔 Disk Health Reminder: still at 85%"
02:00 - Disk health 92% → State: OK
        Alert: "✅ Disk Recovered"
```

### Testing State Transitions

To test the state tracking without waiting for disks to actually fail:

1. **Simulate low health by modifying HDSentinel output parsing** (development only)
2. **Trigger manual scan**: Click "Scan Now" button on dashboard
3. **Check state database**:
   ```bash
   sqlite3 diskwarden_state.db "SELECT disk_id, state, health_percent FROM disk_state;"
   ```
4. **Modify threshold temporarily** via Settings page to force transitions
5. **Check logs** for alert messages

---

## Deployment

### Single-Container Deployment (UI Only, No Background Scanning)

```bash
docker run -d \
  --name diskwarden \
  -p 7500:7500 \
  -v $(pwd)/settings.json:/app/settings.json \
  diskwarden:latest
```

**Note**: Background scanner is disabled. Use `/api/scan_now` endpoint to trigger manual scans.

### Full Stack Deployment (Recommended)

```bash
docker-compose up -d
```

This starts:
- **DiskWarden** on port 7500 (with background scanner enabled)
- **InfluxDB** on port 8086
- **Grafana** on port 3000

### Environment Variables

- `DISKWARDEN_SCANNER=1` → Enable background scanner (required for production)
- `DISKWARDEN_SCANNER=0` or unset → Disable scanner (UI-only mode)

### Safe Deployment (Preventing Duplicate Scanners)

If running DiskWarden with multiple Flask workers (e.g., Gunicorn with 4 workers):

**Option A: Single-Worker Service (Recommended)**
```yaml
# docker-compose.yml
diskwarden:
  build: .
  command: python3 app.py  # Single-threaded Flask
  environment:
    DISKWARDEN_SCANNER: "1"
```

**Option B: Multi-Worker UI + Separate Scanner**
```yaml
# diskwarden-ui.yml - port 7500 (no scanner)
diskwarden-ui:
  build: .
  ports:
    - "7500:7500"
  environment:
    DISKWARDEN_SCANNER: "0"  # Disable scanner
  command: gunicorn -w 4 app:app

# diskwarden-scanner.yml - background only (no exposed port)
diskwarden-scanner:
  build: .
  environment:
    DISKWARDEN_SCANNER: "1"  # Enable scanner
  volumes_from:
    - diskwarden-ui  # Share settings and state DB
  command: python3 app.py
```

This approach:
- Keeps UI responsive across multiple workers
- Ensures scanner runs exactly once
- Shares persistent state database

---

## Configuration

### settings.json

```jsonc
{
  // Scanning
  "scanIntervalSeconds": 60,        // How often to scan (seconds)

  // Alerts
  "healthThreshold": 90,            // Health % threshold for alerts
  "notifyOnRecovery": false,        // Alert when disk recovers
  "alertCooldownMinutes": 0,        // Minutes between reminder alerts (0=disabled)

  // Discord
  "webhookUrl": "",                 // Discord webhook URL (optional)

  // Email (SMTP)
  "email": "",                      // From address (optional)
  "emailPassword": "",              // App password (optional)
  "smtpServer": "smtp.gmail.com",   // SMTP server
  "smtpPort": 587,                  // SMTP port

  // InfluxDB & Grafana
  "influxEnabled": false,           // Enable metrics storage
  "influxUrl": "http://influxdb:8086",
  "influxToken": "",                // InfluxDB API token
  "influxOrg": "diskwarden",
  "influxBucket": "diskwarden",
  "grafanaUrl": ""                  // Grafana URL (adds link to navbar)
}
```

### InfluxDB Setup

1. **Create Organization & Bucket** (one-time):
   ```bash
   docker exec influxdb influx org create --name diskwarden
   docker exec influxdb influx bucket create --name diskwarden --org diskwarden
   ```

2. **Generate API Token**:
   - Open InfluxDB UI: `http://localhost:8086`
   - Login with default credentials (admin/changeme)
   - Settings → API Tokens → Generate Token
   - Copy token to DiskWarden settings

3. **Configure in DiskWarden**:
   - Go to Settings → InfluxDB & Grafana
   - Enable InfluxDB, paste token
   - Save settings

### Grafana Setup

1. **Configure InfluxDB DataSource** (one-time):
   - Open Grafana: `http://localhost:3000` (admin/admin)
   - Data Sources → Add InfluxDB v2
   - URL: `http://influxdb:8086`
   - Token: (same as DiskWarden)
   - Org: `diskwarden`
   - Bucket: `diskwarden`

2. **Create Dashboard**:
   - New Dashboard → Add Panel
   - Query: `disk_health` measurement
   - Fields: `health_percent`, `temp_c`, etc.
   - Tags: Filter by `device`, `serial_no`

3. **Add Link to DiskWarden**:
   - Settings → Grafana URL → Save
   - Navbar will include "📊 Grafana" link

---

## Monitoring & Logging

### View Logs

```bash
# Docker container
docker logs diskwarden -f

# Docker Compose
docker-compose logs diskwarden -f
```

### Key Log Messages

```
INFO - Starting disk scan...
INFO - Disk scan complete: 3 disks
INFO - Sending alert for disk ABC123XYZ: transition
DEBUG - Email sent to user@example.com
DEBUG - Discord notification sent
INFO - Wrote 3 disk metrics to InfluxDB
```

### Database Inspection

```bash
# Check disk states
sqlite3 diskwarden_state.db "SELECT disk_id, state, health_percent, last_state_change FROM disk_state;"

# Check alert cooldown times
sqlite3 diskwarden_state.db "SELECT disk_id, last_alert_time FROM disk_state WHERE state='BELOW_THRESHOLD';"
```

---

## Troubleshooting

### Scanner Not Running

**Check environment variable:**
```bash
docker inspect diskwarden | grep DISKWARDEN_SCANNER
```

**Fix:**
```bash
# Restart with scanner enabled
docker-compose down
docker-compose up -d
```

### No Scan Data Available

**Cause**: Scanner hasn't run yet  
**Fix**: Wait for first scheduled scan, or click "Scan Now" button

### Alerts Not Being Sent

1. **Check scanner is running**: `/api/status` should show `"scanner_running": true`
2. **Verify alert settings**: Health threshold, webhook URL, email config
3. **Test notifications**: Use "Send Test Message" and "Send Test Email" buttons
4. **Check logs**: `docker logs diskwarden`
5. **Verify state transitions**: `sqlite3 diskwarden_state.db "SELECT * FROM disk_state;"`

### InfluxDB Metrics Not Appearing

1. **Enable InfluxDB**: Settings → Enable InfluxDB Metrics
2. **Verify connection**: Check logs for "Failed to write InfluxDB metrics"
3. **Verify token**: Token must have write permission to bucket
4. **Manual check**:
   ```bash
   docker exec influxdb influx query 'from(bucket:"diskwarden") |> range(start: -1h)'
   ```

---

## Architecture Benefits

| Feature | Before | After |
|---------|--------|-------|
| **Scanning** | UI-driven (60s intervals) | Background (configurable) |
| **Alert Spam** | Every request triggers alerts | Only on state transitions |
| **Monitoring** | UI must be open | Runs 24/7 |
| **Metrics** | None | InfluxDB + Grafana |
| **Settings** | Restart required | Live updates |
| **State** | Volatile (lost on restart) | Persistent SQLite |
| **Reminders** | Not supported | Configurable cooldowns |
| **Failure Handling** | Crashes on email/Discord errors | Graceful degradation |

---

## Code Structure

### Core Modules

- **app.py**: Flask application, API endpoints, initialization
- **scanner.py**: HDSentinel execution, parsing, extraction
- **state_tracker.py**: Persistent state, transition detection, cooldowns
- **influx_writer.py**: InfluxDB metrics formatting and writing

### Thread Safety

- Settings updates use `threading.Lock`
- Scan-in-progress flag prevents overlapping scans
- SQLite database with 10s timeout for concurrent access

### Error Handling

- HDSentinel failures: Logged, scan skipped
- Email/Discord failures: Logged, scan continues
- InfluxDB failures: Logged, scan continues
- All exceptions caught and logged (never crashes)

---

## Performance Considerations

- **HDSentinel scan**: ~5-15 seconds (depends on disk count)
- **State database**: Negligible overhead (SQLite, local file)
- **InfluxDB writes**: ~1 second (network call)
- **Flask requests**: <100ms (cached data, no scan)

### Memory Usage

- Flask: ~50 MB
- State tracking: <1 MB
- Full stack (Flask + InfluxDB + Grafana): ~800 MB

---

## Future Enhancements

- [ ] Disk SMART attribute monitoring
- [ ] Predictive failure alerts
- [ ] Multiple alert destination routing
- [ ] Webhook for custom integrations
- [ ] Disk performance trending
- [ ] REST API authentication
- [ ] Multi-system monitoring (agentless)
- [ ] SNMP traps for network integration

---

## License & Support

DiskWarden is provided as-is for self-hosted monitoring.  
No external dependencies beyond open-source software (Flask, InfluxDB, Grafana).

---

## Quick Start

```bash
# Clone and navigate
cd DiskWarden

# Start full stack
docker-compose up -d

# Access UI
http://localhost:7500

# Configure settings
# Go to Settings page, set health threshold, alerts, etc.

# View Grafana dashboards
http://localhost:3000

# Check scanner status
curl http://localhost:7500/api/status
```

Done! DiskWarden is now monitoring your disks in the background.
