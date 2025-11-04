"""
Configuration management for the trading system.
"""


class Config:
    """Configuration parameters for the trading system."""
    
    # Network settings
    GATEWAY_HOST = "127.0.0.1"
    GATEWAY_PORT = 5555
    
    ORDERBOOK_HOST = "127.0.0.1"
    ORDERBOOK_PORT = 5556
    
    STRATEGY_HOST = "127.0.0.1"
    STRATEGY_PORT = 5557
    
    ORDERMANAGER_HOST = "127.0.0.1"
    ORDERMANAGER_PORT = 5558
    
    # Shared memory
    ORDERBOOK_SHM_NAME = "orderbook_shm"
    
    # Trading parameters
    SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    
    # Market data generation
    MARKET_DATA_INTERVAL = 0.1  # seconds
    NEWS_INTERVAL = 2.0  # seconds
    
    # Strategy parameters
    PRICE_CHANGE_THRESHOLD = 0.005  # 0.5% price change for signal
    SENTIMENT_THRESHOLD = 0.3  # Sentiment score threshold
    
    # Performance benchmarking
    ENABLE_BENCHMARKING = True
    BENCHMARK_LOG_INTERVAL = 10.0  # seconds
    
    # System settings
    MAX_QUEUE_SIZE = 1000
    SOCKET_BUFFER_SIZE = 4096
    SHUTDOWN_TIMEOUT = 5.0  # seconds
