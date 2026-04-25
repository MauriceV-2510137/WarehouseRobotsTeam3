from queue import Queue
from core.events import Event

class EventQueue:
    def __init__(self):
        self._queue = Queue()

    def publish(self, event: Event):
        self._queue.put(event)

    def poll_all(self):
        events = []
        while not self._queue.empty():
            events.append(self._queue.get())
        return events