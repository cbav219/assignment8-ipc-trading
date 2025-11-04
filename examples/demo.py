#!/usr/bin/env python3
"""
Example demonstration of the trading system components.
Shows how to use individual components and read from shared memory.
"""
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.shared_memory import OrderBookSharedMemory
from src.utils.protocol import Message, MessageType
from src.utils.config import Config


def demo_message_protocol():
    """Demonstrate message protocol usage."""
    print("\n" + "=" * 60)
    print("MESSAGE PROTOCOL DEMONSTRATION")
    print("=" * 60)
    
    # Create market data message
    market_data = {
        'symbol': 'AAPL',
        'timestamp': time.time(),
        'bids': [[150.00, 100], [149.99, 200], [149.98, 150]],
        'asks': [[150.01, 100], [150.02, 200], [150.03, 150]],
        'last_price': 150.00,
        'volume': 50000
    }
    
    msg = Message(MessageType.MARKET_DATA, market_data)
    print(f"\n1. Created message: {msg}")
    
    # Serialize
    serialized = msg.serialize()
    print(f"2. Serialized size: {len(serialized)} bytes")
    
    # Deserialize
    msg_bytes = serialized[4:]  # Skip length prefix
    deserialized = Message.deserialize(msg_bytes)
    print(f"3. Deserialized message: {deserialized}")
    print(f"4. Data matches: {deserialized.data == market_data}")


def demo_shared_memory():
    """Demonstrate shared memory usage."""
    print("\n" + "=" * 60)
    print("SHARED MEMORY DEMONSTRATION")
    print("=" * 60)
    
    # Create shared memory
    shm = OrderBookSharedMemory(name="demo_shm", create=True)
    
    try:
        # Write order book data
        bids = [(150.00, 100), (149.99, 200), (149.98, 150)]
        asks = [(150.01, 100), (150.02, 200), (150.03, 150)]
        
        print("\n1. Writing order book to shared memory...")
        shm.write_orderbook(bids, asks)
        
        # Read back
        print("2. Reading order book from shared memory...")
        data = shm.read_orderbook()
        
        print(f"\nOrder Book Data:")
        print(f"  Timestamp: {data['timestamp']}")
        print(f"  Bids: {data['bids'][:3]}")
        print(f"  Asks: {data['asks'][:3]}")
        
        # Get best bid/ask
        best_bid, best_ask = shm.get_best_bid_ask()
        print(f"\n3. Best Bid: {best_bid}, Best Ask: {best_ask}")
        print(f"   Spread: {best_ask - best_bid:.4f}")
        
    finally:
        shm.close()
        shm.unlink()


def demo_config():
    """Demonstrate configuration."""
    print("\n" + "=" * 60)
    print("CONFIGURATION DEMONSTRATION")
    print("=" * 60)
    
    print(f"\nNetwork Configuration:")
    print(f"  Gateway: {Config.GATEWAY_HOST}:{Config.GATEWAY_PORT}")
    print(f"  OrderBook: {Config.ORDERBOOK_HOST}:{Config.ORDERBOOK_PORT}")
    print(f"  Strategy: {Config.STRATEGY_HOST}:{Config.STRATEGY_PORT}")
    print(f"  OrderManager: {Config.ORDERMANAGER_HOST}:{Config.ORDERMANAGER_PORT}")
    
    print(f"\nTrading Configuration:")
    print(f"  Symbols: {', '.join(Config.SYMBOLS)}")
    print(f"  Market Data Interval: {Config.MARKET_DATA_INTERVAL}s")
    print(f"  News Interval: {Config.NEWS_INTERVAL}s")
    
    print(f"\nStrategy Parameters:")
    print(f"  Price Change Threshold: {Config.PRICE_CHANGE_THRESHOLD * 100}%")
    print(f"  Sentiment Threshold: {Config.SENTIMENT_THRESHOLD}")


def main():
    """Run all demonstrations."""
    print("=" * 60)
    print("TRADING SYSTEM COMPONENT DEMONSTRATIONS")
    print("=" * 60)
    
    demo_message_protocol()
    demo_shared_memory()
    demo_config()
    
    print("\n" + "=" * 60)
    print("DEMONSTRATIONS COMPLETE")
    print("=" * 60)
    print("\nTo run the full trading system:")
    print("  python main.py --duration 60")
    print("\nTo run benchmarks:")
    print("  python benchmarks/run_benchmarks.py")
    print("\nTo run tests:")
    print("  python -m unittest discover tests")
    print()


if __name__ == '__main__':
    main()
