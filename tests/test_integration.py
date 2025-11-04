"""
Integration tests for the trading system.
"""
import unittest
import time
from multiprocessing import Process
import socket

from src.processes.gateway import run_gateway
from src.processes.ordermanager import run_ordermanager
from src.utils.protocol import Message, MessageType
from src.utils.config import Config


class TestIntegration(unittest.TestCase):
    """Integration tests for trading system components."""
    
    def test_gateway_connection(self):
        """Test connecting to Gateway and receiving messages."""
        # Start Gateway in background
        gateway_proc = Process(target=run_gateway, daemon=True)
        gateway_proc.start()
        time.sleep(1.5)  # Give Gateway time to start
        
        try:
            # Connect to Gateway
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((Config.GATEWAY_HOST, Config.GATEWAY_PORT))
            sock.settimeout(5.0)
            
            # Receive a message
            msg, size = Message.read_message(sock)
            
            # Verify message
            self.assertIn(msg.msg_type, [MessageType.MARKET_DATA, MessageType.NEWS_SENTIMENT])
            self.assertIsInstance(msg.data, dict)
            
            # Close connection
            sock.close()
        
        finally:
            gateway_proc.terminate()
            gateway_proc.join(timeout=2)
    
    def test_ordermanager_connection(self):
        """Test connecting to OrderManager and sending orders."""
        # Start OrderManager in background
        om_proc = Process(target=run_ordermanager, daemon=True)
        om_proc.start()
        time.sleep(1.5)  # Give OrderManager time to start
        
        try:
            # Connect to OrderManager
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((Config.ORDERMANAGER_HOST, Config.ORDERMANAGER_PORT))
            
            # Send an order
            order = {
                'order_id': 'TEST_001',
                'symbol': 'TEST',
                'side': 'BUY',
                'price': 100.0,
                'quantity': 10,
                'timestamp': time.time()
            }
            
            msg = Message(MessageType.ORDER, order)
            sock.sendall(msg.serialize())
            
            # Give time for processing
            time.sleep(0.5)
            
            # Close connection
            sock.close()
        
        finally:
            om_proc.terminate()
            om_proc.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
