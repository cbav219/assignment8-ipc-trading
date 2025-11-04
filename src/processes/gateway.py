"""
Gateway process - Streams market data and news sentiment via TCP.
"""
import socket
import time
import random
from multiprocessing import Process, Event
from typing import List
import logging

from ..utils.protocol import Message, MessageType
from ..utils.config import Config


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class Gateway:
    """Gateway process that streams market data and news."""
    
    def __init__(self, host: str = None, port: int = None):
        """Initialize Gateway.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.host = host or Config.GATEWAY_HOST
        self.port = port or Config.GATEWAY_PORT
        self.logger = logging.getLogger("Gateway")
        self.shutdown_event = Event()
        self.clients = []
        
    def generate_market_data(self, symbol: str) -> dict:
        """Generate synthetic market data.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Market data dictionary
        """
        base_price = random.uniform(100, 500)
        spread = base_price * 0.001  # 0.1% spread
        
        # Generate order book levels
        bids = []
        asks = []
        
        for i in range(5):
            bid_price = base_price - spread - i * 0.1
            ask_price = base_price + spread + i * 0.1
            size = random.uniform(100, 1000)
            
            bids.append([round(bid_price, 2), round(size, 2)])
            asks.append([round(ask_price, 2), round(size, 2)])
        
        return {
            'symbol': symbol,
            'timestamp': time.time(),
            'bids': bids,
            'asks': asks,
            'last_price': round(base_price, 2),
            'volume': random.randint(1000, 100000)
        }
    
    def generate_news_sentiment(self, symbol: str) -> dict:
        """Generate synthetic news sentiment.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            News sentiment dictionary
        """
        sentiments = ['positive', 'negative', 'neutral']
        sentiment = random.choice(sentiments)
        
        # Score: -1 to 1
        if sentiment == 'positive':
            score = random.uniform(0.3, 1.0)
        elif sentiment == 'negative':
            score = random.uniform(-1.0, -0.3)
        else:
            score = random.uniform(-0.2, 0.2)
        
        return {
            'symbol': symbol,
            'timestamp': time.time(),
            'sentiment': sentiment,
            'score': round(score, 3),
            'headline': f"{sentiment.title()} news for {symbol}"
        }
    
    def handle_client(self, client_socket, address):
        """Handle client connection.
        
        Args:
            client_socket: Client socket
            address: Client address
        """
        self.logger.info(f"Client connected from {address}")
        
        try:
            last_market_data_time = 0
            last_news_time = 0
            
            while not self.shutdown_event.is_set():
                current_time = time.time()
                
                # Send market data
                if current_time - last_market_data_time >= Config.MARKET_DATA_INTERVAL:
                    for symbol in Config.SYMBOLS:
                        market_data = self.generate_market_data(symbol)
                        msg = Message(MessageType.MARKET_DATA, market_data)
                        
                        try:
                            client_socket.sendall(msg.serialize())
                        except (BrokenPipeError, ConnectionResetError):
                            self.logger.warning(f"Client {address} disconnected")
                            return
                    
                    last_market_data_time = current_time
                
                # Send news sentiment
                if current_time - last_news_time >= Config.NEWS_INTERVAL:
                    symbol = random.choice(Config.SYMBOLS)
                    news = self.generate_news_sentiment(symbol)
                    msg = Message(MessageType.NEWS_SENTIMENT, news)
                    
                    try:
                        client_socket.sendall(msg.serialize())
                    except (BrokenPipeError, ConnectionResetError):
                        self.logger.warning(f"Client {address} disconnected")
                        return
                    
                    last_news_time = current_time
                
                # Small sleep to prevent busy waiting
                time.sleep(0.01)
        
        except Exception as e:
            self.logger.error(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
            self.logger.info(f"Client {address} disconnected")
    
    def run(self):
        """Run the Gateway server."""
        self.logger.info(f"Starting Gateway on {self.host}:{self.port}")
        
        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        server_socket.settimeout(1.0)  # Allow periodic checking of shutdown event
        
        self.logger.info("Gateway ready to accept connections")
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    client_socket, address = server_socket.accept()
                    
                    # Handle client in a separate thread/process
                    # For simplicity, we'll handle in the same process
                    # In production, use threading or separate process
                    import threading
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if not self.shutdown_event.is_set():
                        self.logger.error(f"Error accepting connection: {e}")
        
        finally:
            server_socket.close()
            self.logger.info("Gateway shut down")
    
    def shutdown(self):
        """Shutdown the Gateway."""
        self.logger.info("Shutting down Gateway")
        self.shutdown_event.set()


def run_gateway(host: str = None, port: int = None):
    """Run Gateway as a separate process.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    gateway = Gateway(host, port)
    gateway.run()
