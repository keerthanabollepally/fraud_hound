import sqlite3
import os
from datetime import datetime

DB_PATH = "db.sqlite"

def init_db():
    """Create tables with timestamp column"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scam_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            risk_score REAL NOT NULL,
            source TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def insert_event(text, risk_score, source):
    """Insert scam event with timestamp"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO scam_events (text, risk_score, source) VALUES (?, ?, ?)",
        (text, risk_score, source)
    )
    
    conn.commit()
    conn.close()
