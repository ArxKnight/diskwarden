# 🛡️ DiskWarden
![DiskWarden Logo](/static/img/diskwarden_logo.png)

DiskWarden is a lightweight disk health monitoring and alerting tool built around
HDSentinel, with a simple web UI and notification support via Discord and email.

It is designed for servers and homelabs where early warning of disk degradation
is critical, but heavyweight monitoring stacks are unnecessary.

---
## 📊 DiskWarden Dashboard
![DiskWarden Dashboard](/static/img/diskwarden-dashboard.png)

---

## ✨ Features

- Reads disk health data directly from HDSentinel
- Web-based dashboard (Flask)
- Configurable health thresholds
- Discord webhook notifications
- Email alerts via SMTP
- Simple JSON-based configuration
- **Optional InfluxDB metrics collection** (time-series monitoring)
- **Optional Grafana dashboard integration** (visual analytics)
- Per-disk alert disabling (useful for USB/external drives)
- Last scan timestamp tracking
- Docker support with automatic hostname resolution
- **Unraid-optimized** deployment with bridge network support

---

## ⚙️ How It Works

DiskWarden runs HDSentinel on the host system and parses its output to extract:

- Drive path
- Disk model
- Serial number
- Capacity
- Temperature
- Highest recorded temperature
- Health percentage
- Performance percentage
- Power-on time
- Estimated remaining lifetime

If a disk’s health drops below the configured threshold, DiskWarden can notify
you via Discord and/or email.

---

## 🌐 Web Interface

DiskWarden exposes a small web UI that allows you to:

- View detected disks and their health
- See temperatures, health %, and lifetime estimates
- Adjust alert settings through the settings page

By default, the web interface listens on:

http://<host>:7500

---

## 🧩 Requirements

### 🖥️ Host Requirements
- Python 3.9+
- HDSentinel installed and accessible on the machine running DiskWarden

### 📦 Python Dependencies

pip install -r requirements.txt

---

## Running DiskWarden

### Docker (recommended)

DiskWarden is primarily distributed as a Docker image.

docker pull arxknight/diskwarden:latest

docker run -d \
  -p 7500:7500 \
  --privileged \
  -v /dev:/dev \
  arxknight/diskwarden:latest

IMPORTANT:
DiskWarden requires access to host disk devices to read health data.
Only run with --privileged in trusted environments.

---

### Local (Python)

pip install -r requirements.txt
python app.py

Open:

http://localhost:7500

---

## Docker Image

The official Docker image is available on Docker Hub:
https://hub.docker.com/r/arxknight/diskwarden
