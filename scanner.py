"""
Disk scanning logic for DiskWarden.
This module contains reusable functions for scanning disks and parsing HDSentinel output.
"""

import subprocess
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_hd_sentinel_output(output: str) -> List[Dict[str, Any]]:
    """
    Parse HDSentinel CLI output into a list of disk dictionaries.
    
    Args:
        output: Raw output from HDSentinel -r command
        
    Returns:
        List of disk dictionaries with parsed fields
    """
    disks = []
    lines = output.splitlines()
    disk = {}
    
    for line in lines:
        if line.startswith("HDD Device"):
            if disk:
                disks.append(disk)
                disk = {}
            disk['device'] = line.split(":", 1)[1].strip() if ":" in line else ""
        elif line.startswith("HDD Model ID"):
            disk['model_id'] = line.split(":", 1)[1].strip() if ":" in line else ""
        elif line.startswith("HDD Serial No"):
            disk['serial_no'] = line.split(":", 1)[1].strip() if ":" in line else ""
        elif line.startswith("HDD Size"):
            disk['size'] = line.split(":", 1)[1].strip() if ":" in line else ""
        elif line.startswith("Temperature"):
            disk['temperature'] = line.split(":", 1)[1].strip() if ":" in line else ""
        elif line.startswith("Highest Temp"):
            disk['highest_temp'] = line.split(":", 1)[1].strip() if ":" in line else ""
        elif line.startswith("Health"):
            disk['health'] = line.split(":", 1)[1].strip() if ":" in line else ""
        elif line.startswith("Performance"):
            disk['performance'] = line.split(":", 1)[1].strip() if ":" in line else ""
        elif line.startswith("Power on time"):
            disk['power_on_time'] = line.split(":", 1)[1].strip() if ":" in line else ""
        elif line.startswith("Est. lifetime"):
            disk['lifetime'] = line.split(":", 1)[1].strip() if ":" in line else ""
    
    if disk:
        disks.append(disk)
    
    return disks


def run_hd_sentinel() -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Execute HDSentinel CLI and return parsed disk data.
    
    Returns:
        Tuple of (success: bool, disks: List[Dict])
        If HDSentinel fails, returns (False, [])
    """
    try:
        result = subprocess.run(
            ['/usr/local/bin/HDSentinel', '-r'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"HDSentinel failed with return code {result.returncode}")
            return False, []
        
        output = result.stdout.decode('utf-8', errors='replace')
        disks = parse_hd_sentinel_output(output)
        logger.debug(f"Successfully scanned {len(disks)} disks")
        return True, disks
        
    except FileNotFoundError:
        logger.error("HDSentinel not found at /usr/local/bin/HDSentinel")
        return False, []
    except subprocess.TimeoutExpired:
        logger.error("HDSentinel scan timed out")
        return False, []
    except Exception as e:
        logger.error(f"Error running HDSentinel: {e}")
        return False, []


def get_disk_identity(disk: Dict[str, Any]) -> str:
    """
    Get a unique identifier for a disk (serial_no or device).
    
    Args:
        disk: Disk dictionary from parse_hd_sentinel_output
        
    Returns:
        Unique identifier string (preferring serial_no)
    """
    if disk.get('serial_no'):
        return disk['serial_no']
    return disk.get('device', 'unknown')


def get_health_percent(disk: Dict[str, Any]) -> int:
    """
    Extract health percentage from disk data.
    
    Args:
        disk: Disk dictionary from parse_hd_sentinel_output
        
    Returns:
        Health percentage (0-100), or 0 if parse fails
    """
    try:
        health_str = disk.get('health', '0%')
        health_percent = int(health_str.split('%')[0].strip())
        return max(0, min(100, health_percent))  # Clamp to 0-100
    except (ValueError, IndexError, AttributeError):
        return 0


def get_numeric_value(value_str: str, default: int = 0) -> int:
    """
    Extract numeric value from a string, ignoring units.
    
    Args:
        value_str: String potentially containing units (e.g., "45°C", "1000 hours")
        default: Default value if parsing fails
        
    Returns:
        Numeric value or default
    """
    try:
        # Extract leading digits and optional decimal
        import re
        match = re.search(r'(\d+\.?\d*)', str(value_str))
        if match:
            return int(float(match.group(1)))
    except (ValueError, AttributeError):
        pass
    return default
