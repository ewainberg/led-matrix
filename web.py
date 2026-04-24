from __future__ import annotations

import time
import io
from flask import Flask, jsonify, Response, request, send_file, render_template

from state import StateStore
from layout import compute_scroll_plan
from control import Control
from matrix.tetris import TetrisGame


def create_app(store: StateStore, ctl: Control, preview_png_provider=None) -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/state")
    def api_state():
        st = store.get()
        d = store.as_dict()
        d["_server_time_unix"] = time.time()

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

        d["bread_alert"] = bool(getattr(st, "bread_alert", False))
        d["snake_alert"] = bool(getattr(st, "snake_alert", False))

        return jsonify(d)

    @app.post("/api/power")
    def api_power():
        data = request.get_json(silent=True) or {}
        on = data.get("on")
        if not isinstance(on, bool):
            return jsonify({"ok": False, "error": "Expected JSON: {on: true|false}"}), 400
        store.update(power_on=on)
        return jsonify({"ok": True, "on": on})

    @app.post("/api/rotation")
    def api_rotation():
        data = request.get_json(silent=True) or {}
        paused = data.get("paused")
        if not isinstance(paused, bool):
            return jsonify({"ok": False, "error": "Expected JSON: {paused: true|false}"}), 400
        store.update(rotation_paused=paused)
        return jsonify({"ok": True, "paused": paused})

    @app.post("/api/mode")
    def api_mode():
        data = request.get_json(silent=True) or {}
        mode = data.get("mode", "")
        if mode not in ("weather", "bus", "excuse", "message", ""):
            return jsonify({"ok": False, "error": "Invalid mode"}), 400
        store.update(forced_mode=mode)
        return jsonify({"ok": True, "mode": mode})

    @app.post("/api/bread_alert")
    def api_bread_alert():
        data = request.get_json(silent=True) or {}
        on = data.get("on")
        if not isinstance(on, bool):
            return jsonify({"ok": False, "error": "Expected JSON: {on: true|false}"}), 400

        store.update(bread_alert=on, bread_alert_changed_at=time.time())
        return jsonify({"ok": True, "bread_alert": on})
    
    @app.post("/api/snake_alert")
    def api_snake_alert():
        data = request.get_json(silent=True) or {}
        on = data.get("on")
        if not isinstance(on, bool):
            return jsonify({"ok": False, "error": "Expected JSON: {on: true|false}"}), 400

        store.update(snake_alert=on, snake_alert_changed_at=time.time())
        return jsonify({"ok": True, "snake_alert": on})

    @app.post("/api/refresh")
    def api_refresh():
        ctl.request_refresh()
        return jsonify({"ok": True, "queued": True})

    @app.get("/preview.png")
    def preview_png():
        if not preview_png_provider:
            return Response("preview not available", status=404)
        data = preview_png_provider() or b""
        return send_file(io.BytesIO(data), mimetype="image/png")

    @app.post("/api/engine/demo")
    def api_engine_demo():
        data = request.get_json(silent=True) or {}
        on = data.get("on")
        if not isinstance(on, bool):
            return jsonify({"ok": False, "error": "Expected JSON: {on:true|false}"}), 400
        store.update(engine_demo=on)
        return jsonify({"ok": True, "engine_demo": on})

    @app.post("/api/engine/demo/next")
    def api_engine_demo_next():
        st = store.get()
        cur = int(getattr(st, "engine_demo_idx", 0))
        store.update(engine_demo_idx=cur + 1)
        return jsonify({"ok": True, "engine_demo_idx": cur + 1})

    # ------------------------------------------------------------------
    # Tetris endpoints
    # ------------------------------------------------------------------

    @app.post("/api/tetris/start")
    def api_tetris_start():
        game = TetrisGame()
        store.update(tetris_game=game)
        return jsonify({"ok": True, "status": "started"})

    @app.post("/api/tetris/stop")
    def api_tetris_stop():
        store.update(tetris_game=None)
        return jsonify({"ok": True, "status": "stopped"})

    @app.post("/api/tetris/action")
    def api_tetris_action():
        data = request.get_json(silent=True) or {}
        player = data.get("player")
        action = data.get("action", "")
        if player not in (1, 2):
            return jsonify({"ok": False, "error": "player must be 1 or 2"}), 400
        valid_actions = ("up", "down", "rotate_cw", "rotate_ccw")
        if action not in valid_actions:
            return jsonify({"ok": False, "error": f"action must be one of {valid_actions}"}), 400
        game = getattr(store.get(), "tetris_game", None)
        if game is None:
            return jsonify({"ok": False, "error": "no active tetris game"}), 409
        game.action(player, action)
        return jsonify({"ok": True, "player": player, "action": action})

    @app.get("/api/tetris/state")
    def api_tetris_state():
        game = getattr(store.get(), "tetris_game", None)
        if game is None:
            return jsonify({"active": False})
        snap = game.snapshot()
        return jsonify({
            "active": True,
            "p1": {
                "score": snap["board1_score"],
                "lines": snap["board1_lines"],
                "game_over": snap["board1_over"],
            },
            "p2": {
                "score": snap["board2_score"],
                "lines": snap["board2_lines"],
                "game_over": snap["board2_over"],
            },
            "tick_interval": snap["tick_interval"],
        })

    return app