#!/usr/bin/env python3
"""
Main orchestrator for the multi-process trading system.
Launches and manages all processes.
"""
import time
import signal
import sys
import logging
from multiprocessing import Process
import argparse

from src.processes.gateway import run_gateway
from src.processes.orderbook import run_orderbook
from src.processes.strategy import run_strategy
from src.processes.ordermanager import run_ordermanager
from src.utils.config import Config
from src.utils.shared_memory import OrderBookSharedMemory


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class TradingSystem:
    """Main trading system orchestrator."""
    
    def __init__(self, duration: int = None):
        """Initialize trading system.
        
        Args:
            duration: Duration to run system in seconds (None for indefinite)
        """
        self.logger = logging.getLogger("TradingSystem")
        self.processes = {}
        self.duration = duration
        self.shutdown_requested = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_requested = True
    
    def start_processes(self):
        """Start all trading system processes."""
        self.logger.info("Starting trading system processes...")
        
        # Start Gateway
        self.logger.info("Starting Gateway process...")
        gateway_process = Process(target=run_gateway, name="Gateway")
        gateway_process.start()
        self.processes['gateway'] = gateway_process
        time.sleep(1)  # Give Gateway time to start
        
        # Start OrderManager
        self.logger.info("Starting OrderManager process...")
        om_process = Process(target=run_ordermanager, name="OrderManager")
        om_process.start()
        self.processes['ordermanager'] = om_process
        time.sleep(1)  # Give OrderManager time to start
        
        # Start OrderBook
        self.logger.info("Starting OrderBook process...")
        ob_process = Process(target=run_orderbook, name="OrderBook")
        ob_process.start()
        self.processes['orderbook'] = ob_process
        time.sleep(1)  # Give OrderBook time to connect
        
        # Start Strategy
        self.logger.info("Starting Strategy process...")
        strategy_process = Process(target=run_strategy, name="Strategy")
        strategy_process.start()
        self.processes['strategy'] = strategy_process
        time.sleep(1)  # Give Strategy time to connect
        
        self.logger.info("All processes started successfully")
    
    def monitor_processes(self):
        """Monitor running processes."""
        start_time = time.time()
        
        while not self.shutdown_requested:
            # Check if duration has elapsed
            if self.duration and (time.time() - start_time) >= self.duration:
                self.logger.info(f"Duration of {self.duration} seconds elapsed")
                break
            
            # Check if all processes are still alive
            all_alive = True
            for name, process in self.processes.items():
                if not process.is_alive():
                    self.logger.error(f"Process {name} has died unexpectedly!")
                    all_alive = False
            
            if not all_alive:
                self.logger.error("One or more processes died, shutting down system...")
                break
            
            # Sleep briefly
            time.sleep(1)
    
    def shutdown_processes(self):
        """Shutdown all processes gracefully."""
        self.logger.info("Shutting down all processes...")
        
        # Terminate processes in reverse order
        for name in ['strategy', 'orderbook', 'ordermanager', 'gateway']:
            if name in self.processes:
                process = self.processes[name]
                if process.is_alive():
                    self.logger.info(f"Terminating {name}...")
                    process.terminate()
                    process.join(timeout=Config.SHUTDOWN_TIMEOUT)
                    
                    if process.is_alive():
                        self.logger.warning(f"Force killing {name}...")
                        process.kill()
                        process.join()
        
        # Clean up shared memory
        try:
            shm = OrderBookSharedMemory(name=Config.ORDERBOOK_SHM_NAME, create=False)
            shm.close()
            shm.unlink()
            self.logger.info("Cleaned up shared memory")
        except Exception as e:
            self.logger.warning(f"Could not clean up shared memory: {e}")
        
        self.logger.info("All processes shut down")
    
    def run(self):
        """Run the trading system."""
        self.logger.info("=" * 60)
        self.logger.info("Multi-Process Trading System")
        self.logger.info("=" * 60)
        
        try:
            # Start all processes
            self.start_processes()
            
            # Monitor processes
            self.logger.info("System running. Press Ctrl+C to stop.")
            self.monitor_processes()
        
        except Exception as e:
            self.logger.error(f"Error running trading system: {e}")
        
        finally:
            # Shutdown
            self.shutdown_processes()
            self.logger.info("Trading system terminated")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Multi-Process Trading System")
    parser.add_argument(
        '--duration',
        type=int,
        default=None,
        help='Duration to run system in seconds (default: run indefinitely)'
    )
    
    args = parser.parse_args()
    
    # Create and run trading system
    system = TradingSystem(duration=args.duration)
    system.run()


if __name__ == '__main__':
    main()
