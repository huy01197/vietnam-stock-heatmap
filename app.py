# region 1. Imports & Initialization
import os
import sys
import time
import signal
import subprocess
import json
import asyncio
import webbrowser
from pathlib import Path
from aiohttp import web

from stream_hub import (
    stream_hub,
    market_store,
    get_snapshot_data,
    get_market_summary,
    get_indices_data
)
from market_service import (
    get_unique_sectors
)

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "bauhaus-ui.html"
ASSETS_DIR = BASE_DIR / "assets"
# endregion 1

# region 2. CORS Middleware & Security Headers
@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        response = web.Response(status=200)
    else:
        try:
            response = await handler(request)
        except web.HTTPException as ex:
            response = ex
        except Exception as e:
            response = web.json_response({"error": str(e)}, status=500)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept"
    return response
# endregion 2

# region 3. Web Server Setup & REST Endpoints
async def handle_index(request):
    if HTML_FILE.exists():
        return web.FileResponse(HTML_FILE)
    return web.Response(text="Bản đồ thị trường UI not found", status=404)

async def handle_api_heatmap(request):
    market = request.query.get("market", "ALL")
    sector = request.query.get("sector", "ALL")
    data = get_snapshot_data(market=market, sector=sector)
    return web.json_response(data)

async def handle_api_summary(request):
    summary = get_market_summary()
    return web.json_response(summary)

async def handle_api_indices(request):
    indices = get_indices_data()
    return web.json_response(indices)

async def handle_api_sectors(request):
    market = request.query.get("market", "ALL")
    sectors = get_unique_sectors(selected_market=market)
    return web.json_response(sectors)
# endregion 3

# region 4. WebSocket Real-time Endpoint
async def handle_websocket(request):
    ws = web.WebSocketResponse(heartbeat=20.0)
    await ws.prepare(request)

    stream_hub.add_client(ws)
    print(f"[WebSocket] Client đã kết nối (Tổng clients: {len(stream_hub.active_connections)})")

    try:
        snapshot_stocks = market_store.get_all_stocks()
        summary = market_store.get_summary()
        initial_msg = {
            "type": "SNAPSHOT",
            "data": snapshot_stocks,
            "summary": summary,
            "indices": market_store.get_indices()
        }
        await ws.send_str(json.dumps(initial_msg))

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    payload = json.loads(msg.data)
                    cmd = payload.get("cmd")
                    if cmd == "PING":
                        await ws.send_str(json.dumps({"type": "PONG"}))
                    elif cmd == "GET_SNAPSHOT":
                        m = payload.get("market", "ALL")
                        s = payload.get("sector", "ALL")
                        filtered = get_snapshot_data(m, s)
                        await ws.send_str(json.dumps({
                            "type": "SNAPSHOT",
                            "data": filtered,
                            "summary": market_store.get_summary(),
                            "indices": market_store.get_indices()
                        }))
                except Exception:
                    pass
            elif msg.type == web.WSMsgType.ERROR:
                print(f"[WebSocket] Lỗi kết nối: {ws.exception()}")
    finally:
        stream_hub.remove_client(ws)
        print(f"[WebSocket] Client ngắt kết nối (Còn lại: {len(stream_hub.active_connections)})")

    return ws
# endregion 4

# region 5. Lifecycle & Stream Hub Bootstrapper
async def on_startup(app):
    loop = asyncio.get_running_loop()
    stream_hub.set_loop(loop)
    stream_hub.start()
    print("[App] Bản đồ thị trường Stream Hub đã khởi động thành công.")

async def on_cleanup(app):
    for ws in list(stream_hub.active_connections):
        await ws.close(code=web.WSCloseCode.GOING_AWAY, message='Server shutdown')
    stream_hub.active_connections.clear()

def create_app():
    app = web.Application(middlewares=[cors_middleware])

    app.router.add_get("/", handle_index)
    app.router.add_get("/index.html", handle_index)
    app.router.add_get("/ws", handle_websocket)
    
    app.router.add_get("/api/heatmap", handle_api_heatmap)
    app.router.add_get("/api/summary", handle_api_summary)
    app.router.add_get("/api/indices", handle_api_indices)
    app.router.add_get("/api/sectors", handle_api_sectors)

    if ASSETS_DIR.exists():
        app.router.add_static("/assets/", path=str(ASSETS_DIR), name="assets")

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app
# endregion 5

# region 6. Main Execution & Auto-Browser
def kill_existing_instance(port: int = 8050):
    """
    Tự động quét và đóng tiến trình cũ đang chiếm cổng 8050 (nếu có),
    giúp người dùng bấm nút 'Play' trong VS Code / IDE là web app lập tức restart mượt mà.
    """
    current_pid = os.getpid()
    try:
        if sys.platform == "win32":
            res = subprocess.run(f"netstat -ano | findstr :{port}", shell=True, capture_output=True, text=True)
            for line in res.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and "LISTENING" in parts:
                    try:
                        pid = int(parts[-1])
                        if pid != current_pid and pid > 0:
                            subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                            print(f"[Auto-Restart] Đã tắt tiến trình cũ (PID: {pid}) đang chiếm cổng {port}.")
                            time.sleep(0.5)
                    except Exception:
                        pass
        else:
            # macOS / Linux
            res = subprocess.run(f"lsof -ti :{port}", shell=True, capture_output=True, text=True)
            pids = [int(p.strip()) for p in res.stdout.split() if p.strip().isdigit()]
            killed = False
            for pid in pids:
                if pid != current_pid:
                    try:
                        os.kill(pid, signal.SIGKILL)
                        print(f"[Auto-Restart] Đã đóng tiến trình cũ (PID: {pid}) để giải phóng cổng {port}.")
                        killed = True
                    except ProcessLookupError:
                        pass
                    except Exception as e:
                        print(f"[Auto-Restart Warning] Không thể tắt PID {pid}: {e}")
            if killed:
                time.sleep(0.6)
    except Exception as e:
        print(f"[Auto-Restart Warning] Kiểm tra cổng {port} thất bại: {e}")

def open_browser():
    try:
        webbrowser.open_new("http://127.0.0.1:8050/")
    except Exception:
        pass

def fast_exit_signal_handler(sig, frame):
    print("\n[App] Đã nhận tín hiệu dừng (Ctrl+C). Đóng toàn bộ tiến trình ngay lập tức...")
    os._exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, fast_exit_signal_handler)
    signal.signal(signal.SIGTERM, fast_exit_signal_handler)

    kill_existing_instance(8050)
    app = create_app()
    import threading
    threading.Timer(1.2, open_browser).start()
    print("[App] Khởi chạy Bản đồ thị trường tại http://127.0.0.1:8050")
    try:
        web.run_app(app, host='127.0.0.1', port=8050)
    except (KeyboardInterrupt, SystemExit):
        os._exit(0)
# endregion 6