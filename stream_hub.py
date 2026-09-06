# region 1. Imports & Configuration
import os
import json
import time
import asyncio
import threading
from pathlib import Path
import urllib3

from market_service import (
    load_ssi_config,
    get_ssi_token,
    get_ssi_client,
    get_market_service_instance,
    get_indices_summary,
    is_trading_hours,
    SSIConfigWrapper
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).resolve().parent
SSI_CONFIG = load_ssi_config()
# endregion 1

# region 2. Real-time In-memory Store & State Management
class MarketStateStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._stocks = {}
        self._indices = get_indices_summary()
        self._sectors_map = {}
        try:
            from market_service import get_market_service_instance
            self._sectors_map = get_market_service_instance().get_dynamic_sectors()
        except Exception:
            pass
        self._last_update_ts = 0

    def set_sectors(self, sectors: dict):
        with self._lock:
            self._sectors_map = sectors.copy()

    def get_sector(self, sym: str) -> str:
        with self._lock:
            sec = self._sectors_map.get(sym)
            if not sec:
                try:
                    from market_service import get_market_service_instance
                    self._sectors_map = get_market_service_instance().get_dynamic_sectors()
                    sec = self._sectors_map.get(sym, "Khác")
                except Exception:
                    sec = "Khác"
            return sec or "Khác"

    def initialize_from_snapshot(self, records: list, indices: dict = None):
        with self._lock:
            for item in records:
                sym = item.get("symbol")
                if sym:
                    self._stocks[sym] = item.copy()
            if indices:
                self._indices.update(indices)
            self._last_update_ts = time.time()

    def update_indices_bulk(self, indices_dict: dict):
        with self._lock:
            for k, v in indices_dict.items():
                if isinstance(v, dict) and v.get("index_value", 0) > 0:
                    self._indices[k] = v.copy()
            self._last_update_ts = time.time()

    def update_index(self, index_id: str, data: dict):
        with self._lock:
            key = str(index_id).upper()
            if "VNINDEX" in key or "VN-INDEX" in key or key == "10":
                target_key = "VNINDEX"
            elif "VN30" in key or key == "11":
                target_key = "VN30"
            elif "HNX30" in key:
                target_key = "HNX30"
            elif ("HNXINDEX" in key or "HNX-INDEX" in key or key == "02") and "UPCOM" not in key:
                target_key = "HNXINDEX"
            elif "UPCOM" in key or "HNXUPCOM" in key or key == "03":
                target_key = "HNXUPCOMINI"
            else:
                target_key = index_id

            val = float(data.get("IndexValue") or data.get("index_value") or data.get("Index") or data.get("PriorVal") or 0)
            chg = float(data.get("Change") or data.get("change") or 0)
            r_chg = float(data.get("RatioChange") or data.get("ratio_change") or data.get("change_pct") or 0)
            
            raw_val = float(data.get("TotalValues") or data.get("TotalValue") or data.get("total_value") or data.get("TotalVal") or 0)
            t_val = raw_val / 1_000_000_000.0 if raw_val > 100_000_000 else raw_val
            
            raw_vol = float(data.get("TotalShares") or data.get("TotalQtty") or data.get("total_vol") or data.get("TotalVol") or 0)
            t_vol = raw_vol / 1_000_000.0 if raw_vol > 10_000 else raw_vol

            if val > 0:
                self._indices[target_key] = {
                    "index_id": "VN-INDEX" if target_key == "VNINDEX" else ("HNX-INDEX" if target_key == "HNXINDEX" else ("UPCOM-INDEX" if target_key == "HNXUPCOMINI" else target_key)),
                    "index_value": round(val, 2),
                    "change": round(chg, 2),
                    "ratio_change": round(r_chg, 2),
                    "total_value": round(t_val, 2),
                    "total_vol": round(t_vol, 2),
                    "advances": int(data.get("Advances") or data.get("advances") or 0),
                    "declines": int(data.get("Declines") or data.get("declines") or 0),
                    "nochanges": int(data.get("NoChanges") or data.get("nochanges") or 0),
                    "ceilings": int(data.get("CeilingStocks") or data.get("Ceilings") or data.get("ceilings") or 0),
                    "floors": int(data.get("FloorStocks") or data.get("Floors") or data.get("floors") or 0)
                }

    def update_stock(self, sym: str, tick_data: dict) -> dict:
        with self._lock:
            existing = self._stocks.get(sym, {})
            sec_name = tick_data.get("sector") or existing.get("sector") or self.get_sector(sym)

            new_p = float(tick_data.get("matched_price") or 0)
            if new_p > 1000: new_p /= 1000.0
            matched_price = new_p if new_p > 0 else float(existing.get("matched_price", 0))

            new_ref = float(tick_data.get("ref_price") or 0)
            if new_ref > 1000: new_ref /= 1000.0
            ref_price = new_ref if new_ref > 0 else float(existing.get("ref_price", 0))
            if ref_price <= 0 and matched_price > 0:
                ref_price = matched_price

            if matched_price <= 0 and ref_price <= 0:
                return {}

            # Ưu tiên lấy % biến động chính thức từ sàn nếu có
            official_pct = tick_data.get("change_pct")
            official_pts = tick_data.get("change_pts")
            if official_pct is not None:
                change_pct = float(official_pct)
                change_pts = float(official_pts) if official_pts is not None else (matched_price - ref_price)
            elif ref_price > 0 and matched_price > 0:
                change_pct = ((matched_price - ref_price) / ref_price) * 100.0
                change_pts = matched_price - ref_price
            else:
                change_pct = existing.get("change_pct", 0.0)
                change_pts = existing.get("change_pts", 0.0)

            # Xử lý Giá trị giao dịch (tỷ đồng) & Khối lượng giao dịch (triệu CP)
            tot_val = float(tick_data.get("total_val", 0))
            mat_val = float(tick_data.get("match_val", 0))
            tot_vol = float(tick_data.get("total_vol", 0))
            mat_vol = float(tick_data.get("match_vol", 0))

            # Giá trị giao dịch lũy kế (tỷ đồng) - SSI luôn gửi TotalVal bằng VND
            if tot_val > 0:
                traded_val = tot_val / 1_000_000_000.0 if tot_val > 100_000 else tot_val
            elif mat_val > 0:
                traded_val = existing.get("traded_value", 0) + (mat_val / 1_000_000_000.0)
            elif mat_vol > 0 and matched_price > 0:
                calc_val = (mat_vol * matched_price * 1000.0) / 1_000_000_000.0
                traded_val = existing.get("traded_value", 0) + calc_val
            else:
                traded_val = existing.get("traded_value", 0)

            # Khối lượng giao dịch lũy kế (triệu CP)
            if tot_vol > 0:
                traded_vol_mil = tot_vol / 1_000_000.0
            elif mat_vol > 0:
                traded_vol_mil = existing.get("traded_vol_mil", 0) + (mat_vol / 1_000_000.0)
            else:
                traded_vol_mil = existing.get("traded_vol_mil", 0)

            # Bảo lưu mọi cổ phiếu hợp lệ đã nạp hoặc có phát sinh thanh khoản > 0.01 tỷ
            if traded_val <= 0.01 and existing.get("traded_value", 0) <= 0.01:
                return {}

            record = {
                "market_root": "Thị trường",
                "market": tick_data.get("market") or existing.get("market", "HOSE"),
                "sector": sec_name,
                "symbol": sym,
                "company_name": sym,
                "ref_price": round(ref_price, 2),
                "matched_price": round(matched_price, 2),
                "change_pts": round(change_pts, 2),
                "change_pct": round(change_pct, 2),
                "traded_value": round(traded_val, 3),
                "traded_vol_mil": round(traded_vol_mil, 3),
                "color_metric": change_pct,
                "timestamp": time.strftime("%H:%M:%S"),
                "price_str": f"{matched_price:,.2f}",
                "change_str": f"{change_pct:+.2f}%",
                "traded_val_str": f"{traded_val:,.2f} tỷ" if traded_val >= 1.0 else f"{traded_val*1000:,.0f} tr"
            }
            self._stocks[sym] = record
            self._last_update_ts = time.time()
            return record

    def get_all_stocks(self) -> list:
        with self._lock:
            return [s for s in self._stocks.values() if s.get("traded_value", 0) > 0.01]

    def get_indices(self) -> dict:
        with self._lock:
            return self._indices.copy()

    def get_summary(self) -> dict:
        stocks = self.get_all_stocks()
        vn_idx = self._indices.get("VNINDEX", {})
        
        # Nếu đã có chỉ số tổng hợp từ SSI, dùng trực tiếp số chuẩn SSI
        if vn_idx and float(vn_idx.get("total_value", 0)) > 0:
            total_val = float(vn_idx.get("total_value", 0))
            total_vol = float(vn_idx.get("total_vol", 0))
            up_count = int(vn_idx.get("advances", 0))
            down_count = int(vn_idx.get("declines", 0))
            ref_count = int(vn_idx.get("nochanges", 0))
            ceil_count = int(vn_idx.get("ceilings", 0))
            floor_count = int(vn_idx.get("floors", 0))
        else:
            total_val = sum(s.get("traded_value", 0) for s in stocks)
            total_vol = sum(s.get("traded_vol_mil", 0) for s in stocks)
            up_count = sum(1 for s in stocks if s.get("change_pct", 0) > 0)
            down_count = sum(1 for s in stocks if s.get("change_pct", 0) < 0)
            ref_count = len(stocks) - up_count - down_count
            ceil_count = sum(1 for s in stocks if s.get("change_pct", 0) >= 6.8)
            floor_count = sum(1 for s in stocks if s.get("change_pct", 0) <= -6.8)

        return {
            "total_traded_val": round(total_val, 2),
            "total_traded_vol": round(total_vol, 2),
            "total_stocks_count": len(stocks),
            "up": up_count,
            "down": down_count,
            "ref": ref_count,
            "ceil": ceil_count,
            "floor": floor_count,
            "indices": self.get_indices()
        }

