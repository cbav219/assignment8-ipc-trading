"""
OrderBook process - Maintains order book state in shared memory.
Receives updates from Gateway and updates shared memory.
"""
import socket
import time
import logging
from multiprocessing import Event
from typing import Dict, List, Tuple

from ..utils.protocol import Message, MessageType
from ..utils.config import Config
from ..utils.shared_memory import OrderBookSharedMemory


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class OrderBook:
    """OrderBook process that maintains order book state."""
    
    def __init__(self, gateway_host: str = None, gateway_port: int = None):
        """Initialize OrderBook.
        
        Args:
            gateway_host: Gateway host to connect to
            gateway_port: Gateway port to connect to
        """
        self.gateway_host = gateway_host or Config.GATEWAY_HOST
        self.gateway_port = gateway_port or Config.GATEWAY_PORT
        self.logger = logging.getLogger("OrderBook")
        self.shutdown_event = Event()
        
        # Shared memory for order book
        self.shm = OrderBookSharedMemory(
            name=Config.ORDERBOOK_SHM_NAME,
            create=True
        )
        
        # In-memory order book state (for aggregation)
        self.order_books: Dict[str, Dict] = {}
        
        # Statistics
        self.update_count = 0
        self.last_update_time = time.time()
    
    def process_market_data(self, data: dict):
        """Process market data message and update order book.
        
        Args:
            data: Market data dictionary
        """
        symbol = data['symbol']
        bids = [(float(price), float(size)) for price, size in data['bids']]
        asks = [(float(price), float(size)) for price, size in data['asks']]
        
        # Update in-memory state
        self.order_books[symbol] = {
            'timestamp': data['timestamp'],
            'bids': bids,
            'asks': asks,
            'last_price': data.get('last_price', 0),
            'volume': data.get('volume', 0)
        }
        
        # Update shared memory with aggregated order book
        # For simplicity, we'll write the first symbol's data
        # In production, you might aggregate all symbols or use separate SHM blocks
        if symbol == Config.SYMBOLS[0]:
            self.shm.write_orderbook(bids, asks)
            self.update_count += 1
    
    def connect_to_gateway(self) -> socket.socket:
        """Connect to Gateway.
        
        Returns:
            Connected socket
        """
        max_retries = 5
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.gateway_host, self.gateway_port))
                self.logger.info(f"Connected to Gateway at {self.gateway_host}:{self.gateway_port}")
                return sock
            except (ConnectionRefusedError, OSError) as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    raise RuntimeError(f"Failed to connect to Gateway after {max_retries} attempts: {e}")
    
    def run(self):
        """Run the OrderBook process."""
        self.logger.info("Starting OrderBook process")
        
        # Connect to Gateway
        gateway_socket = self.connect_to_gateway()
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    # Read message from Gateway
                    msg, size = Message.read_message(gateway_socket)
                    
                    # Process market data
                    if msg.msg_type == MessageType.MARKET_DATA:
                        self.process_market_data(msg.data)
                        
                        # Log statistics periodically
                        current_time = time.time()
                        if current_time - self.last_update_time >= Config.BENCHMARK_LOG_INTERVAL:
                            elapsed = current_time - self.last_update_time
                            rate = self.update_count / elapsed
                            self.logger.info(f"Update rate: {rate:.2f} updates/sec, Total updates: {self.update_count}")
                            self.last_update_time = current_time
                            self.update_count = 0
                    
                    elif msg.msg_type == MessageType.SHUTDOWN:
                        self.logger.info("Received shutdown message")
                        break
                
                except ConnectionError as e:
                    self.logger.error(f"Connection error: {e}")
                    break
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
        
        finally:
            gateway_socket.close()
            self.shm.close()
            self.logger.info("OrderBook process shut down")
    
    def shutdown(self):
        """Shutdown the OrderBook process."""
        self.logger.info("Shutting down OrderBook")
        self.shutdown_event.set()
        if hasattr(self, 'shm'):
            self.shm.close()
            # Don't unlink here, let the main process do it


def run_orderbook(gateway_host: str = None, gateway_port: int = None):
    """Run OrderBook as a separate process.
    
    Args:
        gateway_host: Gateway host to connect to
        gateway_port: Gateway port to connect to
    """
    orderbook = OrderBook(gateway_host, gateway_port)
    orderbook.run()
