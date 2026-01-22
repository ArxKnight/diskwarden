# Building the Unified DiskWarden Container

Two files are now available:

## 1. **dockerfile** (Original - Multi-container)
- Runs only DiskWarden
- Use with `docker-compose.yml` for full stack
- For users who want separate containers

## 2. **dockerfile.unified** (NEW - Single container)
- Runs DiskWarden + InfluxDB + Grafana
- All in one container via supervisord
- Recommended for Unraid deployment

---

## Build the Unified Image

### Quick Build

```bash
cd /mnt/user/appdata/diskwarden
docker build -t diskwarden:unified -f dockerfile.unified .
```

### Build and Push to Docker Hub

```bash
# Build
docker build -t diskwarden:unified -f dockerfile.unified .

# Tag
docker tag diskwarden:unified arxknight/diskwarden:unified

# Push
docker push arxknight/diskwarden:unified
```

---

## Run Unified Container

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

---

## File Descriptions

### dockerfile.unified
- Installs Ubuntu 20.04 base
- Installs supervisord to manage services
- Downloads and installs InfluxDB 2.7
- Downloads and installs Grafana 10.0
- Copies DiskWarden code
- Copies supervisord.conf
- Starts all services on container startup

### supervisord.conf
- Configures InfluxDB service (priority 10)
- Configures Grafana service (priority 20)
- Configures DiskWarden service (priority 30)
- All services auto-restart on failure
- Logs to `/var/log/`

---

## What's Next?

1. Build the image
2. Run the container
3. Follow [UNIFIED_SETUP.md](UNIFIED_SETUP.md) for first-time configuration
4. Access dashboards at ports 7500, 3000, 8086

---

## Comparison

| Feature | Multi-Container (docker-compose) | Unified Container |
|---------|----------------------------------|-------------------|
| **Complexity** | 3 separate containers | 1 container |
| **Networking** | Docker network DNS | Localhost only |
| **Deployment** | docker-compose up | docker run |
| **Storage** | 3 separate volumes | 1 shared volume |
| **Memory** | ~400MB total | ~300MB total |
| **Startup time** | ~10-15s | ~10-15s |
| **Unraid friendly** | Moderate | Excellent |
| **Recommended** | Production multi-node | Unraid single-box |

---

Choose based on your needs!