market_store = MarketStateStore()
# endregion 2

# region 3. FastConnect WebSocket Stream Connector
class StreamHub:
    def __init__(self):
        self.active_connections = set()
        self._connections_lock = threading.Lock()
        self._running = False
        self._stream_connected = False
        self._stream_client = None
        self._loop = None

    def set_loop(self, loop):
        self._loop = loop

    def add_client(self, ws):
        with self._connections_lock:
            self.active_connections.add(ws)

    def remove_client(self, ws):
        with self._connections_lock:
            self.active_connections.discard(ws)

    def broadcast_sync(self, message: dict):
        if not self.active_connections:
            return
        payload = json.dumps(message)
        with self._connections_lock:
            dead_clients = []
            for ws in list(self.active_connections):
                try:
                    if self._loop and self._loop.is_running():
                        asyncio.run_coroutine_threadsafe(ws.send_str(payload), self._loop)
                except Exception:
                    dead_clients.append(ws)
            for ws in dead_clients:
                self.active_connections.discard(ws)

    def on_ssi_message(self, message):
        try:
            payload = json.loads(message) if isinstance(message, str) else message
            datatype = payload.get("DataType") or payload.get("Datatype")
            content = json.loads(payload.get("Content", "{}")) if isinstance(payload.get("Content"), str) else payload.get("Content", {})
            if not content:
                return

            if datatype == "MI":
                index_id = content.get("IndexId") or content.get("IndexName") or ""
                if index_id:
                    market_store.update_index(index_id, content)
                    self.broadcast_sync({
                        "type": "INDEX_UPDATE",
                        "data": market_store.get_indices()
                    })
                return

            if datatype in ["X", "X-TRADE"]:
                sym = str(content.get("Symbol", "")).strip().upper()
                if len(sym) != 3 or not sym.isalpha():
                    return
                
                price = float(content.get("MatchPrice") or content.get("Price") or content.get("LastPrice") or content.get("Close") or 0)
                if price <= 0:
                    return

                tot_vol = float(content.get("TotalVol") or content.get("TotalVolume") or 0)
                mat_vol = float(content.get("MatchVol") or content.get("Vol") or content.get("MatchVolume") or content.get("Volume") or 0)
                tot_val = float(content.get("TotalVal") or content.get("TotalValue") or 0)
                mat_val = float(content.get("MatchVal") or content.get("MatchValue") or 0)
                ref = float(content.get("RefPrice") or content.get("BasicPrice") or content.get("PriorVal") or 0)
                chg = float(content.get("Change")) if content.get("Change") is not None else None
                r_chg = float(content.get("RatioChange")) if content.get("RatioChange") is not None else None
                market = content.get("MarketId") or content.get("Exchange") or "HOSE"

                tick_data = {
                    "matched_price": price,
                    "ref_price": ref,
                    "total_vol": tot_vol,
                    "match_vol": mat_vol,
                    "total_val": tot_val,
                    "match_val": mat_val,
                    "change_pts": chg,
                    "change_pct": r_chg,
                    "market": market
                }

                updated_stock = market_store.update_stock(sym, tick_data)
                if updated_stock:
                    # Ngừng in thông báo tick ra terminal theo yêu cầu người dùng
                    self.broadcast_sync({
                        "type": "TICK",
                        "data": updated_stock
                    })
        except Exception as e:
            pass

    def sync_live_snapshot(self):
        svc = get_market_service_instance()
        sectors = svc.get_dynamic_sectors()
        market_store.set_sectors(sectors)
        
        indices = svc.get_ssi_indices()
        df = svc.generate_heatmap_dataset()
        if not df.empty:
            records = df.to_dict(orient="records")
            market_store.initialize_from_snapshot(records, indices)
            print(f"[StreamHub] Đã nạp {len(records)} mã cổ phiếu từ SSI.")
            self.broadcast_sync({
                "type": "SNAPSHOT",
                "data": market_store.get_all_stocks(),
                "summary": market_store.get_summary(),
                "indices": market_store.get_indices()
            })
            return True
        return False

    def _stream_worker(self):
        # 1. Nạp Snapshot ban đầu đúng một lần khi khởi động
        self.sync_live_snapshot()

        while self._running:
            try:
                # 2. Phân định thời gian giao dịch thực tế
                in_trade = is_trading_hours()

                if in_trade:
                    # TRONG GIỜ GIAO DỊCH: Bám sát Realtime, duy trì duy nhất 1 kết nối SignalR ổn định
                    if not self._stream_connected:
                        token = get_ssi_token()
                        if token:
                            try:
                                from ssi_fc_data.fc_md_stream import MarketDataStream

                                client = get_ssi_client()
                                cfg = SSIConfigWrapper()

                                def on_open_handler():
                                    print("[StreamHub] ✅ Kết nối SSI FastConnect DataHub thành công (X:ALL,MI:ALL)!")
                                    self._stream_connected = True
                                    try:
                                        self._stream_client.swith_channel("X:ALL,MI:ALL")
                                    except Exception:
                                        pass

                                def on_close_handler():
                                    self._stream_connected = False

                                def on_err_handler(err):
                                    self._stream_connected = False

                                self._stream_client = MarketDataStream(cfg, client, on_close=on_close_handler, on_open=on_open_handler)
                                self._stream_client.start(
                                    _on_message=self.on_ssi_message,
                                    _on_error=on_err_handler,
                                    _selected_channel="X:ALL,MI:ALL"
                                )
                            except Exception as sig_err:
                                self._stream_connected = False

                    # Cập nhật định kỳ chỉ số qua API (mỗi 10s một lần) để VN-Index luôn chính xác 100% như sàn lớn
                    now = time.time()
                    if now - getattr(self, '_last_index_poll_ts', 0) >= 10.0:
                        self._last_index_poll_ts = now
                        try:
                            svc = get_market_service_instance()
                            live_idx = svc.get_ssi_indices()
                            if live_idx:
                                market_store.update_indices_bulk(live_idx)
                                self.broadcast_sync({
                                    "type": "INDEX_UPDATE",
                                    "data": market_store.get_indices()
                                })
                        except Exception:
                            pass
                else:
                    # NGOÀI GIỜ GIAO DỊCH: Tĩnh 5 phút rồi cập nhật chốt phiên
                    time.sleep(300)
                    self.sync_live_snapshot()

            except Exception:
                pass

            time.sleep(3)

    def start(self):
        if not self._running:
            self._running = True
            thread = threading.Thread(target=self._stream_worker, daemon=True)
            thread.start()

stream_hub = StreamHub()
# endregion 3

# region 4. Stream Message Parser & Data Validation Pipeline
def get_snapshot_data(market="ALL", sector="ALL") -> list:
    all_stocks = market_store.get_all_stocks()
    if not all_stocks:
        svc = get_market_service_instance()
        df = svc.generate_heatmap_dataset()
        if not df.empty:
            records = df.to_dict(orient="records")
            market_store.initialize_from_snapshot(records)
            all_stocks = market_store.get_all_stocks()

    filtered = []
    for s in all_stocks:
        if market != "ALL" and s.get("market") != market:
            continue
        if sector != "ALL" and s.get("sector") != sector:
            continue
        if s.get("traded_value", 0) > 0.1:
            filtered.append(s)
    return filtered

def get_market_summary() -> dict:
    return market_store.get_summary()

def get_indices_data() -> dict:
    return market_store.get_indices()
# endregion 4

