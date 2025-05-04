import heapq
import time

class Patient:
    def __init__(self, name, condition, severity):
        self.name = name
        self.condition = condition
        self.severity = severity
        self.timestamp = time.time()

    def __lt__(self, other):
        # Lower severity number = higher priority
        return (self.severity, self.timestamp) < (other.severity, other.timestamp)

class TriageQueue:
    def __init__(self):
        self.pq = []

    def add_patient(self, patient):
        heapq.heappush(self.pq, patient)

    def get_next_patient(self):
        return heapq.heappop(self.pq) if self.pq else None

    def view_queue(self):
        return sorted(self.pq)
