# DiskWarden Docker Networking Guide

## How Container Communication Works

### The Problem
DiskWarden, InfluxDB, and Grafana are separate Docker containers. They need to communicate, but Docker bridge networks have special networking rules.

### The Solution: Docker Internal DNS

When containers run on Docker's bridge network, Docker provides an **internal DNS server** at `127.0.0.11:53` that automatically resolves container names to their internal IPs.

**This means:**
- Container name `influxdb` automatically resolves to the InfluxDB container's internal IP (e.g., `172.17.0.2`)
- Container name `grafana` automatically resolves to the Grafana container's internal IP (e.g., `172.17.0.3`)
- You **don't need to manually discover or configure container IPs**

### Configuration

In DiskWarden settings:

**InfluxDB URL**: `http://influxdb:8086`
- Uses Docker's internal DNS to communicate with InfluxDB container
- Works automatically without manual IP discovery
- This URL is only valid from INSIDE containers

**Grafana URL**: `http://192.168.0.204:3000` (your external Unraid IP)
- This is for the browser dashboard link in DiskWarden's navbar
- Use your EXTERNAL IP address because it's accessed from your computer, not from inside the container
- Users click this link from their browser

---

## Why Both URLs Are Different

```
DiskWarden (inside container) → InfluxDB
    Uses: http://influxdb:8086 (internal Docker DNS)
    Why: Containers can only reach each other via internal hostnames

Browser (on your computer) → Grafana Dashboard  
    Uses: http://192.168.0.204:3000 (external IP)
    Why: Your browser can't resolve Docker hostnames; uses external address instead
```

---

## Startup Logs Explained

When DiskWarden starts, you'll see:

```
Configuration: InfluxDB at http://influxdb:8086, Grafana at http://192.168.0.204:3000
--- External Services Status ---
✓ InfluxDB: Connected (http://influxdb:8086)
  → IMPORTANT: Use 'influxdb' hostname (Docker DNS will resolve it)
✗ Grafana: Connection refused (http://192.168.0.204:3000)
  → This is EXPECTED - external IP isn't routable from inside container
```

**This is NORMAL and expected:**

1. ✓ **InfluxDB check succeeds** - Container can reach InfluxDB using internal Docker DNS
2. ✗ **Grafana check fails** - External IP isn't routable from inside container (this is expected and OK)
3. ✓ **Metrics still write successfully** - Using the same internal connection that passed the health check

---

## Troubleshooting

### If InfluxDB connection still fails

Try one of these approaches:

**Option A: Manual Container IP (if hostname doesn't work)**
```bash
# Find container IPs
docker inspect influxdb | grep IPAddress
# Example output: "IPAddress": "172.17.0.2"

# Use this IP in settings instead of hostname
# InfluxDB URL: http://172.17.0.2:8086
```

**Option B: Check container names match exactly**
- Container name must be exactly `influxdb` (not `influxdb-container` or similar)
- Check Unraid Docker settings

**Option C: Check network is Bridge mode**
- All three containers must be on the same bridge network
- Verify in Unraid Docker settings

---

## Advanced: Why External IPs Don't Work From Containers

In a Docker bridge network:

```
┌─────────────────────┐
│  Host Computer      │
│  192.168.0.204      │
└─────────────────────┘
         ↕ (Docker networking)
┌─────────────────────┐
│  Docker Bridge Net  │
│  172.17.x.x IPs     │
├─────────────────────┤
│ DiskWarden Container│
│   172.17.0.18       │
├─────────────────────┤
│ InfluxDB Container  │
│   172.17.0.2        │
└─────────────────────┘
```

When you access DiskWarden from your browser at `192.168.0.204:7500`, the request comes from your computer through Docker's network port mapping.

BUT when DiskWarden tries to access something at `192.168.0.204:3000` (external IP):
- DiskWarden is INSIDE the container network (172.17.x.x)
- External IP `192.168.0.204` isn't routable from inside the container
- The packet gets lost

**Solution:** Use internal container hostnames/IPs for inter-container communication.

---

## Summary

✓ **Metrics Collection**: DiskWarden → InfluxDB uses `http://influxdb:8086` (auto-resolves)
✓ **Dashboard Link**: Browser → Grafana uses `http://192.168.0.204:3000` (external IP)
✓ **No Manual Configuration**: Docker DNS handles hostname resolution automatically
✓ **Out-of-the-Box**: Default settings work without any manual IP discovery

Your setup is working correctly if you see:
- InfluxDB health check: ✓ Connected
- Grafana health check: ✗ Connection refused (expected - this is OK!)
- Dashboard loads successfully in browser
- Metrics appear in InfluxDB/Grafana after a few minutes
