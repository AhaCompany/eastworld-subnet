#!/usr/bin/env python3
# Script to show information from Junior Agent memory database

import sqlite3
import datetime
import argparse
from collections import Counter
from tabulate import tabulate
import re

# Đường dẫn đến file cơ sở dữ liệu
DB_PATH = "eastworld/miner/junior_memory.db"

def connect_db():
    """Kết nối đến cơ sở dữ liệu và thiết lập row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables_if_not_exist(conn):
    """Tạo các bảng nếu chúng chưa tồn tại"""
    cursor = conn.cursor()
    
    # Tạo bảng reflection_memory
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reflection_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tạo bảng action_memory
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
    
    conn.commit()

def show_reflections(conn, limit=10):
    """Hiển thị dữ liệu từ bảng reflection_memory"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, content, timestamp FROM reflection_memory ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    
    print(f"\n=== Reflection Memory ({len(rows)} entries) ===\n")
    
    for row in rows:
        print(f"ID: {row['id']} | {row['timestamp']} | {row['content']}")
        print("-" * 80)

def show_actions(conn, limit=10, status_filter=None):
    """Hiển thị dữ liệu từ bảng action_memory với bộ lọc trạng thái"""
    cursor = conn.cursor()
    
    # Lấy tất cả các hành động
    cursor.execute(
        "SELECT id, timestamp, action, feedback, repeat_times, created_at FROM action_memory ORDER BY created_at DESC"
    )
    all_rows = cursor.fetchall()
    
    # Lọc theo trạng thái nếu có
    filtered_rows = []
    status_counter = Counter()
    
    for row in all_rows:
        feedback = row['feedback']
        
        # Xác định trạng thái của hành động
        if re.search(r'\[SUCCESS\]', feedback) or re.search(r'completed|success|succeeded|thành công|hoàn thành', feedback, re.IGNORECASE):
            row_status = 'SUCCESS'
        elif re.search(r'\[FAILURE\]', feedback) or re.search(r'fail|error|exception|cannot|can\'t|blocked|không thành công|thất bại', feedback, re.IGNORECASE):
            row_status = 'FAILURE'
        elif re.search(r'\[PENDING\]', feedback) or re.search(r'in progress|pending|waiting|đang xử lý|chờ', feedback, re.IGNORECASE):
            row_status = 'PENDING'
        else:
            row_status = 'UNKNOWN'
        
        # Đếm số lượng mỗi trạng thái
        status_counter[row_status] += 1
        
        # Thêm vào danh sách nếu phù hợp với bộ lọc
        if status_filter is None or status_filter.upper() == 'ALL' or status_filter.upper() == row_status:
            filtered_rows.append((row, row_status))
    
    # Giới hạn số lượng kết quả
    filtered_rows = filtered_rows[:limit]
    
    if status_filter and status_filter.upper() != 'ALL':
        print(f"\n=== Action Memory ({len(filtered_rows)} entries with status {status_filter.upper()}) ===\n")
    else:
        print(f"\n=== Action Memory ({len(filtered_rows)} entries) ===\n")
    
    for row, status in filtered_rows:
        print(f"ID: {row['id']} | {row['timestamp']} | Status: {status} | Repeat: {row['repeat_times']}")
        print(f"Action: {row['action']} | Feedback: {row['feedback']}")
        print("-" * 80)

