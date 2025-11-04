"""
Message protocol for IPC communication.
Defines message types and serialization/deserialization methods.
"""
import json
import struct
from enum import Enum
from typing import Dict, Any, Tuple


class MessageType(Enum):
    """Message types for IPC communication."""
    MARKET_DATA = 1
    NEWS_SENTIMENT = 2
    TRADING_SIGNAL = 3
    ORDER = 4
    TRADE_EXECUTION = 5
    ORDERBOOK_UPDATE = 6
    HEARTBEAT = 7
    SHUTDOWN = 8


class Message:
    """Message class for IPC communication."""
    
    def __init__(self, msg_type: MessageType, data: Dict[str, Any]):
        """Initialize a message.
        
        Args:
            msg_type: Type of the message
            data: Message payload as dictionary
        """
        self.msg_type = msg_type
        self.data = data
    
    def serialize(self) -> bytes:
        """Serialize message to bytes for transmission.
        
        Returns:
            Serialized message bytes with length prefix
        """
        # Create message dictionary
        msg_dict = {
            'type': self.msg_type.value,
            'data': self.data
        }
        
        # Serialize to JSON
        json_str = json.dumps(msg_dict)
        json_bytes = json_str.encode('utf-8')
        
        # Add length prefix (4 bytes, big-endian)
        length = len(json_bytes)
        length_prefix = struct.pack('>I', length)
        
        return length_prefix + json_bytes
    
    @staticmethod
    def deserialize(data: bytes) -> 'Message':
        """Deserialize message from bytes.
        
        Args:
            data: Serialized message bytes (without length prefix)
            
        Returns:
            Deserialized Message object
        """
        # Decode JSON
        json_str = data.decode('utf-8')
        msg_dict = json.loads(json_str)
        
        # Extract message type and data
        msg_type = MessageType(msg_dict['type'])
        msg_data = msg_dict['data']
        
        return Message(msg_type, msg_data)
    
    @staticmethod
    def read_message(sock) -> Tuple['Message', int]:
        """Read a complete message from socket.
        
        Args:
            sock: Socket to read from
            
        Returns:
            Tuple of (Message object, message size in bytes)
        """
        # Read length prefix (4 bytes)
        length_bytes = b''
        while len(length_bytes) < 4:
            chunk = sock.recv(4 - len(length_bytes))
            if not chunk:
                raise ConnectionError("Socket connection broken")
            length_bytes += chunk
        
        length = struct.unpack('>I', length_bytes)[0]
        
        # Read message data
        data = b''
        while len(data) < length:
            chunk = sock.recv(min(length - len(data), 4096))
            if not chunk:
                raise ConnectionError("Socket connection broken")
            data += chunk
        
        message = Message.deserialize(data)
        return message, length + 4  # Include length prefix in size
    
    def __repr__(self):
        return f"Message(type={self.msg_type.name}, data={self.data})"
