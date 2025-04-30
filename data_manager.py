import json
import os
from datetime import datetime
from typing import List, Dict, Any

class DataManager:
    def __init__(self, file_path: str = "data.json"):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Ensure the data file exists"""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def load_logs(self) -> List[Dict[str, Any]]:
        """Load logs from JSON file"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_logs(self, logs: List[Dict[str, Any]]):
        """Save logs to JSON file"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def add_log(self, log_entry: Dict[str, Any]):
        """Add a new log entry"""
        logs = self.load_logs()
        logs.append(log_entry)
        self.save_logs(logs)

    def get_logs_by_time_period(self, time_delta) -> List[Dict[str, Any]]:
        """Get logs within a specific time period"""
        logs = self.load_logs()
        now = datetime.now()
        return [
            log for log in logs
            if now - datetime.fromisoformat(log['timestamp']) <= time_delta
        ] 