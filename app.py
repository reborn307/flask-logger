from flask import Flask, request, jsonify, send_file
import csv, os, json
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

# Ensure CSV headers
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "device_id","batch_id","data_index",
            "accX","accY","accZ","gyrX","gyrY","gyrZ","temperature",
            "latitude","longitude","timestamp"
        ])

# ---------------- Upload endpoint ----------------
@app.route("/", methods=["POST"])
def log_data():
    try:
        data = request.get_json()
        device_id = data["device_id"]
        batch_id = data["batch_id"]
        samples = data["samples"]

        doc_ref = db.collection("drive_tests").document(device_id)

        for s in samples:
            index = str(s["index"]).zfill(3)
            payload = {
                "accX": s["accX"],
                "accY": s["accY"],
                "accZ": s["accZ"],
                "gyrX": s["gyrX"],
                "gyrY": s["gyrY"],
                "gyrZ": s["gyrZ"],
                "temperature": s["temperature"],
                "latitude": s["latitude"] if s["latitude"] != 0 else "N/A",
                "longitude": s["longitude"] if s["longitude"] != 0 else "N/A",
                "timestamp": s["timestamp"]
            }

            # Firestore storage
            doc_ref.collection(batch_id).document(index).set(payload)

            # CSV storage
            with open(CSV_FILE,'a',newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    device_id,
                    batch_id,
                    index,
                    payload["accX"],
                    payload["accY"],
                    payload["accZ"],
                    payload["gyrX"],
                    payload["gyrY"],
                    payload["gyrZ"],
                    payload["temperature"],
                    payload["latitude"],
                    payload["longitude"],
                    payload["timestamp"]
                ])
        return jsonify({"status":"success","samples_uploaded":len(samples)})
    except Exception as e:
        return jsonify({"error":str(e)}),500

# ---------------- Download CSV ----------------
@app.route("/download", methods=["GET"])
def download_file():
    if os.path.exists(CSV_FILE):
        return send_file(CSV_FILE, as_attachment=True)
    else:
        return jsonify({"status":"error","message":"CSV file not found"}),404

# ---------------- Read CSV as JSON ----------------
@app.route("/read", methods=["GET"])
def read_data():
    if not os.path.exists(CSV_FILE):
        return jsonify({"status":"error","message":"CSV file not found"}),404

    data_list = []
    try:
        with open(CSV_FILE, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data_list.append(row)
        return jsonify({"status":"success","data":data_list})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}),500

