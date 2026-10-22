"""
This is my simple local control page.

There is one button to turn watching on or off, and two tabs, one
for the current status and one for the anomaly log. I built this to
work even without an internet connection, since it only reads from
the file on this computer.
"""

import threading
import time

from flask import Flask, jsonify, render_template, request

import collector
import detector
import storage
import cloud_sender

app = Flask(__name__)
storage.init_db()
if storage.get_state("mode") is None:
    storage.set_state("mode", "stopped")

_detector = detector.Detector()
_loop_thread = None
_loop_running = threading.Event()

POLL_SECONDS = 5
SEND_EVERY_N_LOOPS = 6  # I try to send anything unsent about every 30 seconds


def _monitoring_loop():
    loop_count = 0
    while _loop_running.is_set():
        reading = collector.read_metrics()
        storage.save_reading(reading)

        mode = storage.get_state("mode")
        if mode in ("learning", "watching"):
            anomalies = _detector.process(reading)
            for a in anomalies:
                storage.save_anomaly(
                    metric=a["metric"],
                    value=a["value"],
                    severity=a["severity"],
                )

        loop_count += 1
        if loop_count % SEND_EVERY_N_LOOPS == 0:
            cloud_sender.flush_unsent()

        time.sleep(POLL_SECONDS)


def _start_loop_if_needed():
    if not _loop_running.is_set():
        _loop_running.set()
        thread = threading.Thread(target=_monitoring_loop, daemon=True)
        thread.start()


# if I was already running before this program last closed, I pick
# back up automatically instead of quietly sitting there looking like
# I am watching when I am really not
if storage.get_state("mode") in ("learning", "watching"):
    _start_loop_if_needed()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    mode = storage.get_state("mode", "stopped")
    latest = storage.get_latest_reading()
    reading_count = storage.get_state("reading_count", 0)
    return jsonify({"mode": mode, "latest_reading": latest, "reading_count": reading_count})


@app.route("/api/anomalies")
def api_anomalies():
    return jsonify(storage.get_recent_anomalies())


@app.route("/api/start", methods=["POST"])
def api_start():
    requested_mode = request.json.get("mode", "learning") if request.is_json else "learning"
    storage.set_state("mode", requested_mode)
    _start_loop_if_needed()
    return jsonify({"ok": True, "mode": requested_mode})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    _loop_running.clear()
    storage.set_state("mode", "stopped")
    return jsonify({"ok": True, "mode": "stopped"})


@app.route("/api/set_mode", methods=["POST"])
def api_set_mode():
    new_mode = request.json.get("mode")
    if new_mode not in ("learning", "watching"):
        return jsonify({"ok": False, "error": "mode must be learning or watching"}), 400
    storage.set_state("mode", new_mode)
    return jsonify({"ok": True, "mode": new_mode})


if __name__ == "__main__":
    app.run(debug=False, port=5000)