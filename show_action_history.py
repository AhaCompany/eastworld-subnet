#!/usr/bin/env python3
# Filename: show_action_history.py
# Purpose: Hiển thị lịch sử các action từ miner_memory.db

import sqlite3
import os
from datetime import datetime
import sys
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='View action history from miner_memory.db')
    parser.add_argument('--limit', type=int, default=300, help='Số lượng action muốn xem (mặc định: 300)')
    parser.add_argument('--quest', type=str, default='', help='Lọc theo quest (mặc định: tất cả)')
    parser.add_argument('--status', type=str, choices=['SUCCESS', 'FAILURE', 'pending', 'all'], 
                        default='all', help='Lọc theo status (SUCCESS/FAILURE/pending/all)')
    parser.add_argument('--action-type', type=str, default='', 
                        help='Lọc theo loại action (vd: move_in_direction, inspect, talk_to)')
    return parser.parse_args()

def show_action_history(limit=300, quest='', status='all', action_type=''):
    # Đường dẫn đến file DB
    db_path = os.path.join(os.getcwd(), 'miner_memory.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)
    
    try:
        # Kết nối đến DB
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Xây dựng câu query với các điều kiện lọc
        query = "SELECT id, action, direction, result, feedback, timestamp FROM actions "
        conditions = []
        params = []
        
        if quest:
            conditions.append("quest = ?")
            params.append(quest)
        
        if status != 'all':
            conditions.append("result LIKE ?")
            params.append(f"%{status}%")
            
        if action_type:
            conditions.append("action = ?")
            params.append(action_type)
            
        if conditions:
            query += "WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        
        # Thực thi query
        cursor.execute(query, params)
        actions = cursor.fetchall()
        
        # Hiển thị header
        print("\n# History Action Log")
        print("<<<")
        
        # Hiển thị các action theo định dạng yêu cầu
        for action in actions:
            action_id, action_name, direction, result, feedback, timestamp = action
            
            # Định dạng direction
            direction_str = f" ({direction})" if direction else ""
            
            # In action với định dạng yêu cầu
            print(f"#{action_id}: {action_name}{direction_str}, Result: {result}, Feedback: {feedback}")
            
            # Thêm output từ agent nếu có (đây chỉ là ví dụ, trong thực tế sẽ không có output này)
            if "Talking to Agent" in feedback and "Agent 126" not in feedback:
                pass  # Remove example agent responses as they're not actually in the DB
        
        print(">>>")
        
        # In thêm thống kê
        print(f"\nThống kê:")
        print(f"- Tổng số action: {len(actions)}")
        
        # Đếm số action theo kết quả
        cursor.execute("SELECT result, COUNT(*) FROM actions GROUP BY result")
        result_counts = cursor.fetchall()
        for result_type, count in result_counts:
            print(f"- {result_type}: {count} actions")
        
        # Đóng kết nối
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    args = parse_args()
    show_action_history(
        limit=args.limit, 
        quest=args.quest, 
        status=args.status,
        action_type=args.action_type
    )
