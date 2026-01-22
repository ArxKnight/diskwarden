# DiskWarden on Unraid - Complete Setup Guide

## Container Configuration

DiskWarden consists of **3 separate containers** that must be running together:

### 1. DiskWarden (Main Application)
- **Image**: `arxknight/diskwarden:v1`
- **Port**: 7500
- **Description**: Disk health monitoring service with background scanner

### 2. InfluxDB (Metrics Database)
- **Image**: `influxdb:2.7-alpine`
- **Port**: 8086
- **Description**: Time-series database for storing disk health metrics

### 3. Grafana (Visualization Dashboard)
- **Image**: `grafana/grafana:latest`
- **Port**: 3000
- **Credentials**: admin / admin
- **Description**: Visual dashboard for displaying metrics

---

## Step 1: Add InfluxDB Container (in Unraid)

1. Go to **Docker** section in Unraid
2. Click **Add Container**
3. Configure:
   - **Repository**: `influxdb:2.7-alpine`
   - **Name**: `influxdb`
   - **Port Mapping**: `8086:8086`
   - **Environment Variables**:
     ```
     INFLUXDB_DB=diskwarden
     INFLUXDB_ADMIN_USER=admin
     INFLUXDB_ADMIN_PASSWORD=changeme
     INFLUXDB_HTTP_AUTH_ENABLED=false
     ```
   - **Network**: Bridge

4. Click **Apply** and start the container

---

## Step 2: Add Grafana Container (in Unraid)

1. Go to **Docker** section in Unraid
2. Click **Add Container**
3. Configure:
   - **Repository**: `grafana/grafana:latest`
   - **Name**: `grafana`
   - **Port Mapping**: `3000:3000`
   - **Environment Variables**:
     ```
     GF_SECURITY_ADMIN_USER=admin
     GF_SECURITY_ADMIN_PASSWORD=admin
     GF_INSTALL_PLUGINS=grafana-pie-chart-panel,grafana-worldmap-panel
     GF_USERS_ALLOW_SIGN_UP=false
     ```
   - **Network**: Bridge

4. Click **Apply** and start the container

---

## Step 3: Configure DiskWarden Container

1. Go to **Docker** section in Unraid
2. Click **Edit** on the DiskWarden container
3. Configure:
   - **Repository**: `arxknight/diskwarden:v1`
   - **Name**: `diskwarden`
   - **Port Mapping**: `7500:7500`
   - **Network**: Bridge
   - **Extra Parameters**: `--privileged -v /dev:/dev`

---

## Step 4: Auto-Configuration (Recommended - No Manual IP Discovery Needed!)

**NEW**: DiskWarden now supports Docker hostname resolution automatically!

The containers communicate using Docker's internal DNS:
- `influxdb` hostname automatically resolves to the InfluxDB container's internal IP
- `grafana` hostname automatically resolves to the Grafana container's internal IP
- You do NOT need to manually discover container IPs anymore

The default configuration is:
- **InfluxDB URL**: `http://influxdb:8086` (will auto-resolve)
- **Grafana URL**: Set to your external Unraid IP (e.g., `http://192.168.0.204:3000`)

This means:
✓ Metrics automatically write to InfluxDB using internal Docker DNS
✓ Dashboard link works from your browser using external IP
✓ No manual container IP discovery needed
✓ Configuration works out-of-the-box after container setup

---

## Step 5 (OPTIONAL): Manual Container IP Configuration

If hostname resolution doesn't work in your Unraid setup, you can still manually configure container IPs:

### Get Container IPs via SSH/Terminal:
```bash
docker inspect influxdb | grep IPAddress
docker inspect grafana | grep IPAddress
docker inspect diskwarden | grep IPAddress
```

Example output:
```
influxdb IP: 172.17.0.2
grafana IP: 172.17.0.3
diskwarden IP: 172.17.0.18
```

Then update settings with these IPs instead of hostnames.

---

## Step 6: Configure DiskWarden Settings

1. Access DiskWarden at: `http://YOUR_UNRAID_IP:7500`
2. Click **Settings** in the navigation menu
3. Configure:

