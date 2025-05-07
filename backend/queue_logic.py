class Patient:
    def __init__(self, name, condition, severity):
        self.name = name
        self.condition = condition
        self.severity = severity
        self.arrival_time = None  # Will be set when adding to queue

class TriageQueue:
    def __init__(self):
        self.queue = []
    
    def add_patient(self, patient):
        """Add a patient to the queue and sort by severity"""
        self.queue.append(patient)
        self.queue.sort(key=lambda x: x.severity)  # Sort by severity (1 is highest priority)
    
    def get_next_patient(self):
        """Get the next patient in the queue (highest severity)"""
        if self.queue:
            return self.queue.pop(0)  # Remove and return the first patient
        return None
    
    def view_queue(self):
        """View the current queue without modifying it"""
        return self.queue.copy()
    
    def remove_patient(self, index):
        """Remove a patient at the specified index"""
        if 0 <= index < len(self.queue):
            return self.queue.pop(index)
        return None
