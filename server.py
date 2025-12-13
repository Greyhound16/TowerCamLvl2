from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np

app = Flask(__name__)
CORS(app)

reports = []
latest_fire = None

def triangulate(points, bearings):
    A, b = [], []
    for (x0, y0), theta in zip(points, bearings):
        a = np.array([np.sin(theta), -np.cos(theta)])
        A.append(a)
        b.append(np.dot(a, [x0, y0]))
    A, b = np.array(A), np.array(b)
    pos, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    return pos

def latlon_to_xy(lat, lon, lat0, lon0):
    R = 6371000
    x = R * np.radians(lon - lon0) * np.cos(np.radians(lat0))
    y = R * np.radians(lat - lat0)
    return x, y

def xy_to_latlon(x, y, lat0, lon0):
    R = 6371000
    lat = y / R + np.radians(lat0)
    lon = x / (R * np.cos(np.radians(lat0))) + np.radians(lon0)
    return np.degrees(lat), np.degrees(lon)

@app.route("/report", methods=["POST"])
def report():
    global reports, latest_fire
    data = request.json
    reports.append(data)

    if len(reports) >= 3:
        lat0, lon0 = reports[0]["lat"], reports[0]["lon"]
        points, bearings = [], []

        for r in reports[:3]:
            x, y = latlon_to_xy(r["lat"], r["lon"], lat0, lon0)
            points.append((x, y))
            bearings.append(np.radians(r["bearing"]))

        fx, fy = triangulate(points, bearings)
        fire_lat, fire_lon = xy_to_latlon(fx, fy, lat0, lon0)

        latest_fire = {
            "lat": fire_lat,
            "lon": fire_lon,
            "towers": reports[:3]
        }

        reports = []
        return jsonify(latest_fire)

    return jsonify({"status": "waiting"})

@app.route("/latest")
def latest():
    return jsonify(latest_fire or {})
