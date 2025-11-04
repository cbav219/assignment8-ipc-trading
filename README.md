# Multi-Process Trading System with IPC

A high-performance multi-process trading system using interprocess communication (IPC) with TCP sockets and shared memory. The system includes Gateway, OrderBook, Strategy, and OrderManager processes that stream market data, update shared state, generate trading signals, and log executed trades in real time.

## Features

- **Multi-Process Architecture**: Four concurrent processes communicating via TCP sockets
- **Shared Memory**: Low-latency order book state sharing using `multiprocessing.shared_memory`
- **Message Protocol**: Binary serialization with JSON for efficient data transmission
- **Market Data Streaming**: Real-time market data and news sentiment generation
- **Trading Strategy**: Automated signal generation based on price movements and sentiment
- **Order Management**: Trade execution and logging
- **Performance Benchmarking**: Latency and throughput measurement tools

## Architecture

```
┌─────────────┐
│   Gateway   │ (TCP Server: Port 5555)
│             │ - Streams market data
│             │ - Generates news sentiment
└──────┬──────┘
       │ TCP
       ├──────────────┐
       │              │
       ▼              ▼
┌─────────────┐  ┌──────────┐
│  OrderBook  │  │ Strategy │
│             │  │          │
│ Shared Mem  │◄─┤ Reads SHM│
│  Updates    │  │ Generates│
└─────────────┘  │ Signals  │
                 └────┬─────┘
                      │ TCP
                      ▼
              ┌──────────────┐
              │OrderManager  │ (TCP Server: Port 5558)
              │              │
              │ - Executes   │
              │ - Logs trades│
              └──────────────┘
```

## Components

### 1. Gateway
- **Purpose**: Streams market data and news sentiment
- **Communication**: TCP server on port 5555
- **Data Generated**:
  - Market data (order book levels, prices, volume)
  - News sentiment (positive/negative/neutral with scores)

### 2. OrderBook
- **Purpose**: Maintains order book state in shared memory
- **Communication**: TCP client (connects to Gateway)
- **Shared Memory**: Writes order book data for other processes

### 3. Strategy
- **Purpose**: Generates trading signals
- **Communication**: 
  - TCP client (connects to Gateway and OrderManager)
  - Reads from shared memory
- **Logic**:
  - Monitors price changes and sentiment
  - Generates BUY/SELL signals based on thresholds
  - Sends orders to OrderManager

### 4. OrderManager
- **Purpose**: Manages and logs executed trades
- **Communication**: TCP server on port 5558
- **Functions**:
  - Receives orders from Strategy
  - Simulates trade execution
  - Logs trades to `trades.log`

## Requirements

- Python 3.8+ (for `multiprocessing.shared_memory`)
- No external dependencies (uses Python standard library only)

## Installation

```bash
git clone https://github.com/cbav219/assignment8-ipc-trading.git
cd assignment8-ipc-trading
```

## Usage

### Running the Trading System

Run the system indefinitely:
```bash
python main.py
```

Run for a specific duration (e.g., 60 seconds):
```bash
python main.py --duration 60
```

### Running Tests

```bash
# Run all tests
python -m unittest discover tests

# Run specific test
python -m unittest tests.test_protocol
python -m unittest tests.test_shared_memory
```

### Running Benchmarks

```bash
# Run all benchmarks
python benchmarks/run_benchmarks.py

# Run specific benchmark
python benchmarks/run_benchmarks.py --test throughput
python benchmarks/run_benchmarks.py --test shm

# Custom parameters
python benchmarks/run_benchmarks.py --duration 30 --operations 50000
```

## Configuration

Edit `src/utils/config.py` to customize:

- Network ports for each component
- Trading symbols
- Market data generation intervals
- Strategy parameters (thresholds)
- Benchmarking settings

## Performance Benchmarks

The system includes comprehensive benchmarking tools:

1. **Throughput Benchmark**: Measures messages/second and data transfer rates
2. **Shared Memory Benchmark**: Measures read/write latency for shared memory operations

Example results:
- Message serialization: ~100,000+ messages/second
- Shared memory operations: <10 microseconds latency

## System Output

When running, you'll see logs from each process:

```
2025-11-04 21:24:35 - TradingSystem - INFO - Starting Gateway process...
2025-11-04 21:24:36 - Gateway - INFO - Gateway ready to accept connections
2025-11-04 21:24:37 - OrderBook - INFO - Connected to Gateway
2025-11-04 21:24:38 - Strategy - INFO - Connected to Gateway
2025-11-04 21:24:39 - Strategy - INFO - Signal generated: BUY AAPL @ 150.25
2025-11-04 21:24:39 - OrderManager - INFO - Order executed: EXEC_1234567890
```

## Trade Logs

Executed trades are logged to `trades.log` in JSON format:

```json
{"execution_id": "EXEC_1699123456789", "order_id": "ORD_1699123456780", "symbol": "AAPL", "side": "BUY", "quantity": 50, "order_price": 150.25, "execution_price": 150.27, "timestamp": 1699123456.789, "status": "FILLED"}
```

## Shutdown

Press `Ctrl+C` to gracefully shutdown all processes. The system will:
1. Stop accepting new connections
2. Terminate processes in reverse order
3. Clean up shared memory resources
4. Display final statistics

## Key Concepts Demonstrated

1. **Multiprocessing**: Four independent processes running concurrently
2. **IPC via TCP Sockets**: Message-based communication between processes
3. **Shared Memory**: Low-latency data sharing for order book state
4. **Serialization**: Binary protocol with JSON encoding
5. **Message Protocol**: Length-prefixed messages for reliable transmission
6. **Synchronization**: Thread-safe shared memory access with locks
7. **Performance Monitoring**: Real-time statistics and benchmarking

## License

MIT License - see LICENSE file for details
