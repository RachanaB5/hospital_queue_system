import heapq
import time

class Patient:
    def __init__(self, name, condition, severity):
        self.name = name
        self.condition = condition
        self.severity = severity
        self.arrival_time = time.time()  # tie-breaker

    def __lt__(self, other):
        # First by severity, then by arrival time
        return (self.severity, self.arrival_time) < (other.severity, other.arrival_time)

class TriageQueue:
    def __init__(self):
        self.heap = []

    def add_patient(self, patient):
        heapq.heappush(self.heap, patient)

    def get_next_patient(self):
        if self.heap:
            return heapq.heappop(self.heap)
        return None

    def view_queue(self):
        return list(self.heap)
