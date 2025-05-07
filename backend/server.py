from flask import Flask, request, jsonify
from queue_logic import TriageQueue, Patient
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)

triage = TriageQueue()
history_log = []

def validate_timestamp(timestamp_str):
    try:
        datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False

@app.route('/')
def home():
    return "🚑 Hospital Queue Management API is running."

@app.route('/add_patient', methods=['POST'])
def add_patient():
    data = request.json
    # Create patient with additional arrival_time property
    patient = Patient(
        name=data['name'], 
        condition=data['condition'], 
        severity=data['severity']
    )
    
    # Add arrival time to patient object
    patient.arrival_time = data.get('arrival_time', datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    
    triage.add_patient(patient)
    return jsonify({"message": "Patient added successfully"})

@app.route('/next_patient', methods=['GET'])
def next_patient():
    patient = triage.get_next_patient()
    if patient:
        # Add the patient to history log
        history_log.append(vars(patient))
        return jsonify(vars(patient))
    else:
        return jsonify({"message": "No patients in queue"}), 404

@app.route('/view_queue', methods=['GET'])
def view_queue():
    return jsonify([vars(p) for p in triage.view_queue()])

@app.route('/history', methods=['GET'])
def history():
    return jsonify(history_log)

@app.route('/mark_treated', methods=['POST'])
def mark_treated():
    data = request.json
    patient_name = data.get('name')
    
    if not patient_name:
        return jsonify({"error": "Patient name is required"}), 400
    
    # Find patient in queue
    queue = triage.view_queue()
    found = False
    
    for i, patient in enumerate(queue):
        if patient.name == patient_name:
            # Add to history
            history_log.append(vars(patient))
            
            # Remove from queue
            triage.remove_patient(i)
            found = True
            break
    
    if found:
        return jsonify({"message": f"Patient {patient_name} marked as treated"})
    else:
        return jsonify({"error": "Patient not found in queue"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5002)
