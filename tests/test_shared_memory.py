"""
Tests for shared memory.
"""
import unittest
import time
from src.utils.shared_memory import OrderBookSharedMemory


class TestSharedMemory(unittest.TestCase):
    """Test shared memory functionality."""
    
    def setUp(self):
        """Set up test."""
        self.shm_name = "test_orderbook_shm"
        self.shm = OrderBookSharedMemory(name=self.shm_name, create=True)
    
    def tearDown(self):
        """Clean up test."""
        if hasattr(self, 'shm'):
            self.shm.close()
            self.shm.unlink()
    
    def test_write_read_orderbook(self):
        """Test writing and reading order book."""
        bids = [(100.0, 10.0), (99.9, 20.0), (99.8, 15.0)]
        asks = [(100.1, 10.0), (100.2, 20.0), (100.3, 15.0)]
        
        # Write
        self.shm.write_orderbook(bids, asks)
        
        # Read
        data = self.shm.read_orderbook()
        
        self.assertIsNotNone(data)
        self.assertIn('timestamp', data)
        self.assertIn('bids', data)
        self.assertIn('asks', data)
        
        self.assertEqual(len(data['bids']), len(bids))
        self.assertEqual(len(data['asks']), len(asks))
        
        # Check values
        for i, (price, size) in enumerate(bids):
            self.assertAlmostEqual(data['bids'][i][0], price)
            self.assertAlmostEqual(data['bids'][i][1], size)
        
        for i, (price, size) in enumerate(asks):
            self.assertAlmostEqual(data['asks'][i][0], price)
            self.assertAlmostEqual(data['asks'][i][1], size)
    
    def test_get_best_bid_ask(self):
        """Test getting best bid and ask."""
        bids = [(100.0, 10.0), (99.9, 20.0)]
        asks = [(100.1, 10.0), (100.2, 20.0)]
        
        self.shm.write_orderbook(bids, asks)
        
        best_bid, best_ask = self.shm.get_best_bid_ask()
        
        self.assertEqual(best_bid, 100.0)
        self.assertEqual(best_ask, 100.1)
    
    def test_empty_orderbook(self):
        """Test reading empty order book."""
        # Initially, order book should be empty
        data = self.shm.read_orderbook()
        self.assertIsNone(data)
    
    def test_multiple_writes(self):
        """Test multiple writes update correctly."""
        # First write
        bids1 = [(100.0, 10.0)]
        asks1 = [(100.1, 10.0)]
        self.shm.write_orderbook(bids1, asks1)
        
        time.sleep(0.01)  # Small delay
        
        # Second write
        bids2 = [(101.0, 20.0)]
        asks2 = [(101.1, 20.0)]
        self.shm.write_orderbook(bids2, asks2)
        
        # Read should get second write
        data = self.shm.read_orderbook()
        self.assertEqual(data['bids'][0][0], 101.0)
        self.assertEqual(data['asks'][0][0], 101.1)


if __name__ == '__main__':
    unittest.main()
