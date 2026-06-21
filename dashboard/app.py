"""
app.py
======
Flask dashboard for the PLC-ROS2 industrial cell.

Serves live cell status at http://localhost:5000

The ROS 2 supervisor pushes state updates via POST /api/update.
The browser polls GET /api/state every 2 seconds (auto-refresh).

USAGE:
  python app.py
  # or via Docker: docker compose up
"""

from flask import Flask, jsonify, render_template, request
import threading

app  = Flask(__name__)
lock = threading.Lock()

# ── Shared state — updated by ROS 2 nodes via /api/update ────────────────────
cell_state = {
    "belt_running":   False,
    "part_detected":  False,
    "gripper_active": False,
    "fault_latch":    False,
    "cycle_count":    0,
    "sensor_analog":  0,
}

supervisor_state = {
    "supervisor_state":  "TRAINING",
    "training_progress": 0,
    "training_target":   200,
    "consec_anomalies":  0,
    "total_processed":   0,
    "cell_fault":        False,
}
# ─────────────────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    """Serve the main dashboard HTML page."""
    return render_template("index.html")


@app.route("/api/state")
def get_state():
    """Return current cell and supervisor state as JSON."""
    with lock:
        return jsonify({
            "cell":       cell_state,
            "supervisor": supervisor_state,
        })


@app.route("/api/update", methods=["POST"])
def update_state():
    """Receive state push from ROS 2 nodes and store it."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "no JSON"}), 400
    with lock:
        if "cell"       in data:
            cell_state.update(data["cell"])
        if "supervisor" in data:
            supervisor_state.update(data["supervisor"])
    return jsonify({"ok": True})


if __name__ == "__main__":
    # debug=False for Docker; use debug=True for local development
    app.run(host="0.0.0.0", port=5000, debug=False)
