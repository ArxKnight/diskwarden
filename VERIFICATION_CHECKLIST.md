# DiskWarden Deployment Verification Checklist

## ✅ Pre-Deployment Checklist

### Container Setup
- [ ] InfluxDB container created with name `influxdb` (exact match)
- [ ] Grafana container created with name `grafana` (exact match)
- [ ] DiskWarden container created with name `diskwarden` (exact match)
- [ ] All containers on Bridge network (verify in Unraid)
- [ ] All containers are RUNNING (check Unraid Docker panel)

### Port Mappings
- [ ] InfluxDB: Port 8086 mapped
- [ ] Grafana: Port 3000 mapped
- [ ] DiskWarden: Port 7500 mapped

### DiskWarden Container
- [ ] Mounted with `--privileged` flag
- [ ] Mounted with `-v /dev:/dev` flag
- [ ] Environment variable `TZ=UTC` set
- [ ] Environment variable `DISKWARDEN_SCANNER=1` set

---

## ✅ Post-Deployment Checklist

### Access Points
- [ ] Can access DiskWarden dashboard: `http://192.168.x.x:7500`
- [ ] Can access Grafana dashboard: `http://192.168.x.x:3000`
- [ ] Can access InfluxDB: `http://192.168.x.x:8086`

### DiskWarden Settings
- [ ] InfluxDB URL set to: `http://influxdb:8086` (hostname, not IP)
- [ ] InfluxDB Enabled: Toggle ON
- [ ] InfluxDB Organization: `diskwarden`
- [ ] InfluxDB Bucket: `diskwarden`
- [ ] Grafana URL set to external IP (e.g., `http://192.168.x.x:3000`)
- [ ] Settings Saved successfully

### DiskWarden Dashboard
- [ ] Disks are displayed
- [ ] Health percentages showing
- [ ] Temperature data visible
- [ ] Last scan time displays (e.g., "Last scan: 2 minutes ago")
- [ ] Grafana link appears in navbar (when Grafana URL configured)

### Startup Logs
- [ ] Check Docker logs for DiskWarden container
- [ ] Should see: `✓ InfluxDB: Connected (http://influxdb:8086)`
- [ ] OK to see: `✗ Grafana: Connection refused` (expected)
- [ ] Should see: `Configuration: InfluxDB at http://influxdb:8086`

---

## ✅ Metrics Verification (Wait 2-3 Minutes)

### InfluxDB
- [ ] Visit `http://192.168.x.x:8086`
- [ ] Navigate to Data Explorer
- [ ] See bucket: `diskwarden`
- [ ] Disk health data appears in measurements
- [ ] Metrics have recent timestamps

### Grafana  
- [ ] Visit `http://192.168.x.x:3000`
- [ ] Login with `admin` / `admin`
- [ ] Navigate to Dashboards
- [ ] "DiskWarden" dashboard exists
- [ ] Dashboard displays disk metrics
- [ ] Graphs show recent data points
- [ ] No "no data" messages

---

## ✅ Alerting Verification

### Discord Webhook (if configured)
- [ ] Webhook URL set in Settings
- [ ] Test by dropping a disk below threshold
- [ ] Check if notification sent to Discord

### Email Alerts (if configured)
- [ ] SMTP server configured
- [ ] Test by setting threshold very high
- [ ] Check if alert email received

### Per-Disk Disabling
- [ ] Settings → Disable alerts for specific disks
- [ ] USB drives (showing 0% health) can be disabled
- [ ] No false alerts for disabled disks

---

## ✅ Advanced Verification

### Container Networking
Test from Unraid terminal:
```bash
# Check container names resolve
docker exec diskwarden ping -c 1 influxdb
# Should succeed

# Check metrics were written
docker exec influxdb curl -s localhost:8086/api/v1/buckets
# Should show diskwarden bucket
```

### Manual Container IP Discovery (Fallback)
If hostnames don't resolve:
```bash
# Find container IPs
docker inspect influxdb | grep IPAddress
docker inspect grafana | grep IPAddress

# Update settings with IPs instead of hostnames
# InfluxDB URL: http://172.17.0.2:8086 (example IP)
```

### Logs Analysis
```bash
# Check DiskWarden logs
docker logs diskwarden | grep -E "InfluxDB|Grafana|Configuration"

# Should show:
# - Configuration: InfluxDB at http://influxdb:8086
# - ✓ InfluxDB: Connected
# - Metrics writing messages
```

---

## 🐛 If Something's Wrong

### DiskWarden Dashboard Won't Load
1. Check container is running: `docker ps | grep diskwarden`
2. Check port mapping: Verify 7500 mapped in Unraid
3. Try different port or restart container
4. Check logs: `docker logs diskwarden`

### InfluxDB Connection Fails
1. Verify container name is exactly `influxdb` (case-sensitive on Linux)
2. Check containers on same bridge network
3. Try manual IP: Find with `docker inspect influxdb`
4. Add to firewall exceptions if needed

### Grafana Dashboard Empty
1. Wait at least 3 minutes for metrics to collect
2. Verify Grafana datasource points to: `http://influxdb:8086`
3. Login to Grafana, check Data Sources
4. Manually query InfluxDB to verify data exists

### Settings Won't Save
1. Check file permissions on settings.json
2. Check disk space on Unraid
3. Restart DiskWarden container
4. Check logs for write errors

---

## 📝 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't find InfluxDB at hostname | Container name wrong | Verify name is exactly `influxdb` |
| Health check fails but metrics write | External IP not routable | Expected! Check metrics in InfluxDB |
| No disks showing on dashboard | HDSentinel not found | Ensure container has privileged + /dev mount |
| Grafana shows "no data" | Metrics not collected yet | Wait 3-5 minutes, check InfluxDB directly |
| Settings not persisting | Permission issue | Check container volume mounts |

---

## ✅ Success Indicators

Your deployment is working correctly if you see ALL of these:

1. ✓ DiskWarden dashboard loads and shows disks
2. ✓ Last scan timestamp updates automatically
3. ✓ InfluxDB health check shows: `✓ Connected`
4. ✓ Metrics appear in InfluxDB after 3 minutes
5. ✓ Grafana dashboard displays disk health charts
6. ✓ Navbar Grafana link appears and works
7. ✓ Alerts work if configured

---

## 📞 Support Resources

1. **UNRAID_SETUP.md** - Full deployment guide
2. **DOCKER_NETWORKING_GUIDE.md** - Understand networking issues
3. **QUICK_START.md** - Fast reference
4. **Docker logs** - Most detailed troubleshooting info

Check logs first: `docker logs diskwarden -f` (follow mode)
