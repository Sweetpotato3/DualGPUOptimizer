import unittest
import concurrent.futures
from dualgpuopt.memory.predictor import LRUCache


class TestLRUCache(unittest.TestCase):
    """Test suite for the LRUCache class in the memory predictor module"""

    def test_basic_cache_operations(self):
        """Test basic cache get/set operations"""
        cache = LRUCache(maxsize=3)
        
        # Test setting and getting values
        cache["key1"] = "value1"
        cache["key2"] = "value2"
        
        self.assertEqual(cache["key1"], "value1")
        self.assertEqual(cache["key2"], "value2")
        self.assertEqual(len(cache), 2)
        
        # Test updating a value
        cache["key1"] = "updated_value1"
        self.assertEqual(cache["key1"], "updated_value1")
        self.assertEqual(len(cache), 2)
        
        # Test key error for missing key
        with self.assertRaises(KeyError):
            _ = cache["nonexistent_key"]

    def test_lru_eviction(self):
        """Test LRU eviction policy works correctly"""
        cache = LRUCache(maxsize=3)
        
        # Fill the cache to capacity
        cache["key1"] = "value1"
        cache["key2"] = "value2"
        cache["key3"] = "value3"
        self.assertEqual(len(cache), 3)
        
        # Access key1 to make it most recently used
        _ = cache["key1"]
        
        # Add a new key, should evict key2 (least recently used)
        cache["key4"] = "value4"
        self.assertEqual(len(cache), 3)
        
        # key1, key3, key4 should exist, key2 should be evicted
        self.assertIn("key1", cache)
        self.assertIn("key3", cache)
        self.assertIn("key4", cache)
        self.assertNotIn("key2", cache)
        
        # Now access key3, then add another item
        _ = cache["key3"]
        cache["key5"] = "value5"
        
        # key3, key1, key5 should exist, key4 should be evicted
        self.assertIn("key1", cache)
        self.assertIn("key3", cache)
        self.assertIn("key5", cache)
        self.assertNotIn("key4", cache)

    def test_clear(self):
        """Test cache clear operation"""
        cache = LRUCache(maxsize=5)
        
        # Add some items
        cache["key1"] = "value1"
        cache["key2"] = "value2"
        cache["key3"] = "value3"
        
        # Clear the cache
        cache.clear()
        
        # Check that the cache is empty
        self.assertEqual(len(cache), 0)
        
        # Check that previous keys are no longer present
        with self.assertRaises(KeyError):
            _ = cache["key1"]

    def test_zero_size_cache(self):
        """Test cache with zero size (should keep at least 1 item)"""
        cache = LRUCache(maxsize=0)
        
        # Add an item, it should still be stored
        cache["key1"] = "value1"
        self.assertEqual(cache["key1"], "value1")
        
        # Add another item, it should replace the first one
        cache["key2"] = "value2"
        self.assertEqual(cache["key2"], "value2")
        
        # First key should be evicted
        with self.assertRaises(KeyError):
            _ = cache["key1"]

    def test_thread_safety(self):
        """Test thread safety of the cache implementation"""
        cache = LRUCache(maxsize=100)
        NUM_THREADS = 10
        NUM_OPERATIONS = 1000
        
        # Function to perform random cache operations
        def cache_worker(thread_id):
            for i in range(NUM_OPERATIONS):
                key = f"key_{thread_id}_{i}"
                try:
                    # Alternate between reads and writes
                    if i % 2 == 0:
                        cache[key] = f"value_{thread_id}_{i}"
                    else:
                        # Try to read a previous key
                        previous_key = f"key_{thread_id}_{i-1}"
                        if previous_key in cache:
                            _ = cache[previous_key]
                except Exception as e:
                    return False, str(e)
            return True, None
        
        # Run concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            futures = [executor.submit(cache_worker, thread_id) for thread_id in range(NUM_THREADS)]
            results = [future.result() for future in futures]
            
        # Check all threads completed successfully
        for success, error in results:
            self.assertTrue(success, f"Thread operation failed: {error}")

    def test_maxsize_enforcement(self):
        """Test that cache never exceeds maximum size"""
        cache = LRUCache(maxsize=10)
        
        # Add more items than maxsize
        for i in range(20):
            cache[f"key_{i}"] = f"value_{i}"
            
        # Cache size should not exceed maxsize
        self.assertLessEqual(len(cache), 10)
        
        # Most recent items should be in the cache
        for i in range(10, 20):
            self.assertIn(f"key_{i}", cache)

    def test_complex_keys_and_values(self):
        """Test cache with complex keys and values"""
        cache = LRUCache(maxsize=5)
        
        # Test with tuple keys
        key1 = (1, "test", 3.14)
        key2 = (2, "sample", 2.71)
        
        # Test with complex values
        value1 = {"name": "test", "data": [1, 2, 3]}
        value2 = ["sample", 123, {"nested": True}]
        
        cache[key1] = value1
        cache[key2] = value2
        
        self.assertEqual(cache[key1], value1)
        self.assertEqual(cache[key2], value2)
        
        # Modify complex value after retrieval (should not affect cached value)
        retrieved_value = cache[key1]
        retrieved_value["name"] = "modified"
        
        # Original value in cache should be unchanged
        self.assertEqual(cache[key1]["name"], "test")

    def test_move_to_end_on_access(self):
        """Test that accessing a key moves it to the end (making it most recently used)"""
        cache = LRUCache(maxsize=3)
        
        # Add items in order
        cache["key1"] = "value1"
        cache["key2"] = "value2"
        cache["key3"] = "value3"
        
        # Order should be: key1 (least recent), key2, key3 (most recent)
        # Access key1 to make it most recent
        _ = cache["key1"]
        
        # Now order should be: key2 (least recent), key3, key1 (most recent)
        # Add a new item to evict the least recent (key2)
        cache["key4"] = "value4"
        
        # key2 should be evicted, others should remain
        self.assertNotIn("key2", cache)
        self.assertIn("key1", cache)
        self.assertIn("key3", cache)
        self.assertIn("key4", cache)


if __name__ == "__main__":
    unittest.main() 