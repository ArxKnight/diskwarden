# DiskWarden Unified Container Setup (Single Container Stack)

This setup runs DiskWarden, InfluxDB, and Grafana all in ONE container using supervisord.

---

## Quick Deploy on Unraid

### Step 1: Build or Pull the Image

Option A - Pull from Docker Hub:
```bash
docker pull arxknight/diskwarden:unified
```

Option B - Build locally:
```bash
cd /mnt/user/appdata/diskwarden
docker build -t diskwarden:unified -f dockerfile.unified .
```

---

### Step 2: Run the Container

Using Unraid Docker interface **OR** SSH/Terminal:

```bash
docker run -d \
  --name='DiskWarden-Stack' \
  --privileged=true \
  -p 7500:7500 \
  -p 8086:8086 \
  -p 3000:3000 \
  -v '/dev:/dev' \
  -v '/mnt/user/appdata/diskwarden/config:/config' \
  -v '/mnt/user/appdata/diskwarden/data:/data' \
  -e TZ='UTC' \
  diskwarden:unified
```

**Explanation:**
- `--privileged=true` - Access to disk devices for HDSentinel
- `-p 7500:7500` - DiskWarden dashboard
- `-p 8086:8086` - InfluxDB metrics
- `-p 3000:3000` - Grafana visualization
- `-v /dev:/dev` - Required for disk health monitoring
- `-v /mnt/user/appdata/diskwarden/config:/config` - Configuration persistence
- `-v /mnt/user/appdata/diskwarden/data:/data` - Data persistence (metrics, Grafana data)

---

## Access Your Services

Once running:

1. **DiskWarden Dashboard**
   - URL: `http://192.168.0.204:7500`
   - View disk health and configure alerts

2. **Grafana Visualization**
   - URL: `http://192.168.0.204:3000`
   - Username: `admin`
   - Password: `admin`

3. **InfluxDB Admin**
   - URL: `http://192.168.0.204:8086`
   - Metrics database (no auth configured)

---

## First Time Setup

### 1. Wait for Services to Start

All three services start automatically. Wait 10-15 seconds for full initialization.

Check container logs:
```bash
docker logs DiskWarden-Stack -f
```

You should see:
```
influxdb | INFO: started HTTP service
grafana | ready to accept connections
DiskWarden | Starting Flask server on 0.0.0.0:7500
```

### 2. Configure InfluxDB (First Time Only)

InfluxDB 2.7 requires initial setup:

1. Go to http://192.168.0.204:8086
2. Click "Get Started"
3. Configure:
   - Username: `admin`
   - Password: Create a strong password
   - Organization: `diskwarden`
   - Bucket: `diskwarden`
