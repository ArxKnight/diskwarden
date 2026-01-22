"""
Persistent disk state tracking for alert suppression.
Uses SQLite for reliable ACID transactions and locking.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DiskStateTracker:
    """Manages persistent disk state to prevent alert spam."""
    
    # State constants
    STATE_OK = "OK"
    STATE_BELOW_THRESHOLD = "BELOW_THRESHOLD"
    
    def __init__(self, db_path: str = "diskwarden_state.db"):
        """
        Initialize the state tracker.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Create the database schema if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS disk_state (
                        disk_id TEXT PRIMARY KEY,
                        device TEXT,
                        serial_no TEXT,
                        state TEXT DEFAULT 'OK',
                        last_state_change TIMESTAMP,
                        last_alert_time TIMESTAMP,
                        health_percent INTEGER,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.debug("Database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_state(self, disk_id: str) -> Tuple[str, Optional[datetime]]:
        """
        Get the current state of a disk.
        
        Args:
            disk_id: Unique disk identifier
            
        Returns:
            Tuple of (state, last_state_change_time)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cursor = conn.execute(
                    "SELECT state, last_state_change FROM disk_state WHERE disk_id = ?",
                    (disk_id,)
                )
                row = cursor.fetchone()
                if row:
                    state, timestamp_str = row
                    change_time = datetime.fromisoformat(timestamp_str) if timestamp_str else None
                    return state, change_time
                return self.STATE_OK, None
        except Exception as e:
            logger.error(f"Error reading state for disk {disk_id}: {e}")
            return self.STATE_OK, None
    
    def update_disk(self, disk_id: str, device: str, serial_no: str, 
                   health_percent: int, threshold: int) -> Dict[str, Any]:
        """
        Update disk state and determine if an alert should be sent.
        
        Args:
            disk_id: Unique disk identifier
            device: Device name (e.g., /dev/sda)
            serial_no: Serial number
            health_percent: Current health percentage
            threshold: Health threshold percentage
            
        Returns:
            Dict with keys:
            - alert_type: "transition", "recovery", "reminder", None
            - old_state: Previous state
            - new_state: Current state
        """
        current_state, last_change = self.get_state(disk_id)
        
        # Determine new state
        new_state = self.STATE_BELOW_THRESHOLD if health_percent < threshold else self.STATE_OK
        
        # Determine alert type
        alert_type = None
        state_changed = current_state != new_state
        
        if state_changed:
            # Only alert on transitions
            if new_state == self.STATE_BELOW_THRESHOLD:
                alert_type = "transition"
            elif new_state == self.STATE_OK:
                alert_type = "recovery"
        
        # Update database
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                if state_changed:
                    # State transition - reset last_alert_time
                    conn.execute("""
                        INSERT OR REPLACE INTO disk_state 
                        (disk_id, device, serial_no, state, last_state_change, last_alert_time, health_percent, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (disk_id, device, serial_no, new_state, datetime.now().isoformat(), 
                          datetime.now().isoformat() if alert_type else None, health_percent))
                else:
                    # No state change - keep existing alert times
                    conn.execute("""
                        INSERT OR REPLACE INTO disk_state 
                        (disk_id, device, serial_no, state, last_state_change, health_percent, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (disk_id, device, serial_no, new_state, 
                          last_change.isoformat() if last_change else datetime.now().isoformat(),
                          health_percent))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update disk state for {disk_id}: {e}")
        
        return {
            "alert_type": alert_type,
            "old_state": current_state,
            "new_state": new_state
        }
    
    def should_send_reminder(self, disk_id: str, cooldown_minutes: int) -> bool:
        """
        Check if a reminder alert should be sent (cooldown elapsed).
        
        Args:
            disk_id: Unique disk identifier
            cooldown_minutes: Minutes to wait between reminders (0 = disabled)
            
        Returns:
            True if reminder should be sent
        """
        if cooldown_minutes <= 0:
            return False
        
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cursor = conn.execute(
                    "SELECT last_alert_time, state FROM disk_state WHERE disk_id = ?",
                    (disk_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return False
                
                last_alert_str, state = row
                
                # Only send reminder if disk is still below threshold
                if state != self.STATE_BELOW_THRESHOLD:
                    return False
                
                if not last_alert_str:
                    return True
                
                last_alert = datetime.fromisoformat(last_alert_str)
                cooldown_expiry = last_alert + timedelta(minutes=cooldown_minutes)
                return datetime.now() >= cooldown_expiry
                
        except Exception as e:
            logger.error(f"Error checking reminder for disk {disk_id}: {e}")
            return False
    
    def update_last_alert_time(self, disk_id: str):
        """Update the last alert time for a disk (for cooldown tracking)."""
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                conn.execute(
                    "UPDATE disk_state SET last_alert_time = CURRENT_TIMESTAMP WHERE disk_id = ?",
                    (disk_id,)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update alert time for {disk_id}: {e}")
    
    def get_all_states(self) -> Dict[str, Dict]:
        """
        Get all tracked disk states.
        
        Returns:
            Dictionary mapping disk_id to state info
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cursor = conn.execute("SELECT disk_id, state, health_percent FROM disk_state")
                return {
                    row[0]: {"state": row[1], "health_percent": row[2]}
                    for row in cursor.fetchall()
                }
        except Exception as e:
            logger.error(f"Error reading all states: {e}")
            return {}
    
    def cleanup_old_entries(self, days: int = 90):
        """Remove state entries for disks not seen in N days."""
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cutoff = datetime.now() - timedelta(days=days)
                conn.execute(
                    "DELETE FROM disk_state WHERE updated_at < ?",
                    (cutoff.isoformat(),)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error cleaning up old entries: {e}")
