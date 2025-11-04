"""
Strategy process - Generates trading signals based on market data and news sentiment.
"""
import socket
import time
import logging
from multiprocessing import Event
from typing import Dict, Optional
from collections import defaultdict

from ..utils.protocol import Message, MessageType
from ..utils.config import Config
from ..utils.shared_memory import OrderBookSharedMemory


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class Strategy:
    """Strategy process that generates trading signals."""
    
    def __init__(self, gateway_host: str = None, gateway_port: int = None,
                 ordermanager_host: str = None, ordermanager_port: int = None):
        """Initialize Strategy.
        
        Args:
            gateway_host: Gateway host to connect to
            gateway_port: Gateway port to connect to
            ordermanager_host: OrderManager host to connect to
            ordermanager_port: OrderManager port to connect to
        """
        self.gateway_host = gateway_host or Config.GATEWAY_HOST
        self.gateway_port = gateway_port or Config.GATEWAY_PORT
        self.ordermanager_host = ordermanager_host or Config.ORDERMANAGER_HOST
        self.ordermanager_port = ordermanager_port or Config.ORDERMANAGER_PORT
        
        self.logger = logging.getLogger("Strategy")
        self.shutdown_event = Event()
        
        # Shared memory for reading order book
        self.shm = None
        
        # Market state
        self.last_prices: Dict[str, float] = {}
        self.sentiment_scores: Dict[str, float] = defaultdict(float)
        
        # Statistics
        self.signal_count = 0
        self.order_count = 0
        
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
    
    def connect_to_ordermanager(self) -> socket.socket:
        """Connect to OrderManager.
        
        Returns:
            Connected socket
        """
        max_retries = 5
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.ordermanager_host, self.ordermanager_port))
                self.logger.info(f"Connected to OrderManager at {self.ordermanager_host}:{self.ordermanager_port}")
                return sock
            except (ConnectionRefusedError, OSError) as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    raise RuntimeError(f"Failed to connect to OrderManager after {max_retries} attempts: {e}")
    
    def generate_signal(self, symbol: str, current_price: float) -> Optional[dict]:
        """Generate trading signal based on price and sentiment.
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            Signal dictionary or None
        """
        # Check if we have previous price
        if symbol not in self.last_prices:
            return None
        
        # Calculate price change
        last_price = self.last_prices[symbol]
        price_change = (current_price - last_price) / last_price
        
        # Get sentiment
        sentiment = self.sentiment_scores.get(symbol, 0.0)
        
        # Generate signal based on price change and sentiment
        signal = None
        
        # Buy signal: price rising and positive sentiment
        if (price_change > Config.PRICE_CHANGE_THRESHOLD and 
            sentiment > Config.SENTIMENT_THRESHOLD):
            signal = {
                'symbol': symbol,
                'action': 'BUY',
                'price': current_price,
                'price_change': price_change,
                'sentiment': sentiment,
                'timestamp': time.time()
            }
            self.signal_count += 1
        
        # Sell signal: price falling and negative sentiment
        elif (price_change < -Config.PRICE_CHANGE_THRESHOLD and 
              sentiment < -Config.SENTIMENT_THRESHOLD):
            signal = {
                'symbol': symbol,
                'action': 'SELL',
                'price': current_price,
                'price_change': price_change,
                'sentiment': sentiment,
                'timestamp': time.time()
            }
            self.signal_count += 1
        
        return signal
    
    def create_order(self, signal: dict) -> dict:
        """Create order from trading signal.
        
        Args:
            signal: Trading signal
            
        Returns:
            Order dictionary
        """
        import random
        
        order = {
            'order_id': f"ORD_{int(time.time() * 1000000)}",
            'symbol': signal['symbol'],
            'side': signal['action'],
            'price': signal['price'],
            'quantity': random.randint(10, 100),
            'timestamp': time.time(),
            'signal_data': {
                'price_change': signal['price_change'],
                'sentiment': signal['sentiment']
            }
        }
        
        return order
    
    def process_market_data(self, data: dict, om_socket: socket.socket):
        """Process market data and generate signals.
        
        Args:
            data: Market data
            om_socket: Socket to OrderManager
        """
        symbol = data['symbol']
        current_price = data.get('last_price', 0)
        
        if current_price > 0:
            # Generate signal
            signal = self.generate_signal(symbol, current_price)
            
            if signal:
                self.logger.info(f"Signal generated: {signal['action']} {signal['symbol']} @ {signal['price']}")
                
                # Create and send order
                order = self.create_order(signal)
                msg = Message(MessageType.ORDER, order)
                
                try:
                    om_socket.sendall(msg.serialize())
                    self.order_count += 1
                    self.logger.info(f"Order sent: {order['order_id']}")
                except Exception as e:
                    self.logger.error(f"Failed to send order: {e}")
            
            # Update last price
            self.last_prices[symbol] = current_price
    
    def process_news(self, data: dict):
        """Process news sentiment.
        
        Args:
            data: News data
        """
        symbol = data['symbol']
        score = data['score']
        
        # Update sentiment score (simple exponential moving average)
        alpha = 0.3  # Weighting factor
        self.sentiment_scores[symbol] = alpha * score + (1 - alpha) * self.sentiment_scores[symbol]
        
        self.logger.debug(f"Updated sentiment for {symbol}: {self.sentiment_scores[symbol]:.3f}")
    
    def run(self):
        """Run the Strategy process."""
        self.logger.info("Starting Strategy process")
        
        # Connect to shared memory
        try:
            self.shm = OrderBookSharedMemory(
                name=Config.ORDERBOOK_SHM_NAME,
                create=False
            )
        except Exception as e:
            self.logger.warning(f"Could not connect to shared memory: {e}")
        
        # Connect to Gateway and OrderManager
        gateway_socket = self.connect_to_gateway()
        om_socket = self.connect_to_ordermanager()
        
        last_stats_time = time.time()
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    # Read message from Gateway
                    msg, size = Message.read_message(gateway_socket)
                    
                    # Process based on message type
                    if msg.msg_type == MessageType.MARKET_DATA:
                        self.process_market_data(msg.data, om_socket)
                    
                    elif msg.msg_type == MessageType.NEWS_SENTIMENT:
                        self.process_news(msg.data)
                    
                    elif msg.msg_type == MessageType.SHUTDOWN:
                        self.logger.info("Received shutdown message")
                        break
                    
                    # Log statistics periodically
                    current_time = time.time()
                    if current_time - last_stats_time >= Config.BENCHMARK_LOG_INTERVAL:
                        self.logger.info(f"Signals: {self.signal_count}, Orders: {self.order_count}")
                        last_stats_time = current_time
                
                except ConnectionError as e:
                    self.logger.error(f"Connection error: {e}")
                    break
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
        
        finally:
            gateway_socket.close()
            om_socket.close()
            if self.shm:
                self.shm.close()
            self.logger.info("Strategy process shut down")
    
    def shutdown(self):
        """Shutdown the Strategy process."""
        self.logger.info("Shutting down Strategy")
        self.shutdown_event.set()


def run_strategy(gateway_host: str = None, gateway_port: int = None,
                 ordermanager_host: str = None, ordermanager_port: int = None):
    """Run Strategy as a separate process.
    
    Args:
        gateway_host: Gateway host to connect to
        gateway_port: Gateway port to connect to
        ordermanager_host: OrderManager host to connect to
        ordermanager_port: OrderManager port to connect to
    """
    strategy = Strategy(gateway_host, gateway_port, ordermanager_host, ordermanager_port)
    strategy.run()
