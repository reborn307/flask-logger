from flask import Flask, request, jsonify, send_file
import csv
import os
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

CSV_FILE = "data_log.csv"

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    firebase_json = os.environ.get("FIREBASE_CREDENTIALS")
    cred_dict = json.loads(firebase_json)
    cred = credentials.Certificate(cred_dict)
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
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON body"}), 400

        device_id = data["device_id"]
        batch_id = data["batch_id"]
        samples = data["samples"]

        doc_ref = db.collection("drive_tests").document(device_id)

        for sample in samples:
            index = str(sample["index"]).zfill(3)

            payload = {
                "accX": sample["accX"],
                "accY": sample["accY"],
                "accZ": sample["accZ"],
                "gyrX": sample["gyrX"],
                "gyrY": sample["gyrY"],
                "gyrZ": sample["gyrZ"],
                "temperature": sample["temperature"],
                "latitude": sample["latitude"] if sample["latitude"] != 0 else "N/A",
                "longitude": sample["longitude"] if sample["longitude"] != 0 else "N/A",
                "timestamp": sample["timestamp"]
            }

            # Firestore path:
            # drive_tests / SRAS01 / batch_xx.xx / 001
            doc_ref.collection(batch_id).document(index).set(payload)

            # CSV logging (optional, still works)
            with open(CSV_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    device_id,
                    batch_id,
                    index,
                    payload["accX"],
                    payload["accY"],
                    payload["accZ"],
                    payload["temperature"],
                    payload["latitude"],
                    payload["longitude"],
                    payload["timestamp"]
                ])

        return jsonify({
            "status": "success",
            "samples_uploaded": len(samples)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

