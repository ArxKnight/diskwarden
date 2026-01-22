"""
DiskWarden - Flask-based disk health monitoring service with background scanning.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from threading import Lock
from flask import Flask, request, jsonify, render_template
from flask_mail import Mail, Message
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Set timezone early to prevent tzlocal errors
# Default to UTC, can be overridden by environment variable or settings
default_tz = os.environ.get('TZ', 'UTC')
os.environ['TZ'] = default_tz
try:
    import time
    time.tzset()
except AttributeError:
    pass  # Windows doesn't have tzset()

from scanner import run_hd_sentinel, get_disk_identity, get_health_percent
from state_tracker import DiskStateTracker
from influx_writer import InfluxDBWriter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global state
settings_lock = Lock()
last_scan_data = None
last_scan_time = None
scan_in_progress = False
state_tracker = DiskStateTracker()
influx_writer = InfluxDBWriter()

# Configure scheduler with explicit timezone to avoid tzlocal errors
# This prevents APScheduler from trying to auto-detect timezone
# which can fail on systems with non-standard timezone configurations
try:
    scheduler = BackgroundScheduler(
        timezone='UTC',
        job_defaults={'coalesce': True, 'max_instances': 1}
    )
except Exception as e:
    logger.error(f"Failed to initialize scheduler with UTC: {e}")
    # Last resort: use a minimal configuration
    scheduler = BackgroundScheduler(job_defaults={'coalesce': True, 'max_instances': 1})


def load_settings():
    """Load settings from JSON file with thread safety."""
    try:
        with open('settings.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        return {}


def save_settings(settings):
    """Save settings to JSON file with thread safety."""
    try:
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
        logger.debug("Settings saved")
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")


def update_mail_config():
    """Update Flask-Mail configuration from current settings."""
    settings = load_settings()
    app.config.update(
        MAIL_SERVER=settings.get('smtpServer', 'smtp.gmail.com'),
        MAIL_PORT=int(settings.get('smtpPort', 587)),
        MAIL_USE_TLS=True,
        MAIL_USERNAME=settings.get('email', ''),
        MAIL_PASSWORD=settings.get('emailPassword', '')
    )
    Mail(app)


def send_email(subject, recipient, body):
    """Send email notification."""
    if not recipient:
        return False
    
    try:
        mail = Mail(app)
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipient])
        msg.body = body
        mail.send(msg)
        logger.debug(f"Email sent to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False



def send_discord_notification(webhook_url, message):
    """Send notification to Discord webhook."""
    if not webhook_url:
        return False
    
    try:
        data = {"content": message}
        response = requests.post(webhook_url, json=data, timeout=10)
        response.raise_for_status()
        logger.debug("Discord notification sent")
        return True
    except Exception as e:
        logger.error(f"Failed to send Discord notification: {e}")
        return False


def perform_disk_scan():
    """
    Perform a disk scan and handle state transitions, alerts, and metrics.
    This is the core scanning logic used by both scheduler and manual API calls.
    """
    global last_scan_data, last_scan_time, scan_in_progress
    
    if scan_in_progress:
        logger.debug("Scan already in progress, skipping")
        return
    
    scan_in_progress = True
    try:
        settings = load_settings()
        
        # Run HDSentinel
        logger.info("Starting disk scan...")
        success, disks = run_hd_sentinel()
        
        if not success or not disks:
            logger.warning("Disk scan failed or returned no disks")
            return
        
        # Get thresholds and alert settings
        health_threshold = int(settings.get('healthThreshold', 90))
        notify_on_recovery = settings.get('notifyOnRecovery', False)
        alert_cooldown_minutes = int(settings.get('alertCooldownMinutes', 0))
        webhook_url = settings.get('webhookUrl', '')
        email = settings.get('email', '')
        disabled_disks = settings.get('disabledDisks', {})
        
        # Process each disk for state tracking and alerts
        for disk in disks:
            disk_id = get_disk_identity(disk)
            health_percent = get_health_percent(disk)
            
            # Check if alerts are disabled for this disk
            if disabled_disks.get(disk_id, False):
                logger.debug(f"Skipping alerts for disk {disk_id} (alerts disabled)")
                continue
            
            # Update state and get alert info
            state_result = state_tracker.update_disk(
                disk_id,
                device=disk.get('device', ''),
                serial_no=disk.get('serial_no', ''),
                health_percent=health_percent,
                threshold=health_threshold
            )
            
            alert_type = state_result['alert_type']
            old_state = state_result['old_state']
            new_state = state_result['new_state']
            
            # Determine if alert should be sent
            should_alert = False
            alert_message = None
            
            if alert_type == "transition":
                # Disk went OK -> BELOW_THRESHOLD
                should_alert = True
                alert_message = (
                    f"⚠️ **Disk Health Alert**: {disk.get('device', 'Unknown')} "
                    f"(SN: {disk.get('serial_no', 'N/A')}) has health {health_percent}% "
                    f"(threshold: {health_threshold}%)"
                )
            
            elif alert_type == "recovery" and notify_on_recovery:
                # Disk went BELOW_THRESHOLD -> OK
                should_alert = True
                alert_message = (
                    f"✅ **Disk Recovered**: {disk.get('device', 'Unknown')} "
                    f"(SN: {disk.get('serial_no', 'N/A')}) health recovered to {health_percent}%"
                )
            
            elif alert_type is None and new_state == state_tracker.STATE_BELOW_THRESHOLD:
                # Check if reminder alert should be sent
                if state_tracker.should_send_reminder(disk_id, alert_cooldown_minutes):
                    should_alert = True
                    alert_message = (
                        f"🔔 **Disk Health Reminder**: {disk.get('device', 'Unknown')} "
                        f"(SN: {disk.get('serial_no', 'N/A')}) still at {health_percent}% "
                        f"(threshold: {health_threshold}%)"
                    )
            
            # Send alerts
            if should_alert and alert_message:
                logger.info(f"Sending alert for disk {disk_id}: {alert_type}")
                
                if webhook_url:
                    send_discord_notification(webhook_url, alert_message)
                
                if email:
                    subject = alert_message.split(':')[0]
                    send_email(subject, email, alert_message)
                
                # Update cooldown tracking
                state_tracker.update_last_alert_time(disk_id)
        
        # Write metrics to InfluxDB if enabled
        if settings.get('influxEnabled', False):
            try:
                influx_writer.configure(
                    url=settings.get('influxUrl', ''),
                    token=settings.get('influxToken', ''),
                    org=settings.get('influxOrg', 'diskwarden'),
                    bucket=settings.get('influxBucket', 'diskwarden')
                )
                influx_writer.write_disk_metrics(disks)
            except Exception as e:
                logger.error(f"Failed to write InfluxDB metrics: {e}")
        
        # Cache the results
        last_scan_data = disks
        last_scan_time = datetime.now()
        logger.info(f"Disk scan complete: {len(disks)} disks")
        
    except Exception as e:
        logger.error(f"Unexpected error during disk scan: {e}")
    finally:
        scan_in_progress = False


def schedule_scanner():
    """Start the background scanner if enabled."""
    if os.environ.get('DISKWARDEN_SCANNER') == '1':
        settings = load_settings()
        scan_interval = int(settings.get('scanIntervalSeconds', 60))
        
        logger.info(f"Starting background scanner (interval: {scan_interval}s)")
        
        scheduler.add_job(
            perform_disk_scan,
            trigger=IntervalTrigger(seconds=scan_interval),
            id='disk_scan',
            name='Disk Health Scan',
            replace_existing=True
        )
        
        if not scheduler.running:
            scheduler.start()




# ============================================================================
# Flask Routes
# ============================================================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/settings')
def settings_page():
    return render_template('settings.html')


@app.route('/api/disk_health', methods=['GET'])
def get_disk_health():
    """
    Get the last cached disk scan results with timestamp.
    Does NOT trigger a new scan.
    """
    if last_scan_data is None:
        return jsonify({"error": "No scan data available yet"}), 503
    
    # Include timestamp with scan data
    response = {
        "last_scan_time": last_scan_time.isoformat() if last_scan_time else None,
        "disks": last_scan_data
    }
    return jsonify(response), 200


@app.route('/api/scan_now', methods=['POST'])
def scan_now():
    """
    Trigger an immediate disk scan.
    Respects state tracking and alert suppression rules.
    """
    try:
        perform_disk_scan()
        return jsonify({
            "message": "Scan completed",
            "last_scan": last_scan_time.isoformat() if last_scan_time else None,
            "disk_count": len(last_scan_data) if last_scan_data else 0
        }), 200
    except Exception as e:
        logger.error(f"Error in scan_now endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Get scanner status information.
    """
    settings = load_settings()
    scan_interval = int(settings.get('scanIntervalSeconds', 60))
    
    # Count disks below threshold
    all_states = state_tracker.get_all_states()
    below_threshold_count = sum(
        1 for disk_state in all_states.values()
        if disk_state['state'] == state_tracker.STATE_BELOW_THRESHOLD
    )
    
    # Calculate next scan time
    next_scan_time = None
    if last_scan_time:
        next_scan_time = (last_scan_time + timedelta(seconds=scan_interval)).isoformat()
    
    return jsonify({
        "last_scan": last_scan_time.isoformat() if last_scan_time else None,
        "next_scan": next_scan_time,
        "scan_interval_seconds": scan_interval,
        "disks_below_threshold": below_threshold_count,
        "scanner_running": os.environ.get('DISKWARDEN_SCANNER') == '1',
        "influx_enabled": settings.get('influxEnabled', False),
        "grafana_url": settings.get('grafanaUrl', '')
    }), 200



