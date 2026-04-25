"""
Unit tests for the AisleManager class.
"""
import time
import unittest
from server.core.aisle_manager import AisleManager


class TestAisleManager(unittest.TestCase):
    
    def setUp(self):
        """Create a fresh AisleManager for each test."""
        self.manager = AisleManager(lock_timeout=2)  # 2 second timeout for fast tests
    
    def test_grant_new_aisle(self):
        """Test that a new aisle request is granted."""
        result = self.manager.request_aisle("robot1", "aisle1", "task1")
        self.assertTrue(result)
        self.assertTrue(self.manager.is_aisle_locked("aisle1"))
    
    def test_deny_locked_aisle(self):
        """Test that a locked aisle is denied to another robot."""
        # First robot locks aisle
        self.manager.request_aisle("robot1", "aisle1", "task1")
        
        # Second robot tries to access same aisle
        result = self.manager.request_aisle("robot2", "aisle1", "task2")
        self.assertFalse(result)
    
    def test_same_robot_can_reaccess(self):
        """Test that the same robot can re-access its locked aisle."""
        self.manager.request_aisle("robot1", "aisle1", "task1")
        
        # Same robot requests again
        result = self.manager.request_aisle("robot1", "aisle1", "task2")
        self.assertTrue(result)
    
    def test_release_aisle(self):
        """Test releasing a specific aisle."""
        self.manager.request_aisle("robot1", "aisle1", "task1")
        
        # Release the aisle
        result = self.manager.release_aisle("robot1", "aisle1")
        self.assertTrue(result)
        self.assertFalse(self.manager.is_aisle_locked("aisle1"))
    
    def test_release_robot(self):
        """Test releasing all aisles for a robot."""
        self.manager.request_aisle("robot1", "aisle1", "task1")
        self.manager.request_aisle("robot1", "aisle2", "task2")
        
        # Release all for robot
        count = self.manager.release_robot("robot1")
        self.assertEqual(count, 2)
        self.assertFalse(self.manager.is_aisle_locked("aisle1"))
        self.assertFalse(self.manager.is_aisle_locked("aisle2"))
    
    def test_lock_expiration(self):
        """Test that locks expire after timeout."""
        self.manager.request_aisle("robot1", "aisle1", "task1")
        
        # Wait for lock to expire
        time.sleep(2.5)
        
        # Lock should be expired
        self.assertFalse(self.manager.is_aisle_locked("aisle1"))
        
        # New request should be granted
        result = self.manager.request_aisle("robot2", "aisle1", "task2")
        self.assertTrue(result)
    
    def test_get_locked_aisles(self):
        """Test getting all locked aisles."""
        self.manager.request_aisle("robot1", "aisle1", "task1")
        self.manager.request_aisle("robot2", "aisle2", "task2")
        
        locked = self.manager.get_locked_aisles()
        self.assertEqual(len(locked), 2)
        self.assertEqual(locked["aisle1"], "robot1")
        self.assertEqual(locked["aisle2"], "robot2")
    
    def test_get_robot_aisle(self):
        """Test getting the aisle locked by a robot."""
        self.manager.request_aisle("robot1", "aisle1", "task1")
        
        aisle = self.manager.get_robot_aisle("robot1")
        self.assertEqual(aisle, "aisle1")
    
    def test_cleanup_expired_locks(self):
        """Test cleaning up expired locks."""
        self.manager.request_aisle("robot1", "aisle1", "task1")
        
        # Wait for expiration
        time.sleep(2.5)
        
        # Cleanup
        count = self.manager.cleanup_expired_locks()
        self.assertEqual(count, 1)
        self.assertFalse(self.manager.is_aisle_locked("aisle1"))


if __name__ == "__main__":
    unittest.main()