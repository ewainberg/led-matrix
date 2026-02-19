from __future__ import annotations

import time
from flask import Flask, jsonify, request, render_template

from state import StateStore
from layout import compute_scroll_plan
from control import Control


def create_app(store: StateStore, ctl: Control) -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/state")
    def api_state():
        st = store.get()
        d = store.as_dict()
        d["_server_time_unix"] = time.time()

        # Attach scroll info per mode snapshot for debugging
        for mode in ("weather", "bus", "excuse", "message"):
            snap = getattr(st, mode, None)
            if snap is None:
                continue
            plan = compute_scroll_plan(snap.display_text or "")
            d[mode]["_scroll"] = {
                "needs_scroll": plan.needs_scroll,
                "text_width_px": plan.text_width_px,
                "cycle_distance_px": plan.cycle_distance_px,
                "cycle_time_s": plan.cycle_time_s,
                "total_time_s": plan.total_time_s,
            }

        return jsonify(d)

    @app.post("/api/power")
    def api_power():
        data = request.get_json(silent=True) or {}
        on = data.get("on")
        if not isinstance(on, bool):
            return jsonify({"ok": False, "error": "Expected JSON: {on: true|false}"}), 400
        store.set_power(on)
        return jsonify({"ok": True, "on": on})

    @app.post("/api/rotation")
    def api_rotation():
        data = request.get_json(silent=True) or {}
        paused = data.get("paused")
        if not isinstance(paused, bool):
            return jsonify({"ok": False, "error": "Expected JSON: {paused: true|false}"}), 400
        store.set_rotation_paused(paused)
        return jsonify({"ok": True, "paused": paused})

    @app.post("/api/mode")
    def api_mode():
        data = request.get_json(silent=True) or {}
        mode = data.get("mode", "")
        if mode not in ("weather", "bus", "excuse", "message", ""):
            return jsonify({"ok": False, "error": "Invalid mode"}), 400
        store.set_mode(mode)
        return jsonify({"ok": True, "mode": mode})
    
    @app.post("/api/refresh")
    def api_refresh():
        ctl.request_refresh()
        return jsonify({"ok": True, "queued": True})

    return app
