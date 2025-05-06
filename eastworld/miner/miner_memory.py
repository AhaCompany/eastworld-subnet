import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional
import bittensor as bt
import os
import sys
import traceback

class MinerMemory:
    def __init__(self, db_path: str = 'miner_memory.db'):
        try:
            abs_path = os.path.abspath(db_path)
            print(f"\n[DEBUG-MEMORY] INIT: Using DB at: {abs_path}")
            sys.stdout.flush()  # Đảm bảo output hiển thị ngay lập tức
            
            # Kiểm tra file có tồn tại và kích thước
            if os.path.exists(abs_path):
                print(f"[DEBUG-MEMORY] INIT: DB file exists, size: {os.path.getsize(abs_path)} bytes")
            else:
                print(f"[DEBUG-MEMORY] INIT: DB file does not exist yet, will create")
            sys.stdout.flush()
            
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            print("[DEBUG-MEMORY] INIT: Connection created successfully")
            sys.stdout.flush()
            
            self._init_db()  # Gọi hàm tạo bảng
            
            # Kiểm tra xem bảng có thực sự được tạo không
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"[DEBUG-MEMORY] INIT: Tables after _init_db(): {tables}")
            sys.stdout.flush()
            
            bt.logging.info(f"MinerMemory: Using DB at: {abs_path}")
            
        except Exception as e:
            print(f"[DEBUG-MEMORY] INIT ERROR: {str(e)}")
            print(f"[DEBUG-MEMORY] INIT ERROR TRACEBACK: {traceback.format_exc()}")
            sys.stdout.flush()
            bt.logging.error(f"MinerMemory: Failed to initialize DB: {e}")

    def _init_db(self):
        try:
            print("[DEBUG-MEMORY] _init_db: Starting to create tables")
            sys.stdout.flush()
            
            c = self.conn.cursor()
            
            # Tạo bảng actions
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
            print("[DEBUG-MEMORY] _init_db: actions table query executed")
            sys.stdout.flush()
            
            # Tạo bảng inventory
            c.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    item TEXT,
                    status TEXT
                )
            ''')
            print("[DEBUG-MEMORY] _init_db: inventory table query executed")
            sys.stdout.flush()
            
            # Commit thay đổi
            self.conn.commit()
            print("[DEBUG-MEMORY] _init_db: Changes committed successfully")
            sys.stdout.flush()
            
            # Kiểm tra bảng sau khi tạo
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = c.fetchall()
            print(f"[DEBUG-MEMORY] _init_db: Tables after creation: {tables}")
            sys.stdout.flush()
            
            bt.logging.info("MinerMemory: DB tables initialized successfully")
            
        except Exception as e:
            print(f"[DEBUG-MEMORY] _init_db ERROR: {str(e)}")
            print(f"[DEBUG-MEMORY] _init_db ERROR TRACEBACK: {traceback.format_exc()}")
            sys.stdout.flush()
            bt.logging.error(f"MinerMemory: Failed to initialize DB tables: {e}")
            # Re-raise để caller biết có lỗi xảy ra
            raise

    def log_action(self, quest: str, action: str, direction: Optional[str], result: str, feedback: str, reflection: str):
        try:
            print(f"[DEBUG-MEMORY] log_action: Logging action: {action} for quest: {quest}")
            sys.stdout.flush()
            
            bt.logging.debug(f"MinerMemory: Logging action: {action} for quest: {quest}")
            c = self.conn.cursor()
            c.execute('''
                INSERT INTO actions (timestamp, quest, action, direction, result, feedback, reflection)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), quest, action, direction, result, feedback, reflection))
            self.conn.commit()
            bt.logging.info(f"MinerMemory: Successfully logged action: {action} for quest: {quest}")
            
            print(f"[DEBUG-MEMORY] log_action: Successfully logged action: {action}")
            sys.stdout.flush()
            
            return True
        except Exception as e:
            print(f"[DEBUG-MEMORY] log_action ERROR: {str(e)}")
            print(f"[DEBUG-MEMORY] log_action ERROR TRACEBACK: {traceback.format_exc()}")
            sys.stdout.flush()
            bt.logging.error(f"MinerMemory: Failed to log action: {e}")
            return False

    def get_recent_actions(self, quest: str, limit: int = 50) -> List[Tuple[str, str, str, str, str]]:
        try:
            print(f"[DEBUG-MEMORY] get_recent_actions: Fetching for quest: {quest}, limit: {limit}")
            sys.stdout.flush()
            
            c = self.conn.cursor()
            c.execute('''
                SELECT action, direction, result, feedback, reflection FROM actions
                WHERE quest=?
                ORDER BY id DESC
                LIMIT ?
            ''', (quest, limit))
            results = c.fetchall()
            bt.logging.debug(f"MinerMemory: Retrieved {len(results)} recent actions for quest: {quest}")
            
            print(f"[DEBUG-MEMORY] get_recent_actions: Retrieved {len(results)} actions")
            sys.stdout.flush()
            
            return results
        except Exception as e:
            print(f"[DEBUG-MEMORY] get_recent_actions ERROR: {str(e)}")
            print(f"[DEBUG-MEMORY] get_recent_actions ERROR TRACEBACK: {traceback.format_exc()}")
            sys.stdout.flush()
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
            print(f"[DEBUG-MEMORY] get_blocked_directions ERROR: {str(e)}")
            print(f"[DEBUG-MEMORY] get_blocked_directions ERROR TRACEBACK: {traceback.format_exc()}")
            sys.stdout.flush()
            bt.logging.error(f"MinerMemory: Failed to get blocked directions: {e}")
            return []

    def log_inventory(self, item: str, status: str):
        try:
            print(f"[DEBUG-MEMORY] log_inventory: Logging item: {item}, status: {status}")
            sys.stdout.flush()
            
            bt.logging.debug(f"MinerMemory: Logging inventory item: {item}, status: {status}")
            c = self.conn.cursor()
            c.execute('''
                INSERT INTO inventory (timestamp, item, status)
                VALUES (?, ?, ?)
            ''', (datetime.now().isoformat(), item, status))
            self.conn.commit()
            bt.logging.info(f"MinerMemory: Successfully logged inventory item: {item}")
            
            print(f"[DEBUG-MEMORY] log_inventory: Successfully logged item: {item}")
            sys.stdout.flush()
            
            return True
        except Exception as e:
            print(f"[DEBUG-MEMORY] log_inventory ERROR: {str(e)}")
            print(f"[DEBUG-MEMORY] log_inventory ERROR TRACEBACK: {traceback.format_exc()}")
            sys.stdout.flush()
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
            print(f"[DEBUG-MEMORY] inventory_is_full ERROR: {str(e)}")
            print(f"[DEBUG-MEMORY] inventory_is_full ERROR TRACEBACK: {traceback.format_exc()}")
            sys.stdout.flush()
            bt.logging.error(f"MinerMemory: Failed to check inventory status: {e}")
            return False

    def close(self):
        try:
            if self.conn:
                self.conn.close()
                bt.logging.info("MinerMemory: DB connection closed")
                print("[DEBUG-MEMORY] close: DB connection closed successfully")
                sys.stdout.flush()
        except Exception as e:
            print(f"[DEBUG-MEMORY] close ERROR: {str(e)}")
            print(f"[DEBUG-MEMORY] close ERROR TRACEBACK: {traceback.format_exc()}")
            sys.stdout.flush()
            bt.logging.error(f"MinerMemory: Error closing DB connection: {e}")
