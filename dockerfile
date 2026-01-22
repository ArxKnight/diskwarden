# Use a base image with glibc
FROM ubuntu:20.04

# Install necessary packages and set timezone non-interactively
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip wget unzip sudo tzdata

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

# Configure sudoers to allow passwordless execution for the script
RUN echo "ALL ALL=(ALL) NOPASSWD: /usr/local/bin/HDSentinel" >> /etc/sudoers

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the application code
COPY . .

# Expose port 7500
EXPOSE 7500

# Environment variables
# DISKWARDEN_SCANNER=1 enables the background scanner (default: enabled)
# TZ=UTC sets the timezone to avoid tzlocal errors on systems with non-zoneinfo timezones
ENV DISKWARDEN_SCANNER=1 \
    TZ=UTC

# Run the application
CMD ["python3", "app.py"]