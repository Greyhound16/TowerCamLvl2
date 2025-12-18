from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import os

app = Flask(__name__)
CORS(app)

reports = []         # Current batch of 3 phone reports
latest_fire = None   # Last triangulated fire location

# Convert lat/lon to planar x/y for triangulation
def latlon_to_xy(lat, lon, lat0, lon0):
    R = 6371000
    x = R * np.radians(lon - lon0) * np.cos(np.radians(lat0))
    y = R * np.radians(lat - lat0)
    return x, y

# Convert back from planar x/y to lat/lon
def xy_to_latlon(x, y, lat0, lon0):
    R = 6371000
    lat = y / R + np.radians(lat0)
    lon = x / (R * np.cos(np.radians(lat0))) + np.radians(lon0)
    return np.degrees(lat), np.degrees(lon)

# Triangulation using least squares
def triangulate(points, bearings):
    A, b = [], []
    for (x, y), brg in zip(points, bearings):
        theta = np.radians(brg)
        a = np.array([np.sin(theta), -np.cos(theta)])
        A.append(a)
        b.append(np.dot(a, [x, y]))
    A, b = np.array(A), np.array(b)
    pos, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    return pos

@app.route("/report", methods=["POST"])
def report():
    global reports, latest_fire
    data = request.json
    reports.append(data)

    # Wait until 3 reports are received
    if len(reports) == 3:
        lat0, lon0 = reports[0]["lat"], reports[0]["lon"]
        points, bearings = [], []

        for r in reports:
            x, y = latlon_to_xy(r["lat"], r["lon"], lat0, lon0)
            points.append((x, y))
            bearings.append(r["bearing"])

        x, y = triangulate(points, bearings)
        fire_lat, fire_lon = xy_to_latlon(x, y, lat0, lon0)

        latest_fire = {"lat": fire_lat, "lon": fire_lon}
        reports = []  # Reset for next batch

        print("🔥 FIRE LOCATION:", fire_lat, fire_lon)
        return jsonify(latest_fire)

    return jsonify({"status": "waiting"})

@app.route("/latest")
def latest():
    return jsonify(latest_fire or {})

@app.route("/reports")
def get_reports():
    return jsonify(reports)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
