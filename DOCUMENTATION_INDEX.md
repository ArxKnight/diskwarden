# 📚 DiskWarden Documentation Index

Welcome to DiskWarden! This index helps you find what you need.

---

## 🚀 Getting Started

**New to DiskWarden?** Start here:

1. **[README.md](README.md)** - Project overview and features
2. **[QUICK_START.md](QUICK_START.md)** - 3-step setup for Unraid

---

## 🏗️ Deployment Guides

Choose based on your setup:

### For Unraid Users
- **[UNRAID_SETUP.md](UNRAID_SETUP.md)** - Complete Unraid deployment guide
  - Container configuration steps
  - Network setup
  - Verification procedures
  - Metrics collection setup

### For Docker Users (Other Systems)
- **[docker-compose.yml](docker-compose.yml)** - Ready-to-use deployment file
- Edit for your network configuration
- Update port mappings as needed

---

## 🔧 Understanding the System

### Networking & Architecture

**I don't understand Docker networking...**
→ Read: **[DOCKER_NETWORKING_GUIDE.md](DOCKER_NETWORKING_GUIDE.md)**
- Explains Docker internal DNS
- Why external IPs don't work from containers
- Hostname resolution diagrams
- Troubleshooting networking issues

**What changed recently?**
→ Read: **[DEPLOYMENT_UPDATE.md](DEPLOYMENT_UPDATE.md)**
- Summary of hostname resolution feature
- Before/after comparison
- How it works
- Code changes

---

## 📋 Verification & Troubleshooting

### Checking Your Setup

**Is my deployment working?**
→ Use: **[VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)**
- Pre-deployment checklist
- Post-deployment checklist
- Metrics verification (after 3 minutes)
- Common issues & solutions
- Troubleshooting procedures

---

## 📖 Comprehensive Overviews

### Full Project Information

**Complete project summary:**
→ Read: **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)**
- Feature completeness
- File inventory (all 19 files)
- Technical stack details
- Performance characteristics
- Architecture diagrams

**Implementation details:**
→ Read: **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)**
- What changed in latest version
- Hostname resolution explained
- User impact analysis
- Before/after comparison
- Technical learning points

---

## 🎯 Common Tasks

### Configuration

**How to enable metrics collection?**
1. Open DiskWarden: http://192.168.x.x:7500
2. Click Settings
3. InfluxDB section:
   - Toggle "Enable InfluxDB Metrics" ON
   - URL: `http://influxdb:8086` (leave default)
   - Organization: `diskwarden`
   - Bucket: `diskwarden`
4. Click Save

**How to set up Grafana dashboard?**
1. Set Grafana URL in Settings: `http://192.168.x.x:3000`
2. Grafana link appears in navbar
3. Login to Grafana: admin / admin
4. Dashboard auto-provisioned with disk metrics

**How to disable alerts for a specific disk?**
1. Open Settings
2. Scroll to "Alert Controls"
3. Check the disk to disable alerts
4. Save

### Alerts

**How to set up Discord notifications?**
1. Settings → Webhook section
2. Paste Discord webhook URL
3. Set health threshold
4. Save

**How to set up Email alerts?**
1. Settings → SMTP section
2. Enter SMTP server details
3. Enter email address
4. Set health threshold
5. Save

---

## 📊 Monitoring

### Accessing Your Dashboards

**DiskWarden Dashboard** (Main Interface)
- URL: http://192.168.x.x:7500
- Shows: Current disk health, temperatures, last scan time
- Actions: Configure alerts, enable metrics

**Grafana Dashboards** (Visual Analytics)
- URL: http://192.168.x.x:3000
- Username: admin
- Password: admin
- Shows: Disk health trends, temperature history, metrics over time

**InfluxDB Admin** (Metrics Database)
- URL: http://192.168.x.x:8086
- Shows: Raw metrics data
- Use for: Advanced queries

---

## 🐛 Problem Solving

### Quick Troubleshooting

**Disks aren't showing on dashboard:**
- Check: Containers running in Unraid Docker section
- Check: DiskWarden container has `--privileged` flag
- Check: `/dev` volume mounted

**InfluxDB connection fails:**
- ✓ This might be OK! Check if metrics are being written
- Container name must be exactly `influxdb`
- If hostname fails, use manual IP: `docker inspect influxdb | grep IPAddress`

**Grafana dashboard is empty:**
- Wait 3-5 minutes for first metrics to collect
- Check: InfluxDB datasource is configured
- Verify: Data exists in InfluxDB

**Settings won't save:**
- Check: File permissions on settings.json
- Check: Disk space on Unraid
- Try: Restart DiskWarden container

