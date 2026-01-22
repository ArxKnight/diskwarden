# Quick Start - DiskWarden Service-Driven Refactoring

## What Changed (TL;DR)

| Aspect | Before | After |
|--------|--------|-------|
| **Scanning** | Triggered by UI requests | Runs in background every 60s |
| **Alerts** | Sent every request | Only on state transitions |
| **State** | Lost on restart | Persistent SQLite DB |
| **Metrics** | None | InfluxDB + Grafana (optional) |
| **Availability** | When UI accessed | 24/7 autonomous |

---

## Files Overview

### Core Application
- **app.py** - Flask API + background scheduler (refactored)
- **scanner.py** - HDSentinel execution (NEW)
- **state_tracker.py** - Persistent state & alert suppression (NEW)
- **influx_writer.py** - Metrics storage (NEW)

### Configuration
- **settings.json** - Extended with new options (updated)
- **requirements.txt** - Added dependencies (updated)

### UI Templates
- **templates/index.html** - Dashboard (updated: removed auto-scan)
- **templates/settings.html** - Settings page (updated: new controls)

### Deployment
- **dockerfile** - Same, with notes on `DISKWARDEN_SCANNER` env var
- **docker-compose.yml** - Full stack (NEW)
- **DEPLOYMENT.md** - Complete guide (NEW)
- **CHANGES.md** - Detailed changelog (NEW)
- **README.md** - This file

---

## Installation & Deployment

### Option 1: Docker Compose (Full Stack - Recommended)

```bash
# Start all services (DiskWarden + InfluxDB + Grafana)
docker-compose up -d

# Access:
# - DiskWarden: http://localhost:7500
# - Grafana: http://localhost:3000 (admin/admin)
# - InfluxDB: http://localhost:8086
```

### Option 2: Docker (Single Container)

```bash
# Build
docker build -t diskwarden .

# Run with background scanner
docker run -d \
  --name diskwarden \
  -p 7500:7500 \
  -e DISKWARDEN_SCANNER=1 \
  -v $(pwd)/settings.json:/app/settings.json \
  -v $(pwd)/diskwarden_state.db:/app/diskwarden_state.db \
  diskwarden:latest
```

### Option 3: Standalone (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run with background scanner
DISKWARDEN_SCANNER=1 python3 app.py

# Or UI-only mode (manual scans only)
DISKWARDEN_SCANNER=0 python3 app.py
```

---

## Key Features

### 1. Background Scanning
- Runs every `scanIntervalSeconds` (default: 60)
- Enabled via `DISKWARDEN_SCANNER=1` environment variable
- Continues running even if UI is closed
- No duplicate scans in multi-worker setups

### 2. Alert Suppression
- **Transition alerts**: Only sent when health crosses threshold
- **Recovery alerts**: Optional (`notifyOnRecovery: true`)
- **Reminder alerts**: Periodic reminders (`alertCooldownMinutes: 30`)
- State tracked in SQLite: `diskwarden_state.db`

### 3. Metrics (Optional)
- Enable in Settings → InfluxDB & Grafana section
- Data points: health%, temperature, power-on hours, lifetime
- Visualize in Grafana dashboards
- Self-hosted, no cloud dependencies

### 4. Live Configuration
- Change settings → Takes effect immediately
- Scan interval adjusts dynamically
- No restart needed

---

## Configuration

### Basic Settings (minimum required)

```json
{
  "healthThreshold": 90,
  "scanIntervalSeconds": 60,
  "notifyOnRecovery": false,
  "alertCooldownMinutes": 0
}
```

### With Discord & Email

```json
{
  "webhookUrl": "https://discord.com/api/webhooks/...",
  "email": "alerts@example.com",
  "emailPassword": "app-password-here",
  "smtpServer": "smtp.gmail.com",
  "smtpPort": 587,
  "healthThreshold": 90,
  "scanIntervalSeconds": 60,
  "notifyOnRecovery": true,
  "alertCooldownMinutes": 30
}
```

### With InfluxDB & Grafana

```json
{
  "influxEnabled": true,
  "influxUrl": "http://influxdb:8086",
  "influxToken": "YOUR_TOKEN_HERE",
  "influxOrg": "diskwarden",
  "influxBucket": "diskwarden",
  "grafanaUrl": "http://grafana:3000"
}
```

---

## API Endpoints

### Dashboard Data
```bash
# Get last cached scan results
GET /api/disk_health
# Response: [disk1, disk2, ...]

# Trigger immediate scan
POST /api/scan_now
# Response: { message, last_scan, disk_count }

# Get scanner status
GET /api/status
# Response: { last_scan, next_scan, scanner_running, disks_below_threshold, ... }
```

### Configuration
```bash
# Get current settings
GET /api/settings

# Update settings (merged with existing)
POST /api/settings
# Body: { "scanIntervalSeconds": 120, "notifyOnRecovery": true, ... }

# Test email
POST /api/test_email
# Body: { "email": "...", "smtpServer": "...", ... }

