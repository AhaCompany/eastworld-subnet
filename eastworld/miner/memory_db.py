# The MIT License (MIT)
# Copyright © 2025 Eastworld AI

import os
import sqlite3
import json
import datetime
from typing import List, Dict, Any, Optional

class JuniorMemoryDB:
    """Class to handle persistent storage of Junior Agent memory in SQLite."""
    
    def __init__(self, db_path="eastworld/miner/junior_memory.db"):
        """Initialize the database connection and create tables if they don't exist."""
        self.db_path = db_path
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Connect to the database
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Create tables if they don't exist
        self._create_tables()
    
    def _create_tables(self):
        """Create the necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Create reflection memory table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reflection_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create action memory table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            feedback TEXT NOT NULL,
            repeat_times INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        self.conn.commit()
    
    def add_reflection(self, reflection: str):
        """Add a reflection to the database."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO reflection_memory (content) VALUES (?)",
            (reflection,)
        )
        self.conn.commit()
    
    def add_action(self, action_log: Dict[str, Any]):
        """Add an action log to the database."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO action_memory (timestamp, action, feedback, repeat_times) VALUES (?, ?, ?, ?)",
            (
                action_log["timestamp"].isoformat(),
                action_log["action"],
                action_log["feedback"],
                action_log["repeat_times"]
            )
        )
        self.conn.commit()
    
    def get_reflections(self, limit: int = 40) -> List[str]:
        """Get the most recent reflections from the database."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT content FROM reflection_memory ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return [row["content"] for row in cursor.fetchall()]
    
    def get_actions(self, limit: int = 40) -> List[Dict[str, Any]]:
        """Get the most recent action logs from the database."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT timestamp, action, feedback, repeat_times FROM action_memory ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        
        result = []
        for row in cursor.fetchall():
            result.append({
                "timestamp": datetime.datetime.fromisoformat(row["timestamp"]),
                "action": row["action"],
                "feedback": row["feedback"],
                "repeat_times": row["repeat_times"]
            })
        return result
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