### Detailed Help

For detailed troubleshooting:
→ See: **[VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)** - Common Issues section
→ See: **[DOCKER_NETWORKING_GUIDE.md](DOCKER_NETWORKING_GUIDE.md)** - Troubleshooting section

---

## 📝 Technical Documentation

### For Developers

**Understanding the code:**
- **app.py** - Flask API and APScheduler orchestration
- **scanner.py** - HDSentinel CLI parsing
- **state_tracker.py** - SQLite persistence
- **influx_writer.py** - InfluxDB metrics writing

**Architecture:**
- REST API endpoints in app.py
- Background scheduler for continuous scanning
- SQLite for state persistence
- Optional InfluxDB for metrics
- Optional Grafana for visualization

### Configuration Files

**settings.json** - Your configuration
```json
{
  "influxEnabled": true,
  "influxUrl": "http://influxdb:8086",
  "grafanaUrl": "http://192.168.x.x:3000",
  "healthThreshold": 90,
  "webhookUrl": "",
  "smtpServer": "",
  // ... more settings
}
```

**docker-compose.yml** - Full stack deployment
- DiskWarden container
- InfluxDB container
- Grafana container
- Volumes and networking

---

## 🔄 Version History

**Current Version:** 1.7

Recent updates:
- v1.7: Automatic Docker hostname resolution
- v1.6: Hostname-based networking
- v1.5: Split InfluxDB/Grafana settings
- v1.4: Per-disk alert disabling
- v1.3: Timezone configuration
- v1.2: Python 3.8 compatibility
- v1.1: InfluxDB and Grafana integration
- v1.0: Initial release

See: **[LATEST_UPDATES.md](LATEST_UPDATES.md)** for full changelog

---

## ✅ Quick Reference

### Container Names (Must Be Exact)
```
influxdb    - Time-series metrics database
grafana     - Dashboard visualization
diskwarden  - Health monitoring service
```

### Important URLs
```
DiskWarden:  http://192.168.x.x:7500
Grafana:     http://192.168.x.x:3000
InfluxDB:    http://192.168.x.x:8086
```

### Configuration URLs (Inside Docker)
```
InfluxDB:    http://influxdb:8086     (auto-resolves)
Grafana:     http://grafana:3000      (auto-resolves)
```

### Default Credentials
```
Grafana:     admin / admin
InfluxDB:    No auth (local setup)
DiskWarden:  No auth (local setup)
```

---

## 📞 Support Resources

### Documentation Files
1. README.md - Start here
2. QUICK_START.md - Fast reference
3. UNRAID_SETUP.md - Detailed deployment
4. DOCKER_NETWORKING_GUIDE.md - Networking help
5. VERIFICATION_CHECKLIST.md - Testing
6. PROJECT_SUMMARY.md - Complete overview
7. IMPLEMENTATION_SUMMARY.md - Technical details

### Checking Logs
```bash
# View DiskWarden logs
docker logs diskwarden -f

# View InfluxDB logs
docker logs influxdb

# View Grafana logs
docker logs grafana
```

### Manual Commands
```bash
# Find container IPs
docker inspect influxdb | grep IPAddress

# Verify containers running
docker ps

# Check network connectivity
docker exec diskwarden ping influxdb
```

---

## 🎓 Learning Path

### For Users
1. Read README.md
2. Follow QUICK_START.md
3. Use VERIFICATION_CHECKLIST.md
4. Refer to specific guides as needed

### For Operators
1. Read UNRAID_SETUP.md
2. Understand DOCKER_NETWORKING_GUIDE.md
3. Bookmark VERIFICATION_CHECKLIST.md
4. Keep PROJECT_SUMMARY.md for reference

### For Developers
1. Explore codebase (app.py, scanner.py, etc.)
2. Read PROJECT_SUMMARY.md architecture
3. Review influx_writer.py integration
4. Check docker-compose.yml deployment

---

## 🎉 You're All Set!

Choose your starting point:
- **First time user?** → Start with [QUICK_START.md](QUICK_START.md)
- **Setting up Unraid?** → Go to [UNRAID_SETUP.md](UNRAID_SETUP.md)
- **Understanding networks?** → Read [DOCKER_NETWORKING_GUIDE.md](DOCKER_NETWORKING_GUIDE.md)
- **Troubleshooting?** → Check [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)
- **Complete overview?** → See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

---

**Questions?** Check the appropriate guide above.
**Issues?** See VERIFICATION_CHECKLIST.md troubleshooting section.
**Enjoy monitoring your disks!** 🛡️
