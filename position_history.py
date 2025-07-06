#!/usr/bin/env python3
"""
Query position history and statistics
"""

import sys
from hyperliquid_monitor.position_tracker import PositionTracker
from datetime import datetime, timedelta

def main():
    if len(sys.argv) < 2:
        print("Usage: python position_history.py <address> [coin]")
        sys.exit(1)
    
    address = sys.argv[1]
    coin = sys.argv[2] if len(sys.argv) > 2 else None
    
    tracker = PositionTracker("trades.db")
    
    # Get open positions
    print("=== OPEN POSITIONS ===")
    open_positions = tracker.get_open_positions(address)
    if open_positions:
        for pos in open_positions:
            duration = datetime.now() - pos['entry_time']
            duration_str = tracker._format_duration(duration)
            print(f"{pos['coin']} {pos['side']}: {pos['size']} @ {pos['entry_price']:.4f} (Open for {duration_str})")
    else:
        print("No open positions")
    
    # Get closed positions
    print("\n=== RECENT CLOSED POSITIONS ===")
    closed_positions = tracker.get_position_history(address, coin, 20)
    if closed_positions:
        total_pnl = 0
        winning_trades = 0
        losing_trades = 0
        
        for pos in closed_positions:
            pnl_color = "+" if pos['pnl'] > 0 else ""
            if pos['pnl'] > 0:
                winning_trades += 1
            elif pos['pnl'] < 0:
                losing_trades += 1
            
            total_pnl += pos['pnl']
            
            print(f"{pos['coin']} {pos['side']}: {pos['size']} @ {pos['entry_price']:.4f} → {pos['exit_price']:.4f}")
            print(f"  Duration: {pos['duration_formatted']}, PnL: {pnl_color}{pos['pnl']:.2f}")
            print(f"  Opened: {pos['entry_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Closed: {pos['exit_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        
        # Statistics
        print("=== STATISTICS ===")
        print(f"Total PnL: {'+' if total_pnl > 0 else ''}{total_pnl:.2f}")
        print(f"Winning trades: {winning_trades}")
        print(f"Losing trades: {losing_trades}")
        if winning_trades + losing_trades > 0:
            win_rate = (winning_trades / (winning_trades + losing_trades)) * 100
            print(f"Win rate: {win_rate:.1f}%")
    else:
        print("No closed positions found")

if __name__ == "__main__":
    main()