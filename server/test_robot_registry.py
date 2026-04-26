import time
import unittest
from server.core.robot_registry import RobotRegistry
from core.pose import Pose


class TestRobotRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = RobotRegistry()
        self.pose = Pose(x=1.0, y=2.0, theta=0.0)

    def test_register_robot(self):
        result = self.registry.register_robot("robot_1")
        self.assertTrue(result)
        self.assertIsNotNone(self.registry.get_robot("robot_1"))

    def test_register_duplicate(self):
        self.registry.register_robot("robot_1")
        result = self.registry.register_robot("robot_1")
        self.assertFalse(result)

    def test_unregister_robot(self):
        self.registry.register_robot("robot_1")
        result = self.registry.unregister_robot("robot_1")
        self.assertTrue(result)
        self.assertIsNone(self.registry.get_robot("robot_1"))

    def test_heartbeat_auto_registers(self):
        self.registry.update_heartbeat("robot_2", self.pose)
        self.assertIsNotNone(self.registry.get_robot("robot_2"))

    def test_heartbeat_idle_status(self):
        self.registry.update_heartbeat("robot_1", self.pose, task_id=None)
        self.assertEqual(self.registry.get_robot("robot_1").status, "IDLE")

    def test_heartbeat_busy_status(self):
        self.registry.update_heartbeat("robot_1", self.pose, task_id="task_1")
        self.assertEqual(self.registry.get_robot("robot_1").status, "BUSY")

    def test_heartbeat_updates_pose(self):
        self.registry.update_heartbeat("robot_1", self.pose)
        self.assertEqual(self.registry.get_robot("robot_1").pose.x, 1.0)
        self.assertEqual(self.registry.get_robot("robot_1").pose.y, 2.0)

    def test_task_status_done_sets_idle(self):
        self.registry.update_heartbeat("robot_1", self.pose, task_id="task_1")
        self.registry.update_task_status("robot_1", "task_1", "DONE")
        robot = self.registry.get_robot("robot_1")
        self.assertEqual(robot.status, "IDLE")
        self.assertIsNone(robot.current_task_id)

    def test_task_status_rejected_sets_idle(self):
        self.registry.update_heartbeat("robot_1", self.pose, task_id="task_1")
        self.registry.update_task_status("robot_1", "task_1", "REJECTED")
        self.assertEqual(self.registry.get_robot("robot_1").status, "IDLE")

    def test_set_aisle(self):
        self.registry.register_robot("robot_1")
        self.registry.set_aisle("robot_1", "aisle_3")
        self.assertEqual(self.registry.get_robot("robot_1").current_aisle_id, "aisle_3")

    def test_get_idle_robots(self):
        self.registry.update_heartbeat("robot_1", self.pose, task_id=None)
        self.registry.update_heartbeat("robot_2", self.pose, task_id="task_1")
        idle = self.registry.get_idle_robots()
        self.assertIn("robot_1", idle)
        self.assertNotIn("robot_2", idle)

    def test_get_busy_robots(self):
        self.registry.update_heartbeat("robot_1", self.pose, task_id=None)
        self.registry.update_heartbeat("robot_2", self.pose, task_id="task_1")
        busy = self.registry.get_busy_robots()
        self.assertIn("robot_2", busy)
        self.assertNotIn("robot_1", busy)

    def test_three_robots(self):
        self.registry.update_heartbeat("robot_1", self.pose, task_id=None)
        self.registry.update_heartbeat("robot_2", self.pose, task_id="task_1")
        self.registry.update_heartbeat("robot_3", self.pose, task_id="task_2")
        self.assertEqual(self.registry.get_robot_count(), 3)
        self.assertEqual(self.registry.get_connected_count(), 3)
        self.assertEqual(len(self.registry.get_idle_robots()), 1)
        self.assertEqual(len(self.registry.get_busy_robots()), 2)

    def test_is_connected(self):
        self.registry.update_heartbeat("robot_1", self.pose)
        self.assertTrue(self.registry.is_connected("robot_1"))

    def test_is_disconnected_after_timeout(self):
        self.registry.register_robot("robot_1")
        # last_heartbeat stays 0.0, so it's instantly "disconnected"
        self.assertFalse(self.registry.is_connected("robot_1"))


if __name__ == "__main__":
    unittest.main()
