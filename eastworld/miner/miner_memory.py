import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional
import bittensor as bt
import os

class MinerMemory:
    def __init__(self, db_path: str = 'miner_memory.db'):
        try:
            abs_path = os.path.abspath(db_path)
            bt.logging.info(f"MinerMemory: Using DB at: {abs_path}")
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self._init_db()
        except Exception as e:
            bt.logging.error(f"MinerMemory: Failed to initialize DB: {e}")

    def _init_db(self):
        try:
            c = self.conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    quest TEXT,
                    action TEXT,
                    direction TEXT,
                    result TEXT,
                    feedback TEXT,
                    reflection TEXT
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    item TEXT,
                    status TEXT
                )
            ''')
            self.conn.commit()
            bt.logging.info("MinerMemory: DB tables initialized successfully")
        except Exception as e:
            bt.logging.error(f"MinerMemory: Failed to initialize DB tables: {e}")

    def log_action(self, quest: str, action: str, direction: Optional[str], result: str, feedback: str, reflection: str):
        try:
            bt.logging.debug(f"MinerMemory: Logging action: {action} for quest: {quest}")
            c = self.conn.cursor()
            c.execute('''
                INSERT INTO actions (timestamp, quest, action, direction, result, feedback, reflection)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), quest, action, direction, result, feedback, reflection))
            self.conn.commit()
            bt.logging.info(f"MinerMemory: Successfully logged action: {action} for quest: {quest}")
            return True
        except Exception as e:
            bt.logging.error(f"MinerMemory: Failed to log action: {e}")
            return False

    def get_recent_actions(self, quest: str, limit: int = 50) -> List[Tuple[str, str, str, str, str]]:
        try:
            c = self.conn.cursor()
            c.execute('''
                SELECT action, direction, result, feedback, reflection FROM actions
                WHERE quest=?
                ORDER BY id DESC
                LIMIT ?
            ''', (quest, limit))
            results = c.fetchall()
            bt.logging.debug(f"MinerMemory: Retrieved {len(results)} recent actions for quest: {quest}")
            return results
        except Exception as e:
            bt.logging.error(f"MinerMemory: Failed to get recent actions: {e}")
            return []

    def get_blocked_directions(self, quest: str, limit: int = 10) -> List[str]:
        try:
            c = self.conn.cursor()
            c.execute('''
                SELECT direction FROM actions
                WHERE quest=? AND result LIKE '%block%'
                ORDER BY id DESC
                LIMIT ?
            ''', (quest, limit))
            results = c.fetchall()
            bt.logging.debug(f"MinerMemory: Retrieved {len(results)} blocked directions for quest: {quest}")
            return [row[0] for row in results if row[0]]
        except Exception as e:
            bt.logging.error(f"MinerMemory: Failed to get blocked directions: {e}")
            return []

    def log_inventory(self, item: str, status: str):
        try:
            bt.logging.debug(f"MinerMemory: Logging inventory item: {item}, status: {status}")
            c = self.conn.cursor()
            c.execute('''
                INSERT INTO inventory (timestamp, item, status)
                VALUES (?, ?, ?)
            ''', (datetime.now().isoformat(), item, status))
            self.conn.commit()
            bt.logging.info(f"MinerMemory: Successfully logged inventory item: {item}")
            return True
        except Exception as e:
            bt.logging.error(f"MinerMemory: Failed to log inventory: {e}")
            return False

    def inventory_is_full(self) -> bool:
        try:
            c = self.conn.cursor()
            c.execute('''
                SELECT status FROM inventory
                ORDER BY id DESC LIMIT 1
            ''')
            row = c.fetchone()
            bt.logging.debug(f"MinerMemory: Inventory status: {row[0] if row else None}")
            return row and row[0] == 'full'
        except Exception as e:
            bt.logging.error(f"MinerMemory: Failed to check inventory status: {e}")
            return False

    def close(self):
        try:
            if self.conn:
                self.conn.close()
                bt.logging.info("MinerMemory: DB connection closed")
        except Exception as e:
            bt.logging.error(f"MinerMemory: Error closing DB connection: {e}")
