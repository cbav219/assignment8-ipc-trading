"""
Shared memory manager for order book state.
Uses multiprocessing shared memory for low-latency data sharing.
"""
import time
from multiprocessing import shared_memory, Lock
import struct
import json
from typing import Dict, List, Optional, Tuple


class OrderBookSharedMemory:
    """Manages order book state in shared memory."""
    
    # Memory layout:
    # - First 8 bytes: timestamp (double)
    # - Next 4 bytes: number of bid levels (int)
    # - Next 4 bytes: number of ask levels (int)
    # - Remaining: JSON encoded order book data
    
    HEADER_SIZE = 16  # 8 + 4 + 4
    MEMORY_SIZE = 1024 * 64  # 64KB for order book data
    
    def __init__(self, name: str = "orderbook_shm", create: bool = True):
        """Initialize shared memory for order book.
        
        Args:
            name: Name of the shared memory block
            create: Whether to create new shared memory or attach to existing
        """
        self.name = name
        self.lock = Lock()
        
        if create:
            try:
                # Try to unlink existing shared memory
                try:
                    old_shm = shared_memory.SharedMemory(name=name)
                    old_shm.close()
                    old_shm.unlink()
                except FileNotFoundError:
                    pass
                
                # Create new shared memory
                self.shm = shared_memory.SharedMemory(
                    name=name, 
                    create=True, 
                    size=self.MEMORY_SIZE
                )
            except Exception as e:
                raise RuntimeError(f"Failed to create shared memory: {e}")
        else:
            try:
                self.shm = shared_memory.SharedMemory(name=name)
            except FileNotFoundError:
                raise RuntimeError(f"Shared memory '{name}' not found")
    
    def write_orderbook(self, bids: List[Tuple[float, float]], 
                       asks: List[Tuple[float, float]]) -> None:
        """Write order book data to shared memory.
        
        Args:
            bids: List of (price, size) tuples for bid side
            asks: List of (price, size) tuples for ask side
        """
        with self.lock:
            # Prepare data
            timestamp = time.time()
            num_bids = len(bids)
            num_asks = len(asks)
            
            # Create JSON data
            data = {
                'bids': [[price, size] for price, size in bids],
                'asks': [[price, size] for price, size in asks]
            }
            json_bytes = json.dumps(data).encode('utf-8')
            
            # Check if data fits
            if len(json_bytes) > self.MEMORY_SIZE - self.HEADER_SIZE:
                raise ValueError("Order book data too large for shared memory")
            
            # Write header
            header = struct.pack('>dII', timestamp, num_bids, num_asks)
            
            # Write to shared memory
            self.shm.buf[:self.HEADER_SIZE] = header
            self.shm.buf[self.HEADER_SIZE:self.HEADER_SIZE + len(json_bytes)] = json_bytes
    
    def read_orderbook(self) -> Optional[Dict]:
        """Read order book data from shared memory.
        
        Returns:
            Dictionary with timestamp, bids, and asks, or None if no data
        """
        with self.lock:
            # Read header
            header_bytes = bytes(self.shm.buf[:self.HEADER_SIZE])
            timestamp, num_bids, num_asks = struct.unpack('>dII', header_bytes)
            
            # If timestamp is 0, no data written yet
            if timestamp == 0:
                return None
            
            # Find end of JSON data (look for null terminator or use fixed size)
            # We'll read until we find the end of JSON structure
            max_json_size = self.MEMORY_SIZE - self.HEADER_SIZE
            json_bytes = bytes(self.shm.buf[self.HEADER_SIZE:self.HEADER_SIZE + max_json_size])
            
            # Find the actual end of JSON (first null byte)
            try:
                null_index = json_bytes.index(b'\x00')
                json_bytes = json_bytes[:null_index]
            except ValueError:
                # No null byte found, use all data
                pass
            
            # Parse JSON
            try:
                data = json.loads(json_bytes.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return None
            
            return {
                'timestamp': timestamp,
                'bids': [(price, size) for price, size in data['bids']],
                'asks': [(price, size) for price, size in data['asks']]
            }
    
    def get_best_bid_ask(self) -> Optional[Tuple[float, float]]:
        """Get best bid and ask prices.
        
        Returns:
            Tuple of (best_bid, best_ask) or None if no data
        """
        orderbook = self.read_orderbook()
        if not orderbook or not orderbook['bids'] or not orderbook['asks']:
            return None
        
        best_bid = orderbook['bids'][0][0]  # First bid price
        best_ask = orderbook['asks'][0][0]  # First ask price
        
        return best_bid, best_ask
    
    def close(self):
        """Close shared memory."""
        if hasattr(self, 'shm'):
            self.shm.close()
    
    def unlink(self):
        """Unlink (delete) shared memory."""
        if hasattr(self, 'shm'):
            self.shm.unlink()
