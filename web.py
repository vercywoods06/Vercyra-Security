import asyncio
import html
import os

from aiohttp import web

import db


async def api(request):
    data = await asyncio.to_thread(lambda: {"stats": db.stats(), "rounds": db.recent(100)})
    return web.json_response(data)


async def index(request):
    s, rows = await asyncio.to_thread(lambda: (db.stats(), db.recent(50)))
    if s["count"]:
        cards = "".join(f'<div class="c"><b>{html.escape(str(v))}</b><span>{k.replace("_", " ")}</span></div>' for k, v in s.items())
    else:
        cards = "<p>No rounds logged yet. Send <code>/add 2.35</code> to the bot.</p>"
    body = "".join(
        f"<tr><td>{r['id']}</td><td>{r['multiplier']:.2f}x</td><td>{html.escape(r['added_by'] or '')}</td><td>{html.escape(r['created_at'])}</td></tr>"
        for r in rows)
    page = f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<meta http-equiv=refresh content=15><title>Vercyra Round Tracker</title>
<style>body{{font:16px system-ui;background:#0f1420;color:#e8ecf4;max-width:760px;margin:2rem auto;padding:0 1rem}}
.g{{display:flex;flex-wrap:wrap;gap:.75rem}}.c{{background:#1a2133;border-radius:10px;padding:.8rem 1rem;min-width:120px}}
.c b{{display:block;font-size:1.5rem}}.c span{{color:#8c97b0;font-size:.8rem;text-transform:capitalize}}
table{{width:100%;border-collapse:collapse;margin-top:1.5rem}}td,th{{padding:.4rem .6rem;text-align:left;border-bottom:1px solid #263049}}
small{{color:#8c97b0}}</style>
<h1>Vercyra Round Tracker</h1><div class=g>{cards}</div>
<table><tr><th>#</th><th>Multiplier</th><th>By</th><th>Time (UTC)</th></tr>{body}</table>
<p><small>Manually logged results. Past rounds do not predict future ones.</small></p>"""
    return web.Response(text=page, content_type="text/html")


def make_app():
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/api/rounds", api)
    return app


async def start_web():
    runner = web.AppRunner(make_app())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080))).start()
    return runner
