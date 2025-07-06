import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

@dataclass
class Position:
    address: str
    coin: str
    side: str  # "LONG" or "SHORT"
    size: float
    entry_price: float
    entry_time: datetime
    entry_fill_id: int

class PositionTracker:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_position_table()
    
    def _init_position_table(self):
        """Initialize position tracking table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create positions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL,
            coin TEXT NOT NULL,
            side TEXT NOT NULL,  -- 'LONG' or 'SHORT'
            size REAL NOT NULL,
            entry_price REAL NOT NULL,
            entry_time DATETIME NOT NULL,
            entry_fill_id INTEGER NOT NULL,
            exit_price REAL,
            exit_time DATETIME,
            exit_fill_id INTEGER,
            duration_seconds INTEGER,
            pnl REAL,
            status TEXT DEFAULT 'OPEN',  -- 'OPEN' or 'CLOSED'
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entry_fill_id) REFERENCES fills(id),
            FOREIGN KEY (exit_fill_id) REFERENCES fills(id)
        )
        ''')
        
        # Create indexes
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_positions_address_coin ON positions(address, coin)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_positions_entry_time ON positions(entry_time)
        ''')
        
        conn.commit()
        conn.close()
    
    def process_fill(self, fill_data: Dict, fill_id: int) -> Optional[Dict]:
        """
        Process a fill and update position tracking
        Returns position info if a position was closed
        """
        direction = fill_data.get('dir', '')
        address = fill_data.get('address', 'Unknown')
        coin = fill_data.get('coin', 'Unknown')
        timestamp = datetime.fromtimestamp(int(fill_data.get('time', 0)) / 1000)
        price = float(fill_data.get('px', 0))
        size = float(fill_data.get('sz', 0))
        side = "BUY" if fill_data.get('side', 'B') == 'A' else "SELL"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        result = None
        
        try:
            # Handle position opening
            if 'Open' in direction:
                position_side = 'LONG' if 'Long' in direction else 'SHORT'
                self._open_position(cursor, address, coin, position_side, size, price, timestamp, fill_id)
            
            # Handle position closing
            elif 'Close' in direction:
                pnl = float(fill_data.get('closedPnl', 0))
                result = self._close_position(cursor, address, coin, direction, size, price, timestamp, fill_id, pnl)
            
            # Handle position flipping (Long > Short or Short > Long)
            elif '>' in direction:
                # Close existing position first
                old_side = 'LONG' if 'Long >' in direction else 'SHORT'
                new_side = 'SHORT' if '> Short' in direction else 'LONG'
                
                pnl = float(fill_data.get('closedPnl', 0))
                close_result = self._close_position(cursor, address, coin, f"Close {old_side.title()}", size, price, timestamp, fill_id, pnl)
                
                # Open new position (position flip usually involves larger size)
                # The new position size would be the difference if any
                if close_result:
                    # For flips, we need to handle the new position opening
                    # This is complex as it depends on the original position size vs trade size
                    pass
                
                result = close_result
            # Note: Unhandled directions are ignored (e.g., market making, other trade types)
            
            conn.commit()
        
        except Exception as e:
            conn.rollback()
            print(f"Error processing position: {e}")
        
        finally:
            conn.close()
        
        return result
    
    def _open_position(self, cursor, address: str, coin: str, side: str, size: float, price: float, timestamp: datetime, fill_id: int):
        """Open a new position"""
        cursor.execute('''
        INSERT INTO positions (address, coin, side, size, entry_price, entry_time, entry_fill_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (address, coin, side, size, price, timestamp, fill_id))
    
    def _close_position(self, cursor, address: str, coin: str, direction: str, size: float, price: float, timestamp: datetime, fill_id: int, pnl: float = 0.0) -> Optional[Dict]:
        """Close existing position and return position info"""
        # Determine which side we're closing
        closing_side = 'LONG' if 'Long' in direction else 'SHORT'
        
        # Find the most recent open position for this address/coin/side
        cursor.execute('''
        SELECT id, size, entry_price, entry_time, entry_fill_id
        FROM positions 
        WHERE address = ? AND coin = ? AND side = ? AND status = 'OPEN'
        ORDER BY entry_time DESC
        LIMIT 1
        ''', (address, coin, closing_side))
        
        position = cursor.fetchone()
        if not position:
            return None
        
        pos_id, pos_size, entry_price, entry_time_str, entry_fill_id = position
        
        # Handle different datetime formats
        try:
            if isinstance(entry_time_str, str):
                if 'T' in entry_time_str:
                    entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00').replace('+00:00', ''))
                else:
                    entry_time = datetime.strptime(entry_time_str, '%Y-%m-%d %H:%M:%S.%f')
            else:
                entry_time = entry_time_str
        except Exception as e:
            print(f"Error parsing entry time {entry_time_str}: {e}")
            return None
        
        # Calculate duration
        duration = timestamp - entry_time
        duration_seconds = int(duration.total_seconds())
        
        # PnL is passed as parameter
        
        # Update position as closed
        cursor.execute('''
        UPDATE positions 
        SET exit_price = ?, exit_time = ?, exit_fill_id = ?, duration_seconds = ?, pnl = ?, status = 'CLOSED'
        WHERE id = ?
        ''', (price, timestamp, fill_id, duration_seconds, pnl, pos_id))
        
        return {
            'position_id': pos_id,
            'address': address,
            'coin': coin,
            'side': closing_side,
            'size': pos_size,
            'entry_price': entry_price,
            'entry_time': entry_time,
            'exit_price': price,
            'exit_time': timestamp,
            'duration': duration,
            'duration_seconds': duration_seconds,
            'duration_formatted': self._format_duration(duration),
            'pnl': pnl
        }
    
    def _format_duration(self, duration: timedelta) -> str:
        """Format duration in human-readable format"""
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}m {seconds}s"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        else:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            return f"{days}d {hours}h"
    
    def get_open_positions(self, address: str = None) -> List[Dict]:
        """Get all open positions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if address:
            cursor.execute('''
            SELECT * FROM positions WHERE address = ? AND status = 'OPEN'
            ORDER BY entry_time DESC
            ''', (address,))
        else:
            cursor.execute('''
            SELECT * FROM positions WHERE status = 'OPEN'
            ORDER BY entry_time DESC
            ''')
        
        positions = []
        for row in cursor.fetchall():
            positions.append({
                'id': row[0],
                'address': row[1],
                'coin': row[2],
                'side': row[3],
                'size': row[4],
                'entry_price': row[5],
                'entry_time': datetime.fromisoformat(row[6].replace('Z', '+00:00').replace('+00:00', '')),
                'entry_fill_id': row[7]
            })
        
        conn.close()
        return positions
    
    def get_position_history(self, address: str, coin: str = None, limit: int = 50) -> List[Dict]:
        """Get position history for an address"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if coin:
            cursor.execute('''
            SELECT * FROM positions 
            WHERE address = ? AND coin = ? AND status = 'CLOSED'
            ORDER BY exit_time DESC
            LIMIT ?
            ''', (address, coin, limit))
        else:
            cursor.execute('''
            SELECT * FROM positions 
            WHERE address = ? AND status = 'CLOSED'
            ORDER BY exit_time DESC
            LIMIT ?
            ''', (address, limit))
        
        positions = []
        for row in cursor.fetchall():
            entry_time = datetime.fromisoformat(row[6].replace('Z', '+00:00').replace('+00:00', ''))
            exit_time = datetime.fromisoformat(row[9].replace('Z', '+00:00').replace('+00:00', '')) if row[9] else None
            duration = timedelta(seconds=row[11]) if row[11] else None
            
            positions.append({
                'id': row[0],
                'address': row[1],
                'coin': row[2],
                'side': row[3],
                'size': row[4],
                'entry_price': row[5],
                'entry_time': entry_time,
                'exit_price': row[8],
                'exit_time': exit_time,
                'duration': duration,
                'duration_formatted': self._format_duration(duration) if duration else None,
                'pnl': row[12]
            })
        
        conn.close()
        return positions