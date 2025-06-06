from flask import Flask, request, jsonify 
import csv
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate(r"C:\Users\tolul\Downloads\road-anomaly-9eec5-firebase-adminsdk-fbsvc-1fbc6dac2b.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

CSV_FILE = "data_log.csv"

# Ensure CSV file exists
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "device_id", "batch_id", "data_index", "accX", "accY", "accZ",
            "gyroX", "gyroY", "gyroZ", "temperature", "vibration",
            "latitude", "longitude", "timestamp"
        ])

# Store batch information in memory (for demo purposes)
current_batches = {}

@app.route("/api/data", methods=["POST"])
def log_data():
    device_id = request.form.get("device_id")
    data = request.form.get("data")

    if not device_id or not data:
        return jsonify({"status": "error", "message": "Missing device_id or data"}), 400

    try:
        values = data.split(",")
        if len(values) != 12:  # counter + 11 values
            return jsonify({"status": "error", "message": "Invalid data format"}), 400

        # Get or create batch ID
        batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare data for Firestore
        firestore_data = {
            "accX": float(values[2]) if values[2] != "N/A" else None,
            "accY": float(values[3]) if values[3] != "N/A" else None,
            "accZ": float(values[4]) if values[4] != "N/A" else None,
            "gyroX": float(values[5]) if values[5] != "N/A" else None,
            "gyroY": float(values[6]) if values[6] != "N/A" else None,
            "gyroZ": float(values[7]) if values[7] != "N/A" else None,
            "temperature": float(values[8]) if values[8] != "N/A" else None,
            "vibration": float(values[1]) if values[1] != "N/A" else None,
            "latitude": float(values[9]) if values[9] != "N/A" else None,
            "longitude": float(values[10]) if values[10] != "N/A" else None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Save to Firestore
        doc_ref = db.collection("drive_tests") \
                   .document(device_id) \
                   .collection(batch_id) \
                   .document(values[0])  # Using counter as document ID
        doc_ref.set(firestore_data)

        # Save to CSV (backup)
        csv_data = [device_id, batch_id] + values
        with open(CSV_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(csv_data)

        return jsonify({
            "status": "success",
            "message": "Data logged successfully",
            "batch_id": batch_id
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Keep your existing /download and /read endpoints unchanged
from flask import send_file

@app.route("/download", methods=["GET"])
def download_file():
    if os.path.exists(CSV_FILE):
        return send_file(CSV_FILE, as_attachment=True)
    else:
        return jsonify({"status": "error", "message": "CSV file not found"}), 404


@app.route("/read", methods=["GET"])
def read_data():
    if not os.path.exists(CSV_FILE):
        return jsonify({"status": "error", "message": "CSV file not found"}), 404

    data_list = []
    try:
        with open(CSV_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data_list.append(row)

        return jsonify({"status": "success", "data": data_list})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



if __name__ == "__main__":
    app.run()
