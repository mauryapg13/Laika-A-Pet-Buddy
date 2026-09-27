"""Run from the project root:  python -m api.server

Tiny HTTP API so the web app can talk to the device model (JSON only).

    POST /input     body: one input object or a list of them -> output JSON (list if a list was sent)
    GET  /state     current device state
    GET  /summary   daily summary (?day=YYYY-MM-DD)
    GET  /events    full event log (?limit=100)
    GET  /layout    what each button/node does
"""
import threading

from flask import Flask, jsonify, request

from device_model import Hub
from device_model.config import CHOICES, LIMITS, NODES


def create_app(hub: Hub = None) -> Flask:
    hub = hub or Hub()
    lock = threading.Lock()
    app = Flask(__name__)

    @app.after_request
    def cors(resp):  # the web app may run on another port/host
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return resp

    @app.route("/input", methods=["POST", "OPTIONS"])
    def post_input():
        if request.method == "OPTIONS":
            return "", 204
        body = request.get_json(force=True, silent=True)
        if body is None:
            return jsonify({"error": "body must be JSON"}), 400
        with lock:
            if isinstance(body, list):
                return jsonify([hub.handle(m) for m in body])
            return jsonify(hub.handle(body))

    @app.get("/state")
    def state():
        with lock:
            return jsonify(hub.handle({"type": "tick"}))

    @app.get("/summary")
    def summary():
        with lock:
            return jsonify(hub.summary(request.args.get("day")))

    @app.get("/events")
    def events():
        limit = int(request.args.get("limit", 100))
        with lock:
            return jsonify(hub.events[-limit:])

    @app.get("/layout")
    def layout():
        return jsonify({"nodes": NODES, "choices": CHOICES, "limits": LIMITS})

    return app


if __name__ == "__main__":
    print("Laika device model API on http://0.0.0.0:5000  (POST /input, GET /state, /summary, /events, /layout)")
    create_app().run(host="0.0.0.0", port=5000, threaded=True)
