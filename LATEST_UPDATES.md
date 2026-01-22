# DiskWarden - Latest Updates Summary

## Issues Fixed

### 1. ✅ Timestamp Display
- **Fixed**: "Last updated: No data available" now shows actual scan timestamp
- **Implementation**: API now returns `last_scan_time` with disk data
- **Result**: Users see when the last scan ran

### 2. ✅ InfluxDB & Grafana Setup  
- **Port Correction**: InfluxDB is now correctly on port 8086 (not 3000)
- **Grafana**: Correctly runs on port 3000
- **Local Setup**: Both included in docker-compose.yml and enabled by default

### 3. ✅ API Token Clarification
- **Updated documentation**: Token is now marked as "Optional"  
- **Local setup**: Leave blank (uses default container auth)
- **Remote setup**: Provide token for external InfluxDB instances
- **Flexibility**: Supports both local and remote InfluxDB

### 4. ✅ Split Settings Pages
- **InfluxDB Settings**: Separate card for metrics configuration
- **Grafana Settings**: Separate card for dashboard visualization
- **Clearer documentation**: Each section explains its purpose

### 5. ✅ Grafana Navbar Link
- **Auto-detect**: Checks settings for Grafana URL on page load
- **Dynamic display**: Link appears in navbar when URL is configured
- **Direct access**: One-click access to Grafana dashboards

### 6. ✅ Auto-Dashboard Setup
- **Grafana provisioning**: Automatic datasource and dashboard creation
- **Default dashboard**: Pre-configured with DiskWarden metrics panels
- **Zero config**: Works immediately after docker-compose up

## New Files Created
- `grafana-provisioning/datasources/datasource.yml` - InfluxDB datasource config
- `grafana-provisioning/dashboards/dashboard.yml` - Dashboard provisioning config  
- `grafana-provisioning/dashboards/diskwarden.json` - Pre-built dashboard with 4 panels

## Per-Disk Alert Disabling
- **Feature**: Disable alerts for specific disks (USB drives, etc.)
- **UI**: Settings page has disk alert toggle list
- **Use case**: Suppress alerts for devices that don't report health properly

## Updated UI Components
- **index.html**: Shows scan timestamp, Grafana link in navbar
- **settings.html**: Separate InfluxDB and Grafana sections, clearer labels

## Quick Start for Your Server
```bash
cd /path/to/diskwarden
docker-compose up -d

# Access points:
# - DiskWarden: http://192.168.0.204:7500
# - Grafana: http://192.168.0.204:3000 (admin/admin)
# - InfluxDB: http://192.168.0.204:8086
```

Configure Grafana URL in Settings → it will automatically add navbar link!