@app.route('/api/settings', methods=['GET', 'POST'])
def settings_endpoint():
    """Get or update settings."""
    if request.method == 'GET':
        try:
            settings = load_settings()
            return jsonify(settings), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    else:  # POST
        try:
            new_settings = request.json
            with settings_lock:
                existing_settings = load_settings()
                existing_settings.update(new_settings)
                save_settings(existing_settings)
            
            # Update mail config if email settings changed
            if any(k in new_settings for k in ['smtpServer', 'smtpPort', 'email', 'emailPassword']):
                update_mail_config()
            
            # Reschedule scanner if scan interval changed
            if 'scanIntervalSeconds' in new_settings and os.environ.get('DISKWARDEN_SCANNER') == '1':
                scan_interval = int(new_settings.get('scanIntervalSeconds', 60))
                if scheduler.running:
                    job = scheduler.get_job('disk_scan')
                    if job:
                        job.reschedule(trigger=IntervalTrigger(seconds=scan_interval))
                        logger.info(f"Rescheduled scanner to {scan_interval}s interval")
            
            return jsonify({"message": "Settings saved"}), 200
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return jsonify({"error": str(e)}), 500


@app.route('/api/email_settings', methods=['POST'])
def email_settings_endpoint():
    """Save email settings endpoint (for backwards compatibility)."""
    try:
        settings_data = request.json
        new_settings = {
            'smtpServer': settings_data.get('smtpServer', ''),
            'smtpPort': int(settings_data.get('smtpPort', 587)),
            'email': settings_data.get('email', ''),
            'emailPassword': settings_data.get('emailPassword', '')
        }
        
        with settings_lock:
            existing_settings = load_settings()
            existing_settings.update(new_settings)
            save_settings(existing_settings)
        
        update_mail_config()
        return jsonify({"message": "Email settings saved"}), 200
    except Exception as e:
        logger.error(f"Error saving email settings: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/api/test_email', methods=['POST'])
def test_email():
    """Send a test email."""
    settings_data = request.json
    try:
        update_mail_config()
        recipient = settings_data.get('email', '')
        if not recipient:
            return jsonify({"error": "Email not provided"}), 400
        
        success = send_email(
            "Test Email from DiskWarden",
            recipient,
            "This is a test email from DiskWarden. If you received this, your SMTP settings are working!"
        )
        
        if success:
            return jsonify({"message": "Test email sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send email"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/test_message', methods=['POST'])
def test_message():
    """Send a test Discord message."""
    settings_data = request.json
    webhook_url = settings_data.get('webhookUrl')
    
    if not webhook_url:
        return jsonify({"error": "Webhook URL not provided"}), 400
    
    try:
        success = send_discord_notification(
            webhook_url,
            "✅ Test message from DiskWarden! Your Discord webhook is working correctly."
        )
        
        if success:
            return jsonify({"message": "Test message sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send message"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Initialization
# ============================================================================

def init_app():
    """Initialize the Flask application."""
    global last_scan_data
    
    logger.info("Initializing DiskWarden...")
    
    # Load initial settings and configure mail
    update_mail_config()
    
    # Start background scanner if enabled
    schedule_scanner()
    
    # Run one initial scan if scanner is enabled
    if os.environ.get('DISKWARDEN_SCANNER') == '1':
        logger.info("Running initial scan...")
        perform_disk_scan()


if __name__ == '__main__':
    try:
        init_app()
        logger.info("Starting Flask server on 0.0.0.0:7500")
        app.run(host='0.0.0.0', port=7500, threaded=True, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        if scheduler.running:
            scheduler.shutdown()
        influx_writer.close()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if scheduler.running:
            scheduler.shutdown()
