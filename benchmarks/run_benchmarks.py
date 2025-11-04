#!/usr/bin/env python3
"""
Benchmark runner for the trading system.
"""
import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.benchmarks import (
    ThroughputBenchmark,
    SharedMemoryBenchmark
)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Trading System Benchmarks")
    parser.add_argument(
        '--test',
        choices=['throughput', 'shm', 'all'],
        default='all',
        help='Which benchmark to run'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=10.0,
        help='Duration for throughput test (seconds)'
    )
    parser.add_argument(
        '--operations',
        type=int,
        default=10000,
        help='Number of operations for shared memory test'
    )
    
    args = parser.parse_args()
    
    if args.test in ['throughput', 'all']:
        print("\n" + "=" * 60)
        print("THROUGHPUT BENCHMARK")
        print("=" * 60)
        tb = ThroughputBenchmark()
        tb.measure_throughput(duration=args.duration)
    
    if args.test in ['shm', 'all']:
        print("\n" + "=" * 60)
        print("SHARED MEMORY BENCHMARK")
        print("=" * 60)
        shm_b = SharedMemoryBenchmark()
        shm_b.measure_shm_latency(num_operations=args.operations)
    
    print("\n" + "=" * 60)
    print("BENCHMARKS COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()
