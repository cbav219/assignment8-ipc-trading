"""
Tests for message protocol.
"""
import unittest
from src.utils.protocol import Message, MessageType


class TestProtocol(unittest.TestCase):
    """Test message protocol."""
    
    def test_message_creation(self):
        """Test message creation."""
        data = {'symbol': 'AAPL', 'price': 150.0}
        msg = Message(MessageType.MARKET_DATA, data)
        
        self.assertEqual(msg.msg_type, MessageType.MARKET_DATA)
        self.assertEqual(msg.data, data)
    
    def test_message_serialization(self):
        """Test message serialization."""
        data = {'symbol': 'AAPL', 'price': 150.0}
        msg = Message(MessageType.MARKET_DATA, data)
        
        # Serialize
        serialized = msg.serialize()
        self.assertIsInstance(serialized, bytes)
        self.assertGreater(len(serialized), 4)  # At least length prefix
    
    def test_message_deserialization(self):
        """Test message deserialization."""
        data = {'symbol': 'AAPL', 'price': 150.0}
        msg = Message(MessageType.MARKET_DATA, data)
        
        # Serialize and deserialize
        serialized = msg.serialize()
        # Remove length prefix for deserialization
        msg_bytes = serialized[4:]
        
        deserialized = Message.deserialize(msg_bytes)
        
        self.assertEqual(deserialized.msg_type, msg.msg_type)
        self.assertEqual(deserialized.data, msg.data)
    
    def test_message_roundtrip(self):
        """Test message serialization roundtrip."""
        test_cases = [
            {'symbol': 'AAPL', 'price': 150.0},
            {'bids': [[100.0, 10.0]], 'asks': [[101.0, 10.0]]},
            {'order_id': 'ORD123', 'quantity': 100}
        ]
        
        for data in test_cases:
            msg = Message(MessageType.MARKET_DATA, data)
            serialized = msg.serialize()
            msg_bytes = serialized[4:]
            deserialized = Message.deserialize(msg_bytes)
            
            self.assertEqual(deserialized.data, data)


if __name__ == '__main__':
    unittest.main()
