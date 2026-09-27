"""Run from the project root:  python -m api.server [--camera]

Tiny HTTP API so the web app can talk to the device model (JSON only).

    POST /input     body: one input object or a list of them -> output JSON (list if a list was sent)
    GET  /state     current device state
    GET  /summary   daily summary (?day=YYYY-MM-DD)
    GET  /events    full event log (?limit=100)
    GET  /layout    what each button/node does

With --camera, the same process also runs the camera + live diary around the SAME hub, so the web app,
the camera and the diary all see one device:

    GET  /live            camera behaviour, human present, live diary entries, hub status + notifications
    GET  /camera/stream   MJPEG live view with tracking boxes (use as an <img src>)
    POST /diary/finish    write today's whole-day diary (saved under out/)
    GET  /diary/days      saved diaries by date: {"YYYY-MM-DD": {"text", "folder"}}
Other --camera options are the same as `python -m diary.live` (--source, --name, --track-anything, ...).
"""
import argparse
import threading
import time

from flask import Flask, Response, jsonify, request

from device_model import Hub
from device_model.config import CHOICES, LIMITS, NODES


def create_app(hub: Hub = None, live=None) -> Flask:
    """`live` is a diary.live.App: its hub becomes this API's hub, and inputs go through it so they
    also reach the diary (and outputs get the simulated sensor confirmation)."""
    if live is not None:
        hub, lock = live.hub, live.hub_lock
    else:
        hub, lock = hub or Hub(), threading.Lock()
    app = Flask(__name__)

    @app.after_request
    def cors(resp):  # the web app may run on another port/host
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return resp

    def handle(msg):
        if live is not None:
            return live.send(msg)  # takes the hub lock itself
        with lock:
            return hub.handle(msg)

    @app.route("/input", methods=["POST", "OPTIONS"])
    def post_input():
        if request.method == "OPTIONS":
            return "", 204
        body = request.get_json(force=True, silent=True)
        if body is None:
            return jsonify({"error": "body must be JSON"}), 400
        if isinstance(body, list):
            return jsonify([handle(m) for m in body])
        return jsonify(handle(body))

    @app.get("/state")
    def state():
        return jsonify(handle({"type": "tick"}))

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

    if live is not None:
        from diary.live import saved_diaries

        @app.get("/live")
        def live_state():
            return jsonify(live.state_json())

        @app.get("/camera/stream")
        def camera_stream():
            def frames():
                while True:
                    with live.lock:
                        jpg = live.jpeg
                    if jpg:
                        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
                    time.sleep(0.08)
            return Response(frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

        @app.route("/diary/finish", methods=["POST", "OPTIONS"])
        def diary_finish():
            if request.method == "OPTIONS":
                return "", 204
            folder = live.finish_day()
            return jsonify({"ok": True, "folder": folder.name, "text": live.diary.final})

        @app.get("/diary/days")
        def diary_days():
            return jsonify(saved_diaries(live.args.out))

    return app


def main():
    ap = argparse.ArgumentParser(prog="python -m api.server", add_help=False)
    ap.add_argument("--camera", action="store_true", help="also run the camera + live diary on the same hub")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--api-port", type=int, default=5050)  # not 5000: macOS AirPlay Receiver holds it
    known, rest = ap.parse_known_args()
    if not known.camera:
        if rest:
            ap.error(f"unrecognized arguments: {' '.join(rest)} (camera options need --camera)")
        print("Laika device model API on http://0.0.0.0:5050  (POST /input, GET /state, /summary, /events, /layout)")
        create_app().run(host=known.host, port=known.api_port, threaded=True)
        return

    from diary.env import load_dotenv
    from diary.live import App, build_parser
    live_args = build_parser("python -m api.server --camera").parse_args(rest)
    load_dotenv()
    live = App(live_args)
    threading.Thread(target=live.capture_loop, daemon=True).start()
    print(f"Laika API + camera + diary on http://{known.host}:{known.api_port}  "
          f"(detector {'on' if live.detector else 'off'}, Claude {'on' if live.diary.use_claude else 'off'})")
    print("  hub:    POST /input · GET /state /summary /events /layout")
    print("  camera: GET /live · GET /camera/stream · POST /diary/finish · GET /diary/days")
    create_app(live=live).run(host=known.host, port=known.api_port, threaded=True)


if __name__ == "__main__":
    main()