def analyze_action_status(conn):
    """Phân tích trạng thái hành động từ feedback"""
    cursor = conn.cursor()
    cursor.execute("SELECT feedback FROM action_memory")
    rows = cursor.fetchall()
    
    if not rows:
        print("\n=== Thống kê trạng thái hành động ===")
        print("Không có dữ liệu hành động để phân tích.")
        return
    
    status_counter = Counter()
    
    for row in rows:
        feedback = row['feedback']
        
        # Phân loại trạng thái dựa trên nội dung feedback
        if re.search(r'\[SUCCESS\]', feedback) or re.search(r'completed|success|succeeded|thành công|hoàn thành', feedback, re.IGNORECASE):
            status_counter['SUCCESS'] += 1
        elif re.search(r'\[FAILURE\]', feedback) or re.search(r'fail|error|exception|cannot|can\'t|blocked|không thành công|thất bại', feedback, re.IGNORECASE):
            status_counter['FAILURE'] += 1
        elif re.search(r'\[PENDING\]', feedback) or re.search(r'in progress|pending|waiting|đang xử lý|chờ', feedback, re.IGNORECASE):
            status_counter['PENDING'] += 1
        else:
            status_counter['UNKNOWN'] += 1
    
    # Tạo bảng thống kê
    status_table = []
    for status, count in status_counter.items():
        status_table.append([status, count])
    
    print("\n=== Thống kê trạng thái hành động ===")
    print(tabulate(status_table, headers=["Trạng thái", "Số lượng"], tablefmt="grid"))

def parse_arguments():
    """Xử lý tham số dòng lệnh"""
    parser = argparse.ArgumentParser(description='Hiển thị thông tin từ cơ sở dữ liệu Junior Agent memory')
    parser.add_argument('--status', type=str, choices=['all', 'SUCCESS', 'FAILURE', 'PENDING', 'UNKNOWN'], 
                        default='all', help='Lọc theo trạng thái hành động')
    parser.add_argument('--limit', type=int, default=10, help='Giới hạn số lượng kết quả hiển thị')
    parser.add_argument('--show-reflections', action='store_true', help='Hiển thị dữ liệu reflection')
    parser.add_argument('--show-actions', action='store_true', help='Hiển thị dữ liệu action')
    parser.add_argument('--show-stats', action='store_true', help='Hiển thị thống kê trạng thái')
    
    args = parser.parse_args()
    
    # Mặc định hiển thị actions và statistics
    if not (args.show_reflections or args.show_actions or args.show_stats):
        args.show_actions = True
        args.show_stats = True
    
    return args

def main():
    # Initialize conn to None to avoid UnboundLocalError
    conn = None
    try:
        # Xử lý tham số dòng lệnh
        args = parse_arguments()
        
        conn = connect_db()
        
        # Tạo các bảng nếu chúng chưa tồn tại
        create_tables_if_not_exist(conn)
        
        # Kiểm tra xem các bảng có dữ liệu không
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='reflection_memory' OR name='action_memory')")
        tables = [row['name'] for row in cursor.fetchall()]
        
        if 'reflection_memory' not in tables or 'action_memory' not in tables:
            print("\nCảnh báo: Một số bảng cần thiết chưa tồn tại. Đã tạo các bảng mới.")
            print("Hãy chạy ứng dụng chính để tạo dữ liệu trước khi sử dụng script này.\n")
            return
        
        # Lấy số lượng dữ liệu
        cursor.execute("SELECT COUNT(*) as count FROM reflection_memory")
        reflection_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM action_memory")
        action_count = cursor.fetchone()['count']
        
        if reflection_count == 0 and action_count == 0:
            print("\nCảnh báo: Cơ sở dữ liệu không có dữ liệu. Hãy chạy ứng dụng chính để tạo dữ liệu.")
            return
        
        # Hiển thị dữ liệu chi tiết dựa trên tham số
        if args.show_reflections:
            show_reflections(conn, args.limit)
        
        if args.show_actions:
            show_actions(conn, args.limit, args.status)
        
        # Hiển thị thông tin tổng quan và thống kê ở cuối
        print(f"\n=== Thống kê cơ sở dữ liệu Junior Memory ===")
        print(f"Tổng số reflection: {reflection_count}")
        print(f"Tổng số action: {action_count}")
        
        # Phân tích trạng thái hành động
        if args.show_stats:
            analyze_action_status(conn)
        
    except sqlite3.Error as e:
        print(f"Lỗi SQLite: {e}")
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
