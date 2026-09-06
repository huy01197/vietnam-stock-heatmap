# 🎨 TÀI LIỆU HƯỚNG DẪN TẠO SƠ ĐỒ TRÊN ERASER.IO & NAPKIN.AI

Tài liệu này cung cấp sẵn mã nguồn và câu lệnh Prompt chuẩn hóa để bạn dán trực tiếp vào **Eraser.io (DiagramGPT)** hoặc **Napkin.ai** nhằm tạo ra sơ đồ kiến trúc đám mây chuẩn Enterprise.

---

## 🥇 CÁCH 1: DÙNG ERASER.IO (DIAGRAMGPT)

### Bước 1: Truy cập và mở DiagramGPT
1. Truy cập [https://app.eraser.io/](https://app.eraser.io/) (Đăng nhập bằng tài khoản Google hoặc GitHub miễn phí).
2. Tạo một **New Canvas** (hoặc New Document).
3. Nhấn vào nút **DiagramGPT** ở góc trên hoặc gõ lệnh `/diagram` trên canvas, chọn **Cloud Architecture** hoặc **Sequence Diagram**.

---

### Bước 2: Dán Prompt sau vào DiagramGPT

```text
Create a modern, high-tech Cloud Architecture Diagram for "Vietnam Stock Market Real-Time Heatmap System" with 5 distinct vertical/horizontal groups:

Group 1: "External Data Sources & SSI FastConnect"
- config.json (RSA PrivateKey & SSI Credentials)
- SSI FastConnect REST API (Daily Stock Price, Daily Index, 10-Day Holiday Fallback)
- SSI DataHub SignalR (Realtime Channels X:ALL for stock ticks, MI:ALL for market indices)
- VNDirect Finfo API (15 Industry Sector Taxonomy & 3,000+ listed tickers)

Group 2: "Data Service Layer (market_service.py)"
- FastConnect Vault (Automated SSI Token Generation, Caching & RSA Signing)
- Dynamic Sector Processor (Standardizing into 15 VS-Sectors, liquidity sorting)
- Snapshot Fetcher (REST data retriever for indices and baseline prices)

Group 3: "Realtime Streaming & In-Memory RAM Store (stream_hub.py)"
- SignalR Connector Client (Subscribing to X:ALL and MI:ALL, packet parser)
- In-Memory RAM Store (Thread-safe lock, holding 700+ stock records, market breadth stats)
- WebSocket Broadcaster (Pushing real-time TICK < 16ms and periodic INDEX_UPDATE)

Group 4: "Web Server & API Gateway (app.py :8050)"
- aiohttp HTTP REST Router (GET /, /api/heatmap, /api/indices, /api/sectors)
- Two-Way WebSocket Route (/ws)
- Process Controller (1-Click Play Restart, Port 8050 cleaner, 0.05s Ctrl+C fast exit)

Group 5: "Client Browser SPA (bauhaus-ui.html)"
- 100% Focused Treemap Canvas (Apache ECharts, ZRender Centroid alignment, Vietstock 5-color palette)
- Responsive Drawer / Sidebar (3 Index cards: VN-Index, HNX, UPCoM, Market Breadth bar, Top 6 leading sectors)

Connections & Data Flow:
- config.json -> FastConnect Vault (Authenticates & fetches Access Token)
- SSI FastConnect REST API -> Snapshot Fetcher (Provides base prices)
- SSI DataHub SignalR -> SignalR Connector Client (Pushes live trading ticks)
- VNDirect Finfo API -> Dynamic Sector Processor (Maps industry classifications)
- Snapshot Fetcher -> In-Memory RAM Store (Initializes 0ms market snapshot)
- SignalR Connector Client -> In-Memory RAM Store (Overwrites live ticks in O(1))
- In-Memory RAM Store -> aiohttp HTTP REST Router (Cold-start data)
- In-Memory RAM Store -> WebSocket Broadcaster -> Two-Way WebSocket Route
- aiohttp HTTP REST Router -> 100% Focused Treemap Canvas (0ms Initial Bootstrap)
- Two-Way WebSocket Route -> 100% Focused Treemap Canvas & Responsive Drawer (Real-time live updates < 16ms)

Theme: Dark mode or clean slate, sleek tech styling, clear labeled arrows.
```

---

### Bước 3 (Nâng cao): Mã nguồn Eraser Diagram-as-Code (Dán trực tiếp vào tab Code của Eraser)

Nếu bạn không muốn AI sinh ngẫu nhiên mà muốn sơ đồ chính xác $100\%$ từng khối theo định dạng của Eraser, mở tab **Code** trong Eraser và dán đoạn sau:

```eraser
title Vietnam Stock Market Real-Time Heatmap Architecture

// ─── Group 1: External APIs ───
group External ["1. Nguồn Cấp Dữ Liệu Gốc & Xác Thực"] {
  cfg ["config.json & RSA Key", icon: key, color: yellow]
  ssi_rest ["SSI FastConnect REST API", icon: globe, color: blue]
  ssi_signalr ["SSI DataHub SignalR (X:ALL, MI:ALL)", icon: zap, color: orange]
  vndirect ["VNDirect Finfo API (15 Ngành)", icon: database, color: purple]
}

// ─── Group 2: Market Service ───
group Service ["2. Tầng Dịch Vụ Dữ Liệu (market_service.py)"] {
  vault ["FastConnect Token Vault", icon: lock, color: yellow]
  sector_proc ["Dynamic Sector Processor", icon: tag, color: purple]
  fetcher ["SSI Snapshot & Fallback Fetcher", icon: download, color: blue]
}

// ─── Group 3: Stream Hub ───
group StreamHub ["3. Tầng Streaming & RAM State (stream_hub.py)"] {
  sig_client ["SignalR Connector Client", icon: radio, color: orange]
  ram_store ["IN-MEMORY RAM STORE (700+ Mã)", icon: cpu, color: cyan]
  broadcaster ["WebSocket Broadcaster", icon: share-2, color: green]
}

// ─── Group 4: Web Server ───
group WebServer ["4. Tầng Máy Chủ Web (app.py :8050)"] {
  rest_api ["HTTP REST API Router", icon: server, color: indigo]
  ws_route ["WebSocket Route (/ws)", icon: wifi, color: green]
  controller ["1-Click Restart & Port Cleaner", icon: refresh-cw, color: gray]
}

// ─── Group 5: Frontend UI ───
group Client ["5. Giao Diện Trình Duyệt (bauhaus-ui.html)"] {
  treemap ["ECharts Treemap (100% Focus)", icon: layout, color: green]
  drawer ["Responsive Drawer (3 Chỉ Số & Top Dòng Tiền)", icon: sidebar, color: blue]
}

// ─── Connections ───
cfg > vault: Ký số RSA
ssi_rest > fetcher: Giá chốt phiên & Lùi lễ
ssi_signalr > sig_client: Tick khớp lệnh sống
vndirect > sector_proc: 15 Nhóm ngành

vault > fetcher: Cấp Token
sector_proc > fetcher: Gán ngành
fetcher > ram_store: Đổ Snapshot ban đầu
sig_client > ram_store: Ghi đè Tick O(1)

ram_store > rest_api: Đọc Snapshot 0ms
ram_store > broadcaster: Tick Event
broadcaster > ws_route: Đẩy luồng 2 chiều

rest_api > treemap: Khởi tạo ban đầu (0ms)
rest_api > drawer: Khởi tạo ban đầu (0ms)
ws_route > treemap: Tick sống (<16ms)
ws_route > drawer: Cập nhật chỉ số
```

---

## 🥈 CÁCH 2: DÙNG NAPKIN.AI HOẶC EXCALIDRAW

1. Mở [https://www.napkin.ai/](https://www.napkin.ai/) hoặc [https://link.excalidraw.com/](https://link.excalidraw.com/).
2. Dán đoạn tóm tắt cấu trúc này:
   > "Hệ thống Vietnam Stock Heatmap gồm 5 tầng dữ liệu: Tầng 1 (External: config.json, SSI REST, SignalR X:ALL, VNDirect); Tầng 2 (Data Service: Token Vault, Phân 15 ngành, Snapshot); Tầng 3 (Stream Hub: SignalR client, In-Memory RAM Store 700 mã, WebSocket broadcaster); Tầng 4 (Web Server: aiohttp REST, /ws, 1-Click Restart); Tầng 5 (Client UI: ECharts Treemap 100% và Responsive Drawer)."
3. Nhấn **Generate** để AI tự động vẽ sơ đồ infographic.

