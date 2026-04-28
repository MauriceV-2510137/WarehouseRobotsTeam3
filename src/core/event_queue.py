import queue
from queue import Queue
from core.events import Event

class EventQueue:
    def __init__(self):
        self._queue = Queue()

    def publish(self, event: Event):
        self._queue.put(event)

    def poll_all(self):
        events = []
        try:
            while True:
                events.append(self._queue.get_nowait())
        except queue.Empty:
            pass
        return events