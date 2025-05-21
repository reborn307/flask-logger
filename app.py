from flask import Flask, request, jsonify, send_file
import csv
import os
from datetime import datetime

app = Flask(__name__)
CSV_FILE = "data_log.csv"

# Ensure CSV file exists and has headers
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'data'])

@app.route("/log", methods=["POST"])
def log_data():
    data = request.form.get("data")
    if not data:
        return jsonify({"error": "No data provided"}), 400

    timestamp = datetime.utcnow().isoformat()
    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, data])

    return jsonify({"message": "Data logged successfully"}), 200

@app.route("/download", methods=["GET"])
def download_csv():
    return send_file(CSV_FILE, as_attachment=True)

@app.route("/")
def home():
    return "Welcome to the Flask Logger API"

if __name__ == "__main__":
    app.run(debug=True)
