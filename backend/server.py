from flask import Flask, request, jsonify
from queue_logic import TriageQueue, Patient
from flask_cors import CORS
import datetime
import logging
import pytz

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

triage = TriageQueue()
history_log = []

def get_utc_timestamp():
    """Generate a UTC timestamp in a consistent format"""
    return datetime.datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")

def parse_timestamp(timestamp_str):
    """Parse and standardize timestamp format"""
    try:
        # Try to parse with timezone info first
        dt = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        # If parsing fails, return a new UTC timestamp
        logger.warning(f"Failed to parse timestamp: {timestamp_str}, using current UTC time")
        return get_utc_timestamp()

@app.route('/')
def home():
    return "🚑 Hospital Queue Management API is running."

@app.route('/add_patient', methods=['POST'])
def add_patient():
    data = request.json
    logger.info(f"Received patient data: {data}")
    
    # Create patient with additional arrival_time property
    patient = Patient(
        name=data['name'], 
        condition=data['condition'], 
        severity=data['severity']
    )
    
    # Handle arrival time with robust parsing
    if 'arrival_time' in data and data['arrival_time']:
        arrival_time = parse_timestamp(data['arrival_time'])
        logger.info(f"Using provided arrival time: {arrival_time}")
    else:
        arrival_time = get_utc_timestamp()
        logger.info(f"Generated new arrival time: {arrival_time}")
    
    patient.arrival_time = arrival_time
    
    triage.add_patient(patient)
    return jsonify({"message": "Patient added successfully", "arrival_time": patient.arrival_time})

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
    logger.info(f"Mark treated request: {data}")
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
            logger.info(f"Patient {patient_name} marked as treated")
            break
    
    if found:
        return jsonify({"message": f"Patient {patient_name} marked as treated"})
    else:
        logger.warning(f"Patient {patient_name} not found in queue")
        return jsonify({"error": "Patient not found in queue"}), 404

@app.route('/debug/timestamp', methods=['GET'])
def debug_timestamp():
    """Debug endpoint to check server timestamp handling"""
    now = datetime.datetime.now()
    utc_now = datetime.datetime.now(pytz.UTC)
    
    return jsonify({
        'local_time': str(now),
        'local_formatted': now.strftime("%Y-%m-%d %H:%M:%S"),
        'utc_time': str(utc_now),
        'utc_formatted': utc_now.strftime("%Y-%m-%d %H:%M:%S"),
        'timestamp': now.timestamp(),
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