### InfluxDB Settings
- **Enable InfluxDB Metrics**: Toggle ON
- **InfluxDB URL**: `http://influxdb:8086` (default - will auto-resolve)
  - Alternative (if above fails): Use container IP like `http://172.17.0.2:8086`
- **InfluxDB API Token**: Leave blank (local setup)
- **Organization**: `diskwarden`
- **Bucket**: `diskwarden`
- Click **Save InfluxDB Settings**

### Grafana Settings
- **Grafana URL**: `http://YOUR_UNRAID_IP:3000`
  - Use your EXTERNAL Unraid IP address
  - Example: `http://192.168.0.204:3000`
- Click **Save Grafana Settings**

---

## Step 7: Verify Configuration

Check DiskWarden logs for:

```
--- External Services Status ---
✓ InfluxDB: Connected (http://influxdb:8086)
  → OR if using manual IP: ✓ InfluxDB: Connected (http://172.17.0.2:8086)
✗ Grafana: Connection refused (http://192.168.0.204:3000)
  → This is NORMAL - external IP isn't routable from inside container
  → Grafana dashboard link still works from your browser
--- Starting Services ---
```

**Expected behavior:**
- ✓ InfluxDB connection should succeed (using internal hostname or IP)
- ✗ Grafana connection may fail (external IP not routable from container)
- ✓ But metrics ARE being written to InfluxDB despite Grafana check failure

---

## Step 8: Verify Metrics Are Being Recorded

1. Wait 2-3 minutes for data collection
2. Access InfluxDB UI directly: `http://192.168.0.204:8086`
3. Look for `diskwarden` bucket with disk health data
4. In Grafana: `http://192.168.0.204:3000` - dashboard should populate with metrics

---

## Troubleshooting

### "Still can't connect to InfluxDB"
1. Find correct container IP: `docker inspect influxdb | grep IPAddress`
2. Test from DiskWarden container:
   ```bash
   docker exec diskwarden curl http://172.17.x.x:8086/health
   ```
   Should return 200 status
3. Update settings with correct IP and save

### "Metrics not appearing in Grafana"
1. Verify InfluxDB URL uses internal IP (step 5)
2. Check logs: `InfluxDB configured: http://172.17.x.x:8086` ✓
3. Run manual scan in DiskWarden UI
4. Wait 30+ seconds for metrics to write
5. Refresh Grafana dashboard

### "Grafana navbar link works from browser but not accessible"
- This is expected! Browser accesses external IP, container cannot
- Metrics still work because they use internal IP
- Link in navbar is just for convenience - all functionality works

---

## Quick Reference - Important Points

| Setting | Unraid Container Network | Explanation |
|---------|-------------------------|-------------|
| InfluxDB URL | `http://172.17.0.2:8086` | Use INTERNAL container IP (find with docker inspect) |
| Grafana URL (Navbar) | `http://192.168.0.204:3000` | Use EXTERNAL IP for browser access |
| Metrics Writing | Works with internal IP | Happens automatically during scans |
| Health Checks | May fail with external IP | But metrics writing still succeeds |

---

## Alternative: Use Docker Compose (Easier)

If you have access to Unraid's stack/compose feature, you can deploy all three containers at once:

```yaml
version: '3.8'
services:
  diskwarden:
    image: arxknight/diskwarden:v1
    ports:
      - "7500:7500"
    environment:
      DISKWARDEN_SCANNER: "1"
    volumes:
      - /dev:/dev
  
  influxdb:
    image: influxdb:2.7-alpine
    ports:
      - "8086:8086"
    environment:
      INFLUXDB_DB: diskwarden
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: admin
```

Then configure InfluxDB URL as: `http://influxdb:8086` (hostnames work in compose)



---

## Quick Reference - Port Mapping Summary

| Service | Host Port | Container Port | URL |
|---------|-----------|----------------|-----|
| DiskWarden | 7500 | 7500 | http://192.168.0.204:7500 |
| Grafana | 3000 | 3000 | http://192.168.0.204:3000 |
| InfluxDB | 8086 | 8086 | http://192.168.0.204:8086 |

All three must be accessible from your network for full functionality.
