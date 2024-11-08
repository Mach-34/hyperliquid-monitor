# Hyperliquid Monitor

A Python package for monitoring trades and orders on Hyperliquid DEX in real-time. This package allows you to track specific addresses and receive notifications when trades are executed or orders are placed/cancelled.

## Features

- Real-time monitoring of trades and orders
- Support for multiple addresses
- Optional SQLite database storage
- Callback system for custom notifications
- Clean shutdown handling
- Proper trade type definitions using dataclasses

## Installation

### Using Poetry (recommended)

```bash
poetry add hyperliquid-monitor
```

### Using pip

```bash
pip install hyperliquid-monitor
```

## Quick Start

Here's a simple example that monitors an address and prints trades to the console:

```python
from hyperliquid_monitor import HyperliquidMonitor
from hyperliquid_monitor.types import Trade

def handle_trade(trade: Trade):
    print(f"\nNew {trade.trade_type}:")
    print(f"Time: {trade.timestamp}")
    print(f"Address: {trade.address}")
    print(f"Coin: {trade.coin}")
    print(f"Side: {trade.side}")
    print(f"Size: {trade.size}")
    print(f"Price: {trade.price}")

# List of addresses to monitor
addresses = [
    "0x010461C14e146ac35Fe42271BDC1134EE31C703a"
]

# Create and start the monitor
monitor = HyperliquidMonitor(
    addresses=addresses,
    db_path="trades.db",  # Optional: remove to disable database
    callback=handle_trade
)

monitor.start()
```

## Trade Object Structure

The `Trade` object contains the following information:

```python
@dataclass
class Trade:
    timestamp: datetime
    address: str
    coin: str
    side: Literal["BUY", "SELL"]
    size: float
    price: float
    trade_type: Literal["FILL", "ORDER_PLACED", "ORDER_CANCELLED"]
    direction: Optional[str] = None
    tx_hash: Optional[str] = None
    fee: Optional[float] = None
    fee_token: Optional[str] = None
    start_position: Optional[float] = None
    closed_pnl: Optional[float] = None
    order_id: Optional[int] = None
```

## Database Storage

If you provide a `db_path`, trades will be stored in an SQLite database with two tables:

### Fills Table
- timestamp
- address
- coin
- side
- size
- price
- direction
- tx_hash
- fee
- fee_token
- start_position
- closed_pnl

### Orders Table
- timestamp
- address
- coin
- action
- side
- size
- price
- order_id

## Example: Telegram Bot Integration

Here's how you can integrate this monitor with a Telegram bot:

```python
from telegram.ext import Updater
from hyperliquid_monitor import HyperliquidMonitor
from hyperliquid_monitor.types import Trade

def send_telegram_message(trade: Trade, bot, chat_id):
    message = f"""
🔔 New {trade.trade_type}

Asset: {trade.coin}
Type: {trade.side}
Size: {trade.size}
Price: {trade.price}
Time: {trade.timestamp}
"""
    if trade.trade_type == "FILL":
        message += f"""
Direction: {trade.direction}
PnL: {trade.closed_pnl}
Hash: {trade.tx_hash}
"""
    
    bot.send_message(chat_id=chat_id, text=message)

def main():
    # Initialize your Telegram bot
    updater = Updater("YOUR_BOT_TOKEN")
    bot = updater.bot
    chat_id = "YOUR_CHAT_ID"

    # Create callback function
    def handle_trade(trade: Trade):
        send_telegram_message(trade, bot, chat_id)

    # Initialize and start the monitor
    monitor = HyperliquidMonitor(
        addresses=["0x..."],
        db_path="trades.db",
        callback=handle_trade
    )
    
    monitor.start()

if __name__ == "__main__":
    main()
```

## Error Handling

The monitor includes built-in error handling and will:
- Catch and log exceptions during trade processing
- Properly close database connections on shutdown
- Continue monitoring even if individual trades fail to process

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built on top of the official Hyperliquid Python SDK
- Inspired by the need for real-time trade monitoring in DeFi