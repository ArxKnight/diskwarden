"""
InfluxDB metrics writer for DiskWarden.
Writes disk health metrics to InfluxDB v2 for long-term storage and Grafana visualization.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class InfluxDBWriter:
    """Writes disk health metrics to InfluxDB."""
    
    def __init__(self):
        """Initialize InfluxDB client (only if settings indicate it's enabled)."""
        self.client = None
        self.write_api = None
    
    def configure(self, url: str, token: str, org: str, bucket: str) -> bool:
        """
        Configure InfluxDB connection.
        
        Args:
            url: InfluxDB URL (e.g., http://influxdb:8086)
            token: InfluxDB API token
            org: InfluxDB organization
            bucket: Target bucket name
            
        Returns:
            True if configuration successful, False otherwise
        """
        try:
            from influxdb_client import InfluxDBClient
            from influxdb_client.client.write_api import SYNCHRONOUS
            
            self.client = InfluxDBClient(url=url, token=token, org=org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.bucket = bucket
            self.org = org
            logger.info(f"InfluxDB configured: {url}")
            return True
        except ImportError:
            logger.warning("influxdb-client not installed. Install to enable InfluxDB support.")
            return False
        except Exception as e:
            logger.error(f"Failed to configure InfluxDB: {e}")
            return False
    
    def write_disk_metrics(self, disks: List[Dict[str, Any]], hostname: str = "diskwarden") -> bool:
        """
        Write disk metrics to InfluxDB.
        
        Args:
            disks: List of disk dictionaries from scanner.parse_hd_sentinel_output
            hostname: Hostname for tagging (default: "diskwarden")
            
        Returns:
            True if write successful, False otherwise
        """
        if not self.write_api:
            logger.debug("InfluxDB not configured, skipping metrics write")
            return False
        
        try:
            from influxdb_client.client.write_api import SYNCHRONOUS
            from influxdb_client.client.write.point import Point
            
            points = []
            
            for disk in disks:
                try:
                    # Extract numeric values
                    health_percent = self._parse_percent(disk.get('health', '0%'))
                    perf_percent = self._parse_percent(disk.get('performance', '0%'))
                    temp_c = self._parse_numeric(disk.get('temperature', '0'))
                    temp_max_c = self._parse_numeric(disk.get('highest_temp', '0'))
                    power_hours = self._parse_numeric(disk.get('power_on_time', '0'))
                    lifetime_days = self._parse_numeric(disk.get('lifetime', '0'))
                    
                    point = Point("disk_health") \
                        .tag("host", hostname) \
                        .tag("device", disk.get('device', 'unknown')) \
                        .tag("serial_no", disk.get('serial_no', 'unknown')) \
                        .tag("model_id", disk.get('model_id', 'unknown')) \
                        .field("health_percent", health_percent) \
                        .field("performance_percent", perf_percent) \
                        .field("temp_c", temp_c) \
                        .field("temp_max_c", temp_max_c) \
                        .field("power_on_hours", power_hours) \
                        .field("lifetime_days", lifetime_days) \
                        .time(datetime.utcnow())
                    
                    points.append(point)
                
                except Exception as e:
                    logger.warning(f"Failed to create point for disk {disk.get('device')}: {e}")
            
            if points:
                self.write_api.write(bucket=self.bucket, org=self.org, records=points)
                logger.debug(f"Wrote {len(points)} disk metrics to InfluxDB")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")
            return False
    
    @staticmethod
    def _parse_percent(value: str) -> float:
        """Extract percentage value from string (e.g., '85%' -> 85.0)."""
        try:
            return float(str(value).replace('%', '').strip())
        except (ValueError, AttributeError):
            return 0.0
    
    @staticmethod
    def _parse_numeric(value: str) -> float:
        """Extract numeric value from string, ignoring units."""
        try:
            import re
            match = re.search(r'(\d+\.?\d*)', str(value))
            return float(match.group(1)) if match else 0.0
        except (ValueError, AttributeError):
            return 0.0
    
    def close(self):
        """Close InfluxDB connection."""
        if self.client:
            try:
                self.client.close()
                logger.debug("InfluxDB connection closed")
            except Exception as e:
                logger.error(f"Error closing InfluxDB connection: {e}")
