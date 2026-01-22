# DiskWarden Deployment Update - Docker Hostname Resolution

## What Changed

Previously, DiskWarden required manual configuration of Docker container IP addresses on Unraid:
1. User had to SSH into Unraid
2. Run `docker inspect` commands to find internal IPs
3. Manually enter these IPs in DiskWarden settings (e.g., `http://172.17.0.2:8086`)
4. Update settings again if containers were recreated

## New Automatic Configuration

DiskWarden now uses **Docker's built-in DNS resolution** to automatically find containers:

### Before (Manual)
```json
{
  "influxUrl": "http://172.17.0.2:8086",
  "grafanaUrl": "http://192.168.0.204:3000"
}
```
❌ Requires manual IP discovery
❌ Breaks when containers are recreated
❌ Confusing which IP to use where

### After (Automatic)
```json
{
  "influxUrl": "http://influxdb:8086",
  "grafanaUrl": "http://192.168.0.204:3000"
}
```
✅ Uses Docker hostnames automatically
✅ Works out-of-the-box
✅ No manual IP discovery needed
✅ Clear separation: internal vs. external URLs

---

## How It Works

### Container-to-Container Communication
When DiskWarden (inside Docker) needs to reach InfluxDB:
```
DiskWarden Container (172.17.0.18)
  → Resolves "influxdb" via Docker DNS (127.0.0.11:53)
  → Gets InfluxDB's internal IP (172.17.0.2)
  → Connects to http://172.17.0.2:8086
```

This resolution happens automatically - **you don't need to configure it**.

### Browser-to-Grafana Access
When you access Grafana from your browser:
```
Your Computer (192.168.0.204)
  → Browser accesses http://192.168.0.204:3000
  → Unraid's port mapping routes to Grafana container
```

This is the **external IP** because your browser can't use Docker's internal DNS.

---

## Configuration

### Default Settings (No Changes Needed)

`settings.json` now ships with hostname-based defaults:

```json
{
  "influxEnabled": true,
  "influxUrl": "http://influxdb:8086",
  "influxToken": "",
  "influxOrg": "diskwarden",
  "influxBucket": "diskwarden",
  "grafanaUrl": "",
  "timezone": "UTC"
}
```

### User Setup

1. **Deploy containers** using docker-compose.yml (with names `influxdb` and `grafana`)
2. **Access DiskWarden** at http://192.168.0.204:7500
3. **Configure Settings:**
   - InfluxDB: Leave default `http://influxdb:8086` (will auto-resolve)
   - Grafana: Set to `http://192.168.0.204:3000` (your external IP)
4. Done! No manual IP discovery needed.

---

## Startup Diagnostics

DiskWarden now provides clear startup messages:

```
Initializing DiskWarden...
Configuration: InfluxDB at http://influxdb:8086, Grafana at http://192.168.0.204:3000
--- External Services Status ---
✓ InfluxDB: Connected (http://influxdb:8086)
  → IMPORTANT: Use 'influxdb' hostname (Docker DNS will resolve it)
✗ Grafana: Connection refused (http://192.168.0.204:3000)
  → Grafana URL is for browser access (192.x address is correct)
  → This check may fail if external IP isn't routable from container
  → Dashboard link will still work from browser - check fails only at startup
--- Starting Services ---
```

**Expected behavior:**
- ✓ InfluxDB succeeds (internal hostname resolves)
- ✗ Grafana fails (external IP not routable from container) - **this is OK**
- ✓ Metrics ARE still written successfully despite Grafana check failure

---

## Documentation Updates

1. **UNRAID_SETUP.md** - Updated deployment guide
   - Removed manual container IP discovery
   - Added hostname-based configuration
   - Kept manual IP option as fallback
   - Clarified external vs. internal URLs

2. **DOCKER_NETWORKING_GUIDE.md** - New comprehensive networking guide
   - Explains Docker internal DNS
   - Shows why external IPs don't work from containers
   - Troubleshooting for hostname resolution failures

3. **README.md** - Updated feature list
   - Added InfluxDB/Grafana capabilities
   - Highlighted Unraid optimization
   - Mentioned automatic hostname resolution

---

## Code Changes

### app.py Improvements

1. **Added hostname resolution helper functions**
   ```python
   def get_container_hostname():
       """Get the hostname of the current container."""
   
   def resolve_hostname(hostname):
       """Resolve hostname to IP address."""
   ```

2. **Updated health check functions**
   - `check_influxdb_connection()` - Now recommends hostname over manual IP
   - `check_grafana_connection()` - Explains external IP behavior
   - Better diagnostic messages for users

3. **Added configuration logging**
   - Startup now shows which URLs are configured
   - Helps users understand the setup

### settings.json Default

- Default `influxUrl` changed from blank to `http://influxdb:8086`
- Enables out-of-the-box functionality for Docker deployments

---

## Backward Compatibility

✅ **Fully backward compatible:**
- Existing manual IP configurations still work
- Users can switch to hostnames anytime by changing settings
- Health checks improved but functionality unchanged
- No breaking changes to API or database

---

## Fallback for Edge Cases

If hostname resolution doesn't work in your Unraid setup:

1. Check container names match exactly (`influxdb` not `influxdb-container`)
2. Verify all containers on same bridge network
3. Manual fallback: Use container IP instead (unchanged from before)
   ```json
   {
     "influxUrl": "http://172.17.0.2:8086"
   }
   ```

---

## Testing

Validate your setup with these checks:

1. **Access DiskWarden Dashboard**
   ```
   http://192.168.0.204:7500 ✅
   ```

2. **Check InfluxDB Metrics**
   ```
   http://192.168.0.204:8086 (or internal IP)
   → Check if disk data is appearing
   ```

3. **Access Grafana Dashboard**
   ```
   http://192.168.0.204:3000 ✅
   ```

4. **Verify DiskWarden Logs**
   ```
   Look for: ✓ InfluxDB: Connected
   Grafana check may fail - this is OK if metrics write successfully
   ```

5. **Check Metrics in InfluxDB**
   ```
   After 2-3 minutes, metrics should appear
   Even if health check failed, they write successfully
   ```

---

## Summary

**Before:** Manual container IP discovery, confusing configuration, fragile setup
**After:** Automatic hostname resolution, out-of-the-box functionality, clear documentation

The system now works correctly with zero manual IP configuration needed!
