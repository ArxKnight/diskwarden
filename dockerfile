# Multi-service container (DiskWarden + InfluxDB + Grafana)
# Based on grafana-unraid-stack pattern
FROM ubuntu:20.04

# Install necessary packages and set timezone non-interactively
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 python3-pip \
    wget unzip sudo tzdata \
    supervisor \
    curl \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Set timezone to UTC by default
RUN ln -fs /usr/share/zoneinfo/UTC /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# Set working directory
WORKDIR /app

# Download and install HDSentinel
RUN wget -O hdsentinel-020b-x64.zip "https://www.hdsentinel.com/hdslin/hdsentinel-020b-x64.zip" && \
    unzip hdsentinel-020b-x64.zip && \
    chmod +x HDSentinel && \
    mv HDSentinel /usr/local/bin/HDSentinel

# Configure sudoers to allow passwordless execution for HDSentinel
RUN echo "ALL ALL=(ALL) NOPASSWD: /usr/local/bin/HDSentinel" >> /etc/sudoers

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Download and install InfluxDB
RUN wget https://dl.influxdata.com/influxdb/releases/influxdb2-2.8.0_linux_amd64.tar.gz && \
    tar xvfz influxdb2-2.8.0_linux_amd64.tar.gz && \
    cp influxdb2-2.8.0/influxd /usr/local/bin/influxd && \
    mkdir -p /var/lib/influxdb && \
    rm -rf influxdb2-2.8.0* *.tar.gz

# Download and install Grafana
RUN wget https://dl.grafana.com/oss/release/grafana-10.0.0.linux-amd64.tar.gz && \
    tar xvfz grafana-10.0.0.linux-amd64.tar.gz && \
    mv grafana-10.0.0 /opt/grafana && \
    mkdir -p /var/lib/grafana && \
    rm -f *.tar.gz

# Create directories for data persistence
RUN mkdir -p /config /data /data/influxdb /data/grafana

# Copy the application code
COPY . .

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports: DiskWarden (7500), InfluxDB (8086), Grafana (3000)
EXPOSE 7500 8086 3000

# Environment variables
ENV DISKWARDEN_SCANNER=1 \
    TZ=UTC \
    INFLUXDB_CONFIG_PATH=/data/influxdb \
    GRAFANA_HOME=/opt/grafana

# Run supervisord to manage all services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]