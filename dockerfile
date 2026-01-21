# Use a base image with glibc
FROM ubuntu:20.04

# Install necessary packages
RUN apt-get update && \
    apt-get install -y python3 python3-pip wget unzip sudo

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

# Run the application
CMD ["python3", "app.py"]