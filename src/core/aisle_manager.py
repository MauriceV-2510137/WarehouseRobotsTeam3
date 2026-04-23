from collections import deque

class AisleManager:
    def __init__(self, num_aisles):
        self.num_aisles = num_aisles
        self.aisles = [False] * num_aisles  # False = free
        self.requests = [deque() for _ in range(num_aisles)]  # queue of robot_ids

    def request_aisle(self, aisle_id, robot_id):
        if aisle_id < 0 or aisle_id >= self.num_aisles:
            return False
        if not self.aisles[aisle_id]:
            self.aisles[aisle_id] = True
            return True  # granted
        else:
            self.requests[aisle_id].append(robot_id)
            return False  # queued

    def release_aisle(self, aisle_id):
        if aisle_id < 0 or aisle_id >= self.num_aisles:
            return
        self.aisles[aisle_id] = False
        if self.requests[aisle_id]:
            next_robot = self.requests[aisle_id].popleft()
            self.aisles[aisle_id] = True
            return next_robot  # notify or something, but for now return
        return None

    def is_aisle_free(self, aisle_id):
        return not self.aisles[aisle_id]