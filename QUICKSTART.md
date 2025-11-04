# Quick Start Guide

## Overview
This is a multi-process trading system that demonstrates IPC using TCP sockets and shared memory.

## Quick Start (3 steps)

### 1. Run the Trading System
```bash
python main.py --duration 30
```

This will:
- Start all 4 processes (Gateway, OrderBook, Strategy, OrderManager)
- Stream market data and news sentiment
- Generate trading signals
- Execute and log trades
- Run for 30 seconds then shutdown gracefully

### 2. View the Results
Check the generated trade log:
```bash
cat trades.log | head -5
```

You'll see JSON-formatted trade executions like:
```json
{"execution_id": "EXEC_...", "symbol": "AAPL", "side": "BUY", ...}
```

### 3. Run Performance Benchmarks
```bash
python benchmarks/run_benchmarks.py --duration 5
```

Expected performance:
- **Throughput**: 100K+ messages/second
- **Shared Memory Latency**: <10 microseconds

## Testing

Run all tests:
```bash
python -m unittest discover tests -v
```

Run specific test suites:
```bash
python -m unittest tests.test_protocol
python -m unittest tests.test_shared_memory  
python -m unittest tests.test_integration
```

## Examples

Run the component demonstration:
```bash
python examples/demo.py
```

## System Architecture

```
Gateway (5555) → OrderBook → Shared Memory
     ↓                            ↑
  Strategy (reads data) ←─────────┘
     ↓
OrderManager (5558) → trades.log
```

## Key Features Demonstrated

1. **Multi-processing**: 4 independent processes
2. **TCP Sockets**: Inter-process communication
3. **Shared Memory**: Low-latency order book sharing
4. **Message Protocol**: Binary serialization
5. **Performance**: High throughput, low latency

## Customization

Edit `src/utils/config.py` to change:
- Trading symbols
- Network ports
- Strategy parameters
- Benchmark intervals

## Troubleshooting

**Port already in use?**
```bash
# Change ports in src/utils/config.py
```

**Shared memory error?**
```bash
# Clean up leftover shared memory
python -c "from multiprocessing import shared_memory; s = shared_memory.SharedMemory(name='orderbook_shm'); s.unlink()"
```

## Next Steps

1. Examine the code in `src/processes/` to understand each component
2. Modify `src/utils/config.py` to customize behavior
3. Add your own trading strategies in `src/processes/strategy.py`
4. Extend the system with additional features

## Documentation

Full documentation in README.md
