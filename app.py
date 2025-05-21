from flask import Flask, request, jsonify
import csv
import os
from datetime import datetime

app = Flask(__name__)

CSV_FILE = "data_log.csv"

# Ensure the CSV file has headers if it doesn't exist
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "accX", "accY", "accZ",
            "gyroX", "gyroY", "gyroZ",
            "temperature", "vibration",
            "latitude", "longitude", "timestamp"
        ])

@app.route("/", methods=["POST"])
def log_data():
    data = request.form.get("data")

    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    try:
        values = data.split(",")
        if len(values) != 11:
            return jsonify({"status": "error", "message": "Invalid data format"}), 400

        # Save to CSV
        with open(CSV_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(values)

        return jsonify({"status": "success", "message": "Data logged successfully"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
