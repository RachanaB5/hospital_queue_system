# backend.py
from flask import Flask, request, jsonify
from queue_logic import TriageQueue, Patient
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

triage = TriageQueue()
history_log = []

@app.route('/')
def home():
    return "🚑 Hospital Queue Management API is running."

@app.route('/add_patient', methods=['POST'])
def add_patient():
    data = request.json
    patient = Patient(data['name'], data['condition'], data['severity'])
    triage.add_patient(patient)
    return jsonify({"message": "Patient added successfully"})

@app.route('/next_patient', methods=['GET'])
def next_patient():
    patient = triage.get_next_patient()
    if patient:
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

if __name__ == '__main__':
    app.run(debug=True)