# Test Discord
POST /api/test_message
# Body: { "webhookUrl": "..." }
```

---

## State Tracking Examples

### Example 1: Simple Alert

```
Time: 12:00 - Disk health: 85% (threshold: 90%)
  Old state: OK
  New state: BELOW_THRESHOLD
  Alert: ⚠️ Disk Health Alert
  Action: Send Discord + Email

Time: 12:01 - Disk health: 84%
  State: BELOW_THRESHOLD (no change)
  Alert: None (same state)
```

### Example 2: With Recovery Alert

```
Settings: notifyOnRecovery=true

Time: 12:00 - Health: 85% → BELOW_THRESHOLD
  Alert: ⚠️ Disk Health Alert

Time: 12:05 - Health: 92% → OK
  Alert: ✅ Disk Recovered

Time: 12:06 - Health: 88% → BELOW_THRESHOLD
  Alert: ⚠️ Disk Health Alert (new transition)
```

### Example 3: With Reminder Alerts

```
Settings: alertCooldownMinutes=30

Time: 12:00 - Health: 85% → BELOW_THRESHOLD
  Alert: ⚠️ Disk Health Alert
  last_alert_time: 12:00

Time: 12:15 - Health: 85% (no change)
  Cooldown: 15 minutes elapsed (< 30)
  Alert: None

Time: 12:30 - Health: 85% (no change)
  Cooldown: 30 minutes elapsed (>= 30)
  Alert: 🔔 Disk Health Reminder
  last_alert_time: 12:30 (reset)

Time: 13:00 - Health: 85% (no change)
  Cooldown: 30 minutes elapsed again
  Alert: 🔔 Disk Health Reminder
```

---

## Monitoring

### View Logs

**Docker**:
```bash
docker logs diskwarden -f
```

**Docker Compose**:
```bash
docker-compose logs diskwarden -f
```

**Standalone**:
```
Console output directly (Flask + logging)
```

### Key Log Messages

```
INFO - Initializing DiskWarden...
INFO - Starting background scanner (interval: 60s)
INFO - Starting disk scan...
INFO - Disk scan complete: 3 disks
INFO - Sending alert for disk ABC123XYZ: transition
DEBUG - Email sent to user@example.com
DEBUG - Discord notification sent
INFO - Wrote 3 disk metrics to InfluxDB
```

### Database Inspection

```bash
# List all disk states
sqlite3 diskwarden_state.db "SELECT disk_id, state, health_percent FROM disk_state;"

# Check alert cooldown times
sqlite3 diskwarden_state.db "SELECT disk_id, last_alert_time FROM disk_state WHERE state='BELOW_THRESHOLD';"

# View schema
sqlite3 diskwarden_state.db ".schema disk_state"
```

---

## Troubleshooting

### "No scan data available"
- **Cause**: Scanner hasn't run yet
- **Fix**: Wait for first scan, or click "Scan Now" button

### "Scanner not running"
- **Check**: `docker inspect diskwarden | grep DISKWARDEN_SCANNER`
- **Fix**: Ensure `DISKWARDEN_SCANNER=1` is set

### Alerts not being sent
1. Verify scanner is running: `/api/status`
2. Check alert settings match expectations
3. Verify state transitions: `sqlite3 diskwarden_state.db "SELECT * FROM disk_state;"`
4. Test Discord/email manually via Settings page
5. Check logs: `docker logs diskwarden`

### InfluxDB metrics not appearing
1. Verify enabled: Settings → InfluxDB & Grafana section
2. Check token is correct and has write permissions
3. Verify URL is reachable from container
4. Check logs for write errors

---

## Environment Variables

```bash
DISKWARDEN_SCANNER=1    # Enable background scanner (production)
DISKWARDEN_SCANNER=0    # Disable (UI-only mode for testing)
```

---

## Health Check (for orchestration)

```bash
# Check if API is responding
curl http://localhost:7500/api/status

# Expected response:
{
  "last_scan": "2026-01-22T14:30:45.123456",
  "scanner_running": true,
  ...
}
```

---

## Safe Shutdown

```bash
# Docker
docker stop diskwarden

# Docker Compose
docker-compose down

# Standalone (Ctrl+C)
# Logs: "Shutting down..."
```

---

## Performance Notes

- **Scan time**: 5-15 seconds (depends on disk count)
- **Cycle overhead**: <2 seconds (alerts + metrics)
- **Memory usage**: ~50 MB Flask + ~1 MB state
- **Disk I/O**: Minimal (local SQLite only)

---

## Next Steps

1. **Deploy**: Run `docker-compose up -d`
2. **Access UI**: Open http://localhost:7500
3. **Configure**:
   - Set health threshold
   - Add Discord webhook (or email)
   - Optionally enable InfluxDB metrics
4. **Test**:
   - Click "Scan Now" button
   - Verify alerts work
   - Check `/api/status` endpoint
5. **Monitor**:
   - View logs: `docker logs diskwarden -f`
   - Access Grafana: http://localhost:3000

---

## Documentation

For detailed information, see:
- **DEPLOYMENT.md** - Full architecture and configuration guide
- **CHANGES.md** - Detailed changelog and technical overview

---

## Support

This is a self-contained project with no external dependencies beyond open-source libraries. Refer to the code comments and documentation for technical details.

Good luck monitoring your disks! 🚀
