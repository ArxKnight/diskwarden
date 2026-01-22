# 🎯 DiskWarden Unified Container - Summary

## What's New

You now have **TWO deployment options**:

### Option 1: Multi-Container (Original)
- **Files**: `dockerfile`, `docker-compose.yml`
- **Services**: DiskWarden, InfluxDB, Grafana (separate containers)
- **Use case**: Production, multiple servers
- **Setup**: `docker-compose up -d`

### Option 2: Unified Container (NEW - Recommended for Unraid)
- **Files**: `dockerfile.unified`, `supervisord.conf`
- **Services**: DiskWarden + InfluxDB + Grafana (one container)
- **Use case**: Unraid, single-box monitoring
- **Setup**: `docker run ... diskwarden:unified`

---

## Build the Unified Image

```bash
cd /mnt/user/appdata/diskwarden

# Build
docker build -t diskwarden:unified -f dockerfile.unified .

# Tag for Docker Hub
docker tag diskwarden:unified arxknight/diskwarden:unified

# Push to Docker Hub
docker push arxknight/diskwarden:unified
```

---

## Deploy on Unraid

### Stop Current Container
```bash
docker stop DiskWarden
docker rm DiskWarden
```

### Run Unified Container
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
  arxknight/diskwarden:unified
```

---

## Access Services

Once running:

- **DiskWarden**: http://192.168.0.204:7500
- **Grafana**: http://192.168.0.204:3000 (admin/admin)
- **InfluxDB**: http://192.168.0.204:8086

All in ONE container! 🎉

---

## How It Works

**supervisord** manages all three services:

```
Container Startup
    ↓
supervisord starts
    ↓
├─ InfluxDB (port 8086)
├─ Grafana (port 3000)
└─ DiskWarden (port 7500)
    ↓
Services communicate via localhost
    ↓
All running! ✓
```

---

## Files Added

1. **dockerfile.unified** - Multi-service Dockerfile
2. **supervisord.conf** - Service configuration
3. **UNIFIED_SETUP.md** - Deployment and setup guide
4. **BUILD_UNIFIED.md** - Build instructions

---

## First Time Setup

See **UNIFIED_SETUP.md** for complete instructions, including:
- Initial InfluxDB configuration
- API token generation
- DiskWarden settings
- Grafana data source setup

---

## Key Benefits

✅ Single container (simpler management)
✅ Works perfectly on Unraid
✅ No docker-compose needed
✅ Shared data volume
✅ All services communicate via localhost
✅ Better resource efficiency
✅ Easier backup/restore

---

## Next Steps

1. Build: `docker build -t diskwarden:unified -f dockerfile.unified .`
2. Stop current container
3. Deploy: Use docker run command above
4. Configure: Follow UNIFIED_SETUP.md
5. Enjoy unified monitoring! 🛡️

---

**Questions?** Check **UNIFIED_SETUP.md** or **BUILD_UNIFIED.md**

Your complete, production-ready, single-container monitoring stack! 🚀
