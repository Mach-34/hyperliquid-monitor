#!/usr/bin/env python3
"""
Example script to run Hyperliquid Monitor live
"""

from hyperliquid_monitor import HyperliquidMonitor
from hyperliquid_monitor.types import Trade
from datetime import datetime

def print_trade(trade: Trade):
    """Print trade information to console with colors"""
    timestamp = trade.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    # Color codes
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    
    # Choose color based on trade type and side
    color = GREEN if trade.side == "BUY" else RED
    
    print(f"\n{BLUE}[{timestamp}]{RESET} New {trade.trade_type}:")
    print(f"Address: {trade.address}")
    print(f"Coin: {trade.coin}")
    print(f"{color}Side: {trade.side}{RESET}")
    print(f"Size: {trade.size}")
    print(f"Price: {trade.price}")

    print(f"Trade: {trade}")
    
    if trade.trade_type == "FILL":
        print(f"Direction: {trade.direction}")
        if trade.closed_pnl and trade.closed_pnl != 0:
            pnl_color = GREEN if trade.closed_pnl > 0 else RED
            print(f"PnL: {pnl_color}{trade.closed_pnl:.2f}{RESET}")
        if trade.fee:
            print(f"Fee: {trade.fee} {trade.fee_token}")
        print(f"Hash: {trade.tx_hash}")
    elif trade.trade_type in ["ORDER_PLACED", "ORDER_CANCELLED"]:
        print(f"Order ID: {trade.order_id}")

def main():
    # Replace with actual addresses you want to monitor
    addresses = [
        "0x0dd5db9c3748486e747c6a123727f472668cf6ee",  # Example address
        # Add more addresses here
    ]
    
    print("Starting Hyperliquid Monitor...")
    print(f"Monitoring {len(addresses)} addresses")
    print("Press Ctrl+C to stop\n")
    
    # Create monitor with database storage and console notifications
    monitor = HyperliquidMonitor(
        addresses=addresses,
        db_path="trades.db",  # Will store all trades in SQLite
        callback=print_trade   # Print to console
    )
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop()
        print("Monitor stopped.")

if __name__ == "__main__":
    main()