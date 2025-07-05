#!/usr/bin/env python3
"""
Silent background monitor - records to database only
"""

import sys
import logging
from hyperliquid_monitor import HyperliquidMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    addresses = [
        "0x010461C14e146ac35Fe42271BDC1134EE31C703a",
        # Add your addresses here
    ]
    
    logging.info(f"Starting silent monitor for {len(addresses)} addresses")
    
    # Silent mode - only records to database
    monitor = HyperliquidMonitor(
        addresses=addresses,
        db_path="trades.db",
        silent=True  # No console output, only database recording
    )
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        logging.info("Stopping monitor...")
        monitor.stop()
        logging.info("Monitor stopped")

if __name__ == "__main__":
    main()