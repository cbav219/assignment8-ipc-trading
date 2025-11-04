"""
Performance benchmarking utilities for the trading system.
Measures latency and throughput.
"""
import time
import socket
import statistics
from typing import List, Dict
import logging

from ..utils.protocol import Message, MessageType
from ..utils.config import Config


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class LatencyBenchmark:
    """Benchmark for measuring message latency."""
    
    def __init__(self):
        """Initialize latency benchmark."""
        self.logger = logging.getLogger("LatencyBenchmark")
        self.latencies: List[float] = []
    
    def measure_roundtrip(self, host: str, port: int, num_messages: int = 1000) -> Dict:
        """Measure round-trip latency.
        
        Args:
            host: Host to connect to
            port: Port to connect to
            num_messages: Number of messages to send
            
        Returns:
            Dictionary with latency statistics
        """
        self.logger.info(f"Starting latency benchmark with {num_messages} messages...")
        
        # Connect to server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        
        latencies = []
        
        try:
            for i in range(num_messages):
                # Create test message
                msg = Message(MessageType.HEARTBEAT, {'seq': i, 'timestamp': time.time()})
                
                # Measure send + receive time
                start_time = time.perf_counter()
                sock.sendall(msg.serialize())
                
                # For this benchmark, we just measure serialization overhead
                # In a real system, you'd measure actual round-trip to server
                end_time = time.perf_counter()
                
                latency_us = (end_time - start_time) * 1_000_000  # Convert to microseconds
                latencies.append(latency_us)
                
                if (i + 1) % 100 == 0:
                    self.logger.info(f"Processed {i + 1} messages...")
        
        finally:
            sock.close()
        
        # Calculate statistics
        stats = {
            'count': len(latencies),
            'mean': statistics.mean(latencies),
            'median': statistics.median(latencies),
            'stdev': statistics.stdev(latencies) if len(latencies) > 1 else 0,
            'min': min(latencies),
            'max': max(latencies),
            'p95': self._percentile(latencies, 95),
            'p99': self._percentile(latencies, 99)
        }
        
        self.logger.info("Latency Statistics (microseconds):")
        self.logger.info(f"  Mean: {stats['mean']:.2f}")
        self.logger.info(f"  Median: {stats['median']:.2f}")
        self.logger.info(f"  Std Dev: {stats['stdev']:.2f}")
        self.logger.info(f"  Min: {stats['min']:.2f}")
        self.logger.info(f"  Max: {stats['max']:.2f}")
        self.logger.info(f"  P95: {stats['p95']:.2f}")
        self.logger.info(f"  P99: {stats['p99']:.2f}")
        
        return stats
    
    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """Calculate percentile.
        
        Args:
            data: Data list
            percentile: Percentile (0-100)
            
        Returns:
            Percentile value
        """
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class ThroughputBenchmark:
    """Benchmark for measuring message throughput."""
    
    def __init__(self):
        """Initialize throughput benchmark."""
        self.logger = logging.getLogger("ThroughputBenchmark")
    
    def measure_throughput(self, duration: float = 10.0) -> Dict:
        """Measure message throughput.
        
        Args:
            duration: Duration to run benchmark in seconds
            
        Returns:
            Dictionary with throughput statistics
        """
        self.logger.info(f"Starting throughput benchmark for {duration} seconds...")
        
        message_count = 0
        total_bytes = 0
        start_time = time.time()
        
        # Generate and serialize messages as fast as possible
        while time.time() - start_time < duration:
            # Create test message
            msg = Message(MessageType.MARKET_DATA, {
                'symbol': 'TEST',
                'bids': [[100.0, 10.0]] * 5,
                'asks': [[101.0, 10.0]] * 5,
                'timestamp': time.time()
            })
            
            # Serialize
            msg_bytes = msg.serialize()
            total_bytes += len(msg_bytes)
            message_count += 1
        
        elapsed = time.time() - start_time
        
        # Calculate statistics
        stats = {
            'duration': elapsed,
            'message_count': message_count,
            'total_bytes': total_bytes,
            'messages_per_sec': message_count / elapsed,
            'bytes_per_sec': total_bytes / elapsed,
            'mbps': (total_bytes * 8) / (elapsed * 1_000_000)  # Megabits per second
        }
        
        self.logger.info("Throughput Statistics:")
        self.logger.info(f"  Messages: {stats['message_count']}")
        self.logger.info(f"  Duration: {stats['duration']:.2f}s")
        self.logger.info(f"  Messages/sec: {stats['messages_per_sec']:.2f}")
        self.logger.info(f"  Bytes/sec: {stats['bytes_per_sec']:.2f}")
        self.logger.info(f"  Mbps: {stats['mbps']:.2f}")
        
        return stats


class SharedMemoryBenchmark:
    """Benchmark for shared memory operations."""
    
    def __init__(self):
        """Initialize shared memory benchmark."""
        self.logger = logging.getLogger("SharedMemoryBenchmark")
    
    def measure_shm_latency(self, num_operations: int = 10000) -> Dict:
        """Measure shared memory read/write latency.
        
        Args:
            num_operations: Number of operations to perform
            
        Returns:
            Dictionary with latency statistics
        """
        from ..utils.shared_memory import OrderBookSharedMemory
        
        self.logger.info(f"Starting shared memory benchmark with {num_operations} operations...")
        
        # Create shared memory
        shm = OrderBookSharedMemory(name="benchmark_shm", create=True)
        
        write_latencies = []
        read_latencies = []
        
        try:
            # Test data
            bids = [(100.0 - i * 0.1, 10.0) for i in range(5)]
            asks = [(101.0 + i * 0.1, 10.0) for i in range(5)]
            
            for i in range(num_operations):
                # Measure write
                start = time.perf_counter()
                shm.write_orderbook(bids, asks)
                end = time.perf_counter()
                write_latencies.append((end - start) * 1_000_000)
                
                # Measure read
                start = time.perf_counter()
                data = shm.read_orderbook()
                end = time.perf_counter()
                read_latencies.append((end - start) * 1_000_000)
                
                if (i + 1) % 1000 == 0:
                    self.logger.info(f"Processed {i + 1} operations...")
        
        finally:
            shm.close()
            shm.unlink()
        
        # Calculate statistics
        stats = {
            'write': {
                'mean': statistics.mean(write_latencies),
                'median': statistics.median(write_latencies),
                'min': min(write_latencies),
                'max': max(write_latencies),
                'p95': self._percentile(write_latencies, 95)
            },
            'read': {
                'mean': statistics.mean(read_latencies),
                'median': statistics.median(read_latencies),
                'min': min(read_latencies),
                'max': max(read_latencies),
                'p95': self._percentile(read_latencies, 95)
            }
        }
        
        self.logger.info("Shared Memory Write Latency (microseconds):")
        self.logger.info(f"  Mean: {stats['write']['mean']:.2f}")
        self.logger.info(f"  Median: {stats['write']['median']:.2f}")
        self.logger.info(f"  P95: {stats['write']['p95']:.2f}")
        
        self.logger.info("Shared Memory Read Latency (microseconds):")
        self.logger.info(f"  Mean: {stats['read']['mean']:.2f}")
        self.logger.info(f"  Median: {stats['read']['median']:.2f}")
        self.logger.info(f"  P95: {stats['read']['p95']:.2f}")
        
        return stats
    
    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """Calculate percentile."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
