#!/usr/bin/env python3
"""
Test position tracking functionality
"""

import sqlite3
from datetime import datetime
from hyperliquid_monitor.position_tracker import PositionTracker

def test_position_tracking():
    # Create a test database
    test_db = "test_positions.db"
    tracker = PositionTracker(test_db)
    
    # Create a mock fill for opening a position
    open_fill = {
        'time': str(int(datetime.now().timestamp() * 1000 - 3600000)),  # 1 hour ago
        'address': '0xtest',
        'coin': 'ETH',
        'side': 'A',  # BUY
        'sz': '1.0',
        'px': '2000.0',
        'dir': 'Open Long',
        'hash': '0x123',
        'fee': '0.1',
        'feeToken': 'USDC',
        'startPosition': '0.0',
        'closedPnl': '0.0'
    }
    
    # Create a mock fill for closing the position
    close_fill = {
        'time': str(int(datetime.now().timestamp() * 1000)),  # Now
        'address': '0xtest',
        'coin': 'ETH',
        'side': 'B',  # SELL
        'sz': '1.0',
        'px': '2100.0',
        'dir': 'Close Long',
        'hash': '0x456',
        'fee': '0.1',
        'feeToken': 'USDC',
        'startPosition': '1.0',
        'closedPnl': '100.0'
    }
    
    print("Testing position tracking...")
    
    # Process opening fill
    result1 = tracker.process_fill(open_fill, 1)
    print(f"Open position result: {result1}")
    
    # Process closing fill
    result2 = tracker.process_fill(close_fill, 2)
    print(f"Close position result: {result2}")
    
    if result2:
        print(f"Position duration: {result2['duration_formatted']}")
        print(f"PnL: {result2['pnl']}")
    
    # Check what's in the database
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM positions")
    positions = cursor.fetchall()
    print(f"Positions in database: {len(positions)}")
    for pos in positions:
        print(f"  {pos}")
    conn.close()

if __name__ == "__main__":
    test_position_tracking()