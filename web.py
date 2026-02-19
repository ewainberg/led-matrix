from __future__ import annotations

import time
from flask import Flask, jsonify, Response

from state import StateStore
from layout import compute_scroll_plan


def create_app(store: StateStore) -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index() -> Response:
        html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>LED Matrix Debug</title>
  <style>
    body { font-family: system-ui, -apple-system, Arial, sans-serif; margin: 16px; }
    .meta { margin-bottom: 14px; }
    .row { display: grid; grid-template-columns: 140px 1fr; gap: 10px; padding: 10px 0; border-bottom: 1px solid #ddd; }
    .k { font-weight: 600; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }
    .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; background: #eee; margin-left: 6px; }
  </style>
</head>
<body>
  <h2>LED Matrix Debug</h2>
  <div id="meta" class="meta mono"></div>
  <div id="grid"></div>

<script>
function esc(s) {
  return (s ?? '').toString()
    .replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
}

async function refresh() {
  const r = await fetch('/api/state');
  const s = await r.json();

  document.getElementById('meta').textContent =
    'mode=' + s.current_mode +
    ' | mode_duration=' + s.current_mode_duration_s + 's' +
    ' | clock=' + s.time_text +
    ' | updated=' + new Date(s._server_time_unix*1000).toLocaleTimeString();

  const modes = [
    ['weather', s.weather],
    ['bus', s.bus],
    ['excuse', s.excuse],
    ['message', s.message],
  ];

  const grid = document.getElementById('grid');
  grid.innerHTML = '';

  for (const [name, snap] of modes) {
    const div = document.createElement('div');
    div.className = 'row';

    const extra = snap._scroll
      ? `<div class="mono">fit=${snap._scroll.needs_scroll ? 'scroll' : 'fits'} | text_px=${snap._scroll.text_width_px} | cycle_s=${snap._scroll.cycle_time_s.toFixed(2)} | total_s=${snap._scroll.total_time_s.toFixed(2)}</div>`
      : '';

    div.innerHTML = `
      <div class="k">${name}<span class="pill">${snap.ok ? 'ok' : 'err'}</span></div>
      <div>
        <div>${snap.display_text ? esc(snap.display_text) : '<span class="mono">(empty)</span>'}</div>
        <div class="mono">fetched_at=${new Date(snap.fetched_at_unix*1000).toLocaleTimeString()}</div>
        ${snap.error ? `<div class="mono">error=${esc(snap.error)}</div>` : ''}
        ${extra}
      </div>
    `;
    grid.appendChild(div);
  }
}

refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>
"""
        return Response(html, mimetype="text/html")

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

    return app
