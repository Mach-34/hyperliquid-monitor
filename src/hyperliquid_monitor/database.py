import sqlite3
import threading
import os
from datetime import datetime
from typing import Dict, Optional

class TradeDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self.initialize()

    @property
    def conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path)
        return self._local.conn

    def initialize(self) -> None:
        """Initialize the database connection and create tables if they don't exist."""
        self.create_tables()

    def create_tables(self) -> None:
        """Create the necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Create fills table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            address TEXT,
            coin TEXT,
            side TEXT,
            size REAL,
            price REAL,
            direction TEXT,
            tx_hash TEXT,
            fee REAL,
            fee_token TEXT,
            start_position REAL,
            closed_pnl REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create orders table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            address TEXT,
            coin TEXT,
            action TEXT,
            side TEXT,
            size REAL,
            price REAL,
            order_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        self.conn.commit()

    def store_fill(self, fill: Dict) -> None:
        """Store a fill in the database."""
        cursor = self.conn.cursor()
        timestamp = datetime.fromtimestamp(int(fill.get("time", 0)) / 1000)
        
        cursor.execute('''
        INSERT INTO fills (
            timestamp, address, coin, side, size, price, direction, tx_hash, 
            fee, fee_token, start_position, closed_pnl
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            fill.get("address", "Unknown"),
            fill.get("coin", "Unknown"),
            "BUY" if fill.get("side", "B") == "A" else "SELL",
            float(fill.get("sz", 0)),
            float(fill.get("px", 0)),
            fill.get("dir", "Unknown"),
            fill.get("hash", "Unknown"),
            float(fill.get("fee", 0)),
            fill.get("feeToken", "Unknown"),
            float(fill.get("startPosition", 0)),
            float(fill.get("closedPnl", 0))
        ))
        
        self.conn.commit()

    def store_order(self, order: Dict, action: str) -> None:
        """Store an order in the database."""
        cursor = self.conn.cursor()
        timestamp = datetime.fromtimestamp(int(order.get("time", 0)) / 1000)
        
        # Get the placed or canceled order details
        order_details = order.get("placed", {}) if action == "placed" else order.get("canceled", {})
        
        cursor.execute('''
        INSERT INTO orders (timestamp, address, coin, action, side, size, price, order_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            order.get("address", "Unknown"),
            order.get("coin", "Unknown"),
            action,
            "BUY" if order_details.get("side", "B") == "A" else "SELL",
            float(order_details.get("sz", 0)),
            float(order_details.get("px", 0)),
            int(order_details.get("oid", 0))
        ))
        
        self.conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            delattr(self._local, 'conn')