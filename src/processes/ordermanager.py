"""
OrderManager process - Manages and logs executed trades.
"""
import socket
import time
import logging
from multiprocessing import Event
from typing import List, Dict
import json
import os

from ..utils.protocol import Message, MessageType
from ..utils.config import Config


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class OrderManager:
    """OrderManager process that manages and logs trades."""
    
    def __init__(self, host: str = None, port: int = None, log_file: str = "trades.log"):
        """Initialize OrderManager.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            log_file: File to log trades to
        """
        self.host = host or Config.ORDERMANAGER_HOST
        self.port = port or Config.ORDERMANAGER_PORT
        self.log_file = log_file
        self.logger = logging.getLogger("OrderManager")
        self.shutdown_event = Event()
        
        # Trade tracking
        self.orders: List[Dict] = []
        self.executed_trades: List[Dict] = []
        
        # Statistics
        self.total_orders = 0
        self.total_executed = 0
        self.total_volume = 0.0
        
        # Ensure log file directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def execute_order(self, order: dict) -> dict:
        """Execute an order (simulated).
        
        Args:
            order: Order dictionary
            
        Returns:
            Execution result dictionary
        """
        import random
        
        # Simulate order execution
        # In a real system, this would interact with an exchange
        
        # Simulate execution price with slippage
        slippage = random.uniform(-0.001, 0.001)  # 0.1% slippage
        execution_price = order['price'] * (1 + slippage)
        
        execution = {
            'execution_id': f"EXEC_{int(time.time() * 1000000)}",
            'order_id': order['order_id'],
            'symbol': order['symbol'],
            'side': order['side'],
            'quantity': order['quantity'],
            'order_price': order['price'],
            'execution_price': round(execution_price, 2),
            'timestamp': time.time(),
            'status': 'FILLED'
        }
        
        return execution
    
    def log_trade(self, execution: dict):
        """Log executed trade to file.
        
        Args:
            execution: Execution dictionary
        """
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(execution) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to log trade: {e}")
    
    def process_order(self, order: dict):
        """Process incoming order.
        
        Args:
            order: Order dictionary
        """
        self.logger.info(f"Received order: {order['order_id']} - {order['side']} {order['quantity']} {order['symbol']} @ {order['price']}")
        
        # Track order
        self.orders.append(order)
        self.total_orders += 1
        
        # Execute order
        execution = self.execute_order(order)
        self.executed_trades.append(execution)
        self.total_executed += 1
        self.total_volume += order['quantity'] * execution['execution_price']
        
        # Log trade
        self.log_trade(execution)
        
        self.logger.info(f"Order executed: {execution['execution_id']} - {execution['status']}")
    
    def handle_client(self, client_socket, address):
        """Handle client connection.
        
        Args:
            client_socket: Client socket
            address: Client address
        """
        self.logger.info(f"Client connected from {address}")
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    # Read message
                    msg, size = Message.read_message(client_socket)
                    
                    # Process order
                    if msg.msg_type == MessageType.ORDER:
                        self.process_order(msg.data)
                    
                    elif msg.msg_type == MessageType.SHUTDOWN:
                        self.logger.info("Received shutdown message")
                        break
                
                except ConnectionError:
                    self.logger.info(f"Client {address} disconnected")
                    break
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
        
        finally:
            client_socket.close()
    
    def run(self):
        """Run the OrderManager server."""
        self.logger.info(f"Starting OrderManager on {self.host}:{self.port}")
        
        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        server_socket.settimeout(1.0)
        
        self.logger.info("OrderManager ready to accept connections")
        
        last_stats_time = time.time()
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    client_socket, address = server_socket.accept()
                    
                    # Handle client in a separate thread
                    import threading
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                
                except socket.timeout:
                    # Log statistics periodically
                    current_time = time.time()
                    if current_time - last_stats_time >= Config.BENCHMARK_LOG_INTERVAL:
                        self.logger.info(
                            f"Orders: {self.total_orders}, Executed: {self.total_executed}, "
                            f"Volume: ${self.total_volume:.2f}"
                        )
                        last_stats_time = current_time
                    continue
                except Exception as e:
                    if not self.shutdown_event.is_set():
                        self.logger.error(f"Error accepting connection: {e}")
        
        finally:
            server_socket.close()
            self.logger.info("OrderManager shut down")
            
            # Print final statistics
            self.logger.info(
                f"Final statistics - Orders: {self.total_orders}, "
                f"Executed: {self.total_executed}, Volume: ${self.total_volume:.2f}"
            )
    
    def shutdown(self):
        """Shutdown the OrderManager."""
        self.logger.info("Shutting down OrderManager")
        self.shutdown_event.set()


def run_ordermanager(host: str = None, port: int = None, log_file: str = "trades.log"):
    """Run OrderManager as a separate process.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        log_file: File to log trades to
    """
    ordermanager = OrderManager(host, port, log_file)
    ordermanager.run()
