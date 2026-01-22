from flask import Flask, request, jsonify, render_template
from flask_mail import Mail, Message
import json
import subprocess
import requests

app = Flask(__name__)

# Load settings from JSON
with open('settings.json', 'r') as f:
    settings = json.load(f)

app.config.update(
    MAIL_SERVER=settings.get('smtpServer', 'smtp.gmail.com'),
    MAIL_PORT=settings.get('smtpPort', 587),
    MAIL_USE_TLS=True,
    MAIL_USERNAME=settings.get('email', ''),
    MAIL_PASSWORD=settings.get('emailPassword', '')
)

mail = Mail(app)

def send_email(subject, recipient, body):
    msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipient])
    msg.body = body
    mail.send(msg)

def send_discord_notification(webhook_url, message):
    """Send a notification to Discord webhook"""
    try:
        data = {"content": message}
        requests.post(webhook_url, json=data)
        return True
    except Exception as e:
        print(f"Error sending Discord notification: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings')
def settings_page():
    return render_template('settings.html')

@app.route('/api/settings', methods=['GET', 'POST'])
def settings_endpoint():
    if request.method == 'GET':
        # Load and return existing settings
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
            return jsonify(settings), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        # Save new settings
        settings = request.json
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
        app.config.update(
            MAIL_SERVER=settings.get('smtpServer', 'smtp.gmail.com'),
            MAIL_PORT=settings.get('smtpPort', 587),
            MAIL_USE_TLS=True,
            MAIL_USERNAME=settings.get('email', ''),
            MAIL_PASSWORD=settings.get('emailPassword', '')
        )
        return jsonify({"message": "Settings saved"}), 200

@app.route('/api/test_email', methods=['POST'])
def test_email():
    settings = request.json
    try:
        send_email("Test Email", settings['email'], "This is a test email from Disk Health Monitor.")
        return jsonify({"message": "Test email sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test_message', methods=['POST'])
def test_message():
    settings = request.json
    webhook_url = settings.get('webhookUrl')
    if not webhook_url:
        return jsonify({"error": "Webhook URL not provided"}), 400
    try:
        send_discord_notification(webhook_url, "Test message from DiskWarden! Your Discord webhook is working correctly.")
        return jsonify({"message": "Test message sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/disk_health', methods=['GET'])
def disk_health():
    try:
        result = subprocess.run(['/usr/local/bin/HDSentinel', '-r'], stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        # Parse the output to extract the required information
        disks = parse_hd_sentinel_output(output)
        
        # Load settings to check threshold and notification settings
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        
        health_threshold = int(settings.get('healthThreshold', 90))
        webhook_url = settings.get('webhookUrl', '')
        email = settings.get('email', '')
        
        # Check each disk and send notifications if health is below threshold
        for disk in disks:
            if 'health' in disk:
                try:
                    health_value = int(disk['health'].split('%')[0])
                    if health_value < health_threshold:
                        message = f"⚠️ Disk Health Alert: {disk.get('device', 'Unknown')} has health {health_value}% (threshold: {health_threshold}%)"
                        
                        # Send Discord notification if webhook URL is set
                        if webhook_url:
                            send_discord_notification(webhook_url, message)
                        
                        # Send email notification if email is set
                        if email:
                            try:
                                send_email("Disk Health Alert", email, message)
                            except Exception as e:
                                print(f"Error sending email: {e}")
                except (ValueError, AttributeError):
                    pass
        
        return jsonify(disks), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def parse_hd_sentinel_output(output):
    # Implement the parsing logic here
    disks = []
    lines = output.splitlines()
    disk = {}
    for line in lines:
        if line.startswith("HDD Device"):
            if disk:
                disks.append(disk)
                disk = {}
            disk['device'] = line.split(":")[1].strip()
        elif line.startswith("HDD Model ID"):
            disk['model_id'] = line.split(":")[1].strip()
        elif line.startswith("HDD Serial No"):
            disk['serial_no'] = line.split(":")[1].strip()
        elif line.startswith("HDD Size"):
            disk['size'] = line.split(":")[1].strip()
        elif line.startswith("Temperature"):
            disk['temperature'] = line.split(":")[1].strip()
        elif line.startswith("Highest Temp"):
            disk['highest_temp'] = line.split(":")[1].strip()
        elif line.startswith("Health"):
            disk['health'] = line.split(":")[1].strip()
        elif line.startswith("Performance"):
            disk['performance'] = line.split(":")[1].strip()
        elif line.startswith("Power on time"):
            disk['power_on_time'] = line.split(":")[1].strip()
        elif line.startswith("Est. lifetime"):
            disk['lifetime'] = line.split(":")[1].strip()
    if disk:
        disks.append(disk)
    return disks

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7500)