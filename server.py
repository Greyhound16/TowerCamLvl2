from flask import Flask, request, jsonify
from flask_cors import CORS
import math
import time

app = Flask(__name__)
CORS(app)

reports = {}

@app.route("/report", methods=["POST"])
def report():
    data = request.json
    tower_id = data.get("tower_id")

    reports[tower_id] = {
        "lat": data["lat"],
        "lon": data["lon"],
        "bearing": data["bearing"],
        "time": time.time()
    }

    return jsonify({"status": "ok", "stored": tower_id})

@app.route("/reports")
def get_reports():
    return jsonify(reports)

@app.route("/clear", methods=["POST"])
def clear():
    reports.clear()
    return jsonify({"status": "cleared"})

def intersect(p1, b1, p2, b2):
    # Convert bearings to radians
    b1 = math.radians(b1)
    b2 = math.radians(b2)

    x1, y1 = p1
    x2, y2 = p2

    dx1, dy1 = math.sin(b1), math.cos(b1)
    dx2, dy2 = math.sin(b2), math.cos(b2)

    det = dx1 * dy2 - dy1 * dx2
    if abs(det) < 1e-6:
        return None

    t = ((x2 - x1) * dy2 - (y2 - y1) * dx2) / det
    return x1 + t * dx1, y1 + t * dy1

@app.route("/triangulate")
def triangulate():
    if len(reports) < 3:
        return jsonify({"error": "need 3 towers"}), 400

    keys = list(reports.keys())
    p1 = (reports[keys[0]]["lon"], reports[keys[0]]["lat"])
    p2 = (reports[keys[1]]["lon"], reports[keys[1]]["lat"])
    p3 = (reports[keys[2]]["lon"], reports[keys[2]]["lat"])

    i1 = intersect(p1, reports[keys[0]]["bearing"],
                   p2, reports[keys[1]]["bearing"])
    i2 = intersect(p1, reports[keys[0]]["bearing"],
                   p3, reports[keys[2]]["bearing"])

    if not i1 or not i2:
        return jsonify({"error": "no intersection"}), 400

    lat = (i1[1] + i2[1]) / 2
    lon = (i1[0] + i2[0]) / 2

    return jsonify({"lat": lat, "lon": lon})

if __name__ == "__main__":
    app.run()
