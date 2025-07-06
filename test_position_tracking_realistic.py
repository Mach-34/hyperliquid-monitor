#!/usr/bin/env python3
"""
Test position tracking with realistic data
"""

import sqlite3
from datetime import datetime, timedelta
from hyperliquid_monitor.position_tracker import PositionTracker

def test_realistic_position():
    # Use the real database
    tracker = PositionTracker("trades.db")
    
    # Simulate a realistic position: Open Short -> Close Short
    base_time = datetime.now() - timedelta(minutes=30)
    
    # First, open a short position
    open_fill = {
        'time': str(int(base_time.timestamp() * 1000)),
        'address': '0xtest123',
        'coin': 'SUI',
        'side': 'A',  # BUY to open short
        'sz': '100.0',
        'px': '2.90',
        'dir': 'Open Short',
        'hash': '0xopen',
        'fee': '0.01',
        'feeToken': 'USDC',
        'startPosition': '0.0',
        'closedPnl': '0.0'
    }
    
    # Then close the short position
    close_time = base_time + timedelta(minutes=25)
    close_fill = {
        'time': str(int(close_time.timestamp() * 1000)),
        'address': '0xtest123',
        'coin': 'SUI',
        'side': 'B',  # SELL to close short
        'sz': '100.0',
        'px': '2.85',
        'dir': 'Close Short',
        'hash': '0xclose',
        'fee': '0.01',
        'feeToken': 'USDC',
        'startPosition': '100.0',
        'closedPnl': '5.0'  # Profit of $5
    }
    
    print("Testing realistic position tracking...")
    
    # Process opening fill
    print("Opening position...")
    result1 = tracker.process_fill(open_fill, 9999)
    print(f"Open result: {result1}")
    
    # Check if position was created
    conn = sqlite3.connect("trades.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM positions WHERE address = ? AND coin = ? AND status = 'OPEN'", 
                   ('0xtest123', 'SUI'))
    open_positions = cursor.fetchall()
    print(f"Open positions: {len(open_positions)}")
    for pos in open_positions:
        print(f"  Position: {pos}")
    
    # Process closing fill
    print("\nClosing position...")
    result2 = tracker.process_fill(close_fill, 10000)
    print(f"Close result: {result2}")
    
    if result2:
        print(f"\n✅ Position tracked successfully!")
        print(f"   Duration: {result2['duration_formatted']}")
        print(f"   Entry: ${result2['entry_price']:.4f}")
        print(f"   Exit: ${result2['exit_price']:.4f}")
        print(f"   PnL: ${result2['pnl']:.2f}")
    
    # Check final state
    cursor.execute("SELECT * FROM positions WHERE address = ? AND coin = ?", 
                   ('0xtest123', 'SUI'))
    all_positions = cursor.fetchall()
    print(f"\nFinal positions count: {len(all_positions)}")
    for pos in all_positions:
        print(f"  {pos}")
    
    conn.close()

if __name__ == "__main__":
    test_realistic_position()