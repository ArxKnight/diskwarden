# DiskWarden Quick Reference - Docker Setup

## 🚀 Quick Start (Unraid)

### Step 1: Add Containers
- Add `influxdb:2.7-alpine` (Name: `influxdb`, Port: 8086)
- Add `grafana/grafana:latest` (Name: `grafana`, Port: 3000)
- Add `arxknight/diskwarden:v1` (Name: `diskwarden`, Port: 7500)

### Step 2: Access DiskWarden
```
http://192.168.0.204:7500  (use your Unraid IP)
```

### Step 3: Configure Settings
**InfluxDB Settings:**
- URL: `http://influxdb:8086` ← Leave as-is, auto-resolves!
- Organization: `diskwarden`
- Bucket: `diskwarden`
- Token: (leave blank)

**Grafana Settings:**
- URL: `http://192.168.0.204:3000` ← Use your Unraid IP

Click Save → Done!

---

## 📊 Verify It Works

Wait 2-3 minutes, then check:

1. **DiskWarden logs show:**
   ```
   ✓ InfluxDB: Connected (http://influxdb:8086)
   ✗ Grafana: Connection refused  ← OK, this is expected!
   ```

2. **Disks appear on dashboard** ✓

3. **Grafana dashboard has data** 
   - Visit http://192.168.0.204:3000
   - Login: admin / admin
   - Should see disk metrics

---

## 🔧 Troubleshooting

### "InfluxDB: Connection refused"
- **Check container name:** Must be exactly `influxdb` in Unraid
- **Check network:** All containers must be on Bridge network
- **Fallback:** Find container IP: `docker inspect influxdb | grep IPAddress`
  - Then set URL to: `http://172.17.0.2:8086` (use your actual IP)

### "Grafana: Connection refused" 
**This is NORMAL!** External IP not routable from container.
- Metrics still write successfully
- Dashboard link works from browser

### No metrics appearing
- Check InfluxDB health check passes (✓)
- Wait 5 minutes for first metrics
- Check logs for errors

---

## 🌐 Access Your Dashboards

**DiskWarden Main:**
```
http://192.168.0.204:7500
```

**Grafana Visualization:**
```
http://192.168.0.204:3000
```

**InfluxDB Admin:**
```
http://192.168.0.204:8086
```

Replace `192.168.0.204` with your Unraid IP address.

---

## 📝 Container Names Matter!

These exact names must be used in Unraid:
- `influxdb` - Time-series database
- `grafana` - Dashboard visualization  
- `diskwarden` - Health monitoring

**Important:** Don't rename containers, or hostname resolution breaks!

---

## 🔗 Key URLs

| Component | URL | Purpose |
|-----------|-----|---------|
| DiskWarden | `http://192.168.x.x:7500` | Main dashboard |
| Grafana | `http://192.168.x.x:3000` | Visual analytics |
| InfluxDB | `http://192.168.x.x:8086` | Metrics database |

All external IPs in your local network range.

---

## 🐛 Emergency Reset

If something breaks:

1. Delete containers in Unraid Docker
2. Remove volumes if needed (lose historical data)
3. Re-add containers with exact names
4. Deploy again

Default settings will auto-configure with hostname resolution.
