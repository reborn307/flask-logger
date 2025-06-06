from flask import Flask, request, jsonify, send_file
import csv
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

CSV_FILE = "data_log.csv"

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
cred = credentials.Certificate(r"C:\Users\tolul\Downloads\road-anomaly-9eec5-firebase-adminsdk-fbsvc-1fbc6dac2b.json") # Make sure this file is in your root directory
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Ensure the CSV file has headers if it doesn't exist
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "device_id", "batch_id", "data_index",
            "accX", "accY", "accZ", "temperature",
            "latitude", "longitude", "timestamp"
        ])

@app.route("/", methods=["POST"])
def log_data():
    raw_data = request.form.get("data")

    if not raw_data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    try:
        fields = raw_data.strip().split(",")
        if len(fields) != 10:
            return jsonify({"status": "error", "message": "Invalid data format"}), 400

        # Extract values
        device_id = fields[0].strip()
        batch_id = fields[1].strip().replace("Batch", "batch_")  # Normalize batch ID
        data_index = fields[2].strip().zfill(3)  # e.g., "001"
        accX, accY, accZ = map(float, fields[3:6])
        temperature = float(fields[6])
        latitude = None if fields[7] == "N/A" else float(fields[7])
        longitude = None if fields[8] == "N/A" else float(fields[8])
        timestamp = fields[9].strip()

        # Save to CSV
        with open(CSV_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([device_id, batch_id, data_index, accX, accY, accZ, temperature, latitude, longitude, timestamp])

        # Save to Firestore
        doc_ref = db.collection("drive_tests").document(device_id)
        batch_ref = doc_ref.collection(batch_id).document(data_index)

        payload = {
            "accX": accX,
            "accY": accY,
            "accZ": accZ,
            "temperature": temperature,
            "latitude": latitude if latitude is not None else "N/A",
            "longitude": longitude if longitude is not None else "N/A",
            "timestamp": timestamp
        }

        batch_ref.set(payload)

        return jsonify({"status": "success", "message": "Data logged and uploaded to Firestore"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