4. Copy the API token (you'll need it)

### 3. Create InfluxDB API Token for DiskWarden

In InfluxDB Admin:
1. Click "API Tokens" (left sidebar)
2. Click "Generate" → "All Access API Token"
3. Name: `diskwarden-token`
4. Copy the token

### 4. Configure DiskWarden

1. Go to http://192.168.0.204:7500
2. Click "Settings"
3. InfluxDB section:
   - **Enable InfluxDB**: Toggle ON
   - **URL**: `http://localhost:8086` (internal localhost)
   - **API Token**: Paste the token from step 3
   - **Organization**: `diskwarden`
   - **Bucket**: `diskwarden`
4. Save

### 5. Wait for Metrics

After 2-3 minutes, metrics start flowing:
- Check Grafana: http://192.168.0.204:3000
- Dashboard should show disk health data
- InfluxDB should have measurements

---

## Upgrades & Restarts

### Restart Container

```bash
docker restart DiskWarden-Stack
```

### Update Image

```bash
# Pull latest
docker pull arxknight/diskwarden:unified

# Stop old container
docker stop DiskWarden-Stack

# Remove old container
docker rm DiskWarden-Stack

# Run with new image (use same docker run command as above)
docker run -d ...
```

Your data in `/data` persists across restarts and updates!

---

## Backup & Restore

### Backup

```bash
# Backup config and data
tar czf diskwarden-backup.tar.gz /mnt/user/appdata/diskwarden/

# Or via Unraid Backup tool
```

### Restore

```bash
# Extract backup
tar xzf diskwarden-backup.tar.gz -C /

# Restart container
docker restart DiskWarden-Stack
```

---

## Troubleshooting

### Services Won't Start

Check logs:
```bash
docker logs DiskWarden-Stack -f
```

Look for:
- `ERROR` messages
- Port conflicts (try different ports)
- Permission issues

### InfluxDB Won't Initialize

Try resetting:
```bash
# Stop container
docker stop DiskWarden-Stack

# Delete InfluxDB data
rm -rf /mnt/user/appdata/diskwarden/data/influxdb/*

# Restart
docker start DiskWarden-Stack

# Reconfigure InfluxDB from scratch
```

### Grafana Won't Show Metrics

1. Check InfluxDB is running: `http://192.168.0.204:8086`
2. Check data source in Grafana:
   - Settings → Data Sources
   - Should show `InfluxDB` pointing to `http://localhost:8086`
3. Check API token is correct in DiskWarden settings

### DiskWarden Won't Connect

- Wait 15 seconds for InfluxDB to start
- Check DiskWarden logs: `docker logs DiskWarden-Stack | grep DiskWarden`
- Verify InfluxDB token is correct

---

## Performance Notes

- All three services run in single container
- Uses ~300-400MB RAM
- ~5-10% CPU average
- Data volumes can grow to several GB per year

---

## Directory Structure

```
/mnt/user/appdata/diskwarden/
├── config/              # Configuration files
│   └── (empty - for future use)
└── data/
    ├── influxdb/        # InfluxDB database
    │   ├── influxd.bolt
    │   └── engine/
    └── grafana/         # Grafana data
        ├── plugins/
        └── storage/
```

---

## Monitoring the Stack

### View Service Status

```bash
# Check if container is running
docker ps | grep DiskWarden-Stack

# View all logs
docker logs DiskWarden-Stack -f

# View specific service logs
docker exec DiskWarden-Stack tail -f /var/log/diskwarden.out.log
docker exec DiskWarden-Stack tail -f /var/log/influxdb.out.log
docker exec DiskWarden-Stack tail -f /var/log/grafana.out.log
```

### Check Supervisor Status (Inside Container)

```bash
docker exec DiskWarden-Stack supervisorctl status
```

Should show all three services running:
```
influxdb                         RUNNING   pid 12, uptime 0:05:23
grafana                          RUNNING   pid 34, uptime 0:05:20
diskwarden                       RUNNING   pid 56, uptime 0:05:18
```

---

## Architecture

```
┌─────────────────────────────────────┐
│   DiskWarden-Stack Container        │
│   (Single Docker Container)         │
├─────────────────────────────────────┤
│  InfluxDB (port 8086)               │
│  └─ Stores metrics in /data/        │
├─────────────────────────────────────┤
│  Grafana (port 3000)                │
│  └─ Visualizes InfluxDB data        │
├─────────────────────────────────────┤
│  DiskWarden (port 7500)             │
│  └─ Reads disks, writes metrics     │
├─────────────────────────────────────┤
│  Supervisord                        │
│  └─ Manages all services            │
└─────────────────────────────────────┘
```

All services communicate via `localhost` inside the container!

---

## Why Single Container?

✅ **Simpler deployment** - One container to manage
✅ **Easier backup/restore** - Single data volume
✅ **Lower overhead** - Shared base image, no inter-container networking
✅ **Unraid friendly** - Works with bridge network
✅ **Better integration** - Services use localhost
✅ **Faster startup** - All services in parallel

---

## Summary

That's it! You now have a single container running DiskWarden, InfluxDB, and Grafana. Everything works together automatically with no docker-compose needed.

Questions? Check the logs: `docker logs DiskWarden-Stack -f`
