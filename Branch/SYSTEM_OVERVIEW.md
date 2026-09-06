# TÀI LIỆU VẬN HÀNH HỆ THỐNG & ĐẶC TẢ MÃ NGUỒN (SYSTEM OVERVIEW)
*(Vietnamese Stock Realtime Heatmap Architecture • Core Python Engine & ECharts Client)*

---

## PHẦN 1: TỔNG QUAN VẬN HÀNH DỰ ÁN (SYSTEM LIFECYCLE & DATA PIPELINE)

Hệ thống **Heatmap Stocks** là một ứng dụng toàn trình (Full-stack) vận hành theo mô hình: **100% Lõi xử lý & Máy chủ viết bằng Python** kết hợp với **Tầng trình chiếu đồ họa bằng HTML5/ECharts Canvas** trên trình duyệt.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               QUY TRÌNH VẬN HÀNH HỆ THỐNG                              │
└────────────────────────────────────────────────────────────────────────────────────────┘

  [Sở GDCK HOSE/HNX]
          │
          ▼
  [SSI FastConnect & DataHub]  ── (SignalR: X:ALL, MI:ALL)
          │
          ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ TẦNG DỮ LIỆU & BẢO MẬT (market_service.py)                  │
  │ • Ký số RSA, cấp phát & gia hạn Token tự động               │
  │ • Phân loại 15 nhóm ngành chuẩn VS-Sector                   │
  │ • Quét lùi 10 ngày khi thị trường nghỉ lễ                   │
  │ • VNDirect finfo fallback cho chỉ số thị trường             │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼ (Đổ Snapshot khởi tạo)
  ┌─────────────────────────────────────────────────────────────┐
  │ TẦNG STREAMING & BỘ NHỚ RAM (stream_hub.py)                 │
  │ • Lớp MarketStateStore: Lưu trữ RAM 700+ mã cổ phiếu        │
  │ • Tính toán độ rộng thị trường (Trần/Tăng/TC/Giảm/Sàn)      │
  │ • Khóa an toàn đa luồng (Thread-Safe Mutex Lock)            │
  │ • SignalR Stream Worker: Nhận tick giá sống liên tục        │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼ (Phát sóng thời gian thực)
  ┌─────────────────────────────────────────────────────────────┐
  │ TẦNG MÁY CHỦ WEB & WEBSOCKET HUB (app.py :8050)             │
  │ • Máy chủ web bất đồng bộ aiohttp (Asynchronous)            │
  │ • 1-Click Play Restart: Tự giải phóng cổng 8050             │
  │ • Thoát Ctrl+C tức thời (SIGINT 0.05s)                      │
  │ • REST Endpoints: /api/heatmap, /api/indices, /api/summary  │
  │ • WebSocket Hub: Route /ws phát sóng hai chiều              │
  │ • Tự động kích hoạt trình duyệt khi khởi động               │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼ (WebSocket Tick Stream < 16ms)
  ┌─────────────────────────────────────────────────────────────┐
  │ GIAO DIỆN CLIENT TRÌNH DUYỆT (bauhaus-ui.html)              │
  │ • Main Canvas: ECharts Treemap chiếm 100% trọng tâm         │
  │ • Hook ZRender Centroid: Căn giữa nhãn chữ và chống tràn    │
  │ • Cột phụ / Drawer: 3 chỉ số, thanh độ rộng, top dòng tiền  │
  │ • Tự co dãn theo thiết bị (Desktop, Nửa màn hình, Mobile)   │
  │ • Hai chế độ: FASTCONNECT LIVE và POLLING LIVE (Fallback)   │
  └─────────────────────────────────────────────────────────────┘
```

### 1. Trình tự khởi động hệ thống (Bootstrapping Sequence)
Khi bạn chạy lệnh `python3 app.py` (hoặc bấm nút Play trong VS Code):
1. **Kiểm tra và Giải phóng Cổng (`kill_existing_instance`)**: Quét cổng `8050`, nếu có tiến trình cũ đang chiếm giữ thì tự động đóng ngay lập tức và đợi $0.6	ext{s}$ để giải phóng socket hoàn toàn.
2. **Đăng ký Tín hiệu Thoát Tức Thời (`fast_exit_signal_handler`)**: Đăng ký sự kiện `SIGINT` (Ctrl+C) và `SIGTERM` để gọi `os._exit(0)` tức thời, tránh hiện tượng socket ngầm làm treo terminal.
3. **Khởi tạo Máy chủ Web (`app.py`)**: `aiohttp.web.Application` được tạo lập, thiết lập các middleware bảo mật CORS headers.
4. **Khởi chạy Vòng đời Ứng dụng (`on_startup`)**:
   - Nạp cấu hình khóa xác thực `config.json` thông qua `market_service.py` (`load_ssi_config()`).
   - Gọi `market_service.py` để quét dữ liệu phiên gần nhất, phân loại ngành cho hơn 700 mã và nạp vào bộ nhớ RAM `MarketStateStore`.
   - Kích hoạt luồng chạy ngầm (Background Worker Thread) của `StreamHub` để mở kết nối SignalR WebSocket tới máy chủ SSI DataHub (`fc-datahub.ssi.com.vn`).
5. **Mở cổng dịch vụ & Phục vụ Client**:
   - Máy chủ lắng nghe tại cổng `http://127.0.0.1:8050`.
   - Module `webbrowser` tự động mở trình duyệt web mặc định của hệ điều hành.

### 2. Luồng dữ liệu thời gian thực (Real-time Streaming Pipeline)
- **Khi sàn có lệnh khớp mới**: Sàn SSI bắn gói tin `X` (khớp lệnh cổ phiếu) hoặc `MI` (chỉ số sàn) qua kênh SignalR.
- **Tại `stream_hub.py`**: Parser giải mã gói tin thô, tính toán lại % biến động theo giá tham chiếu, ghi đè vào RAM Store trong thời gian microsecond ($O(1)$).
- **Phát sóng tức thì**: `stream_hub.broadcast_tick()` đẩy gói tin JSON qua kênh WebSocket `/ws` tới tất cả các trình duyệt đang kết nối.
- **Tại `bauhaus-ui.html`**: Trình duyệt nhận gói tin, cập nhật trực tiếp vào node ECharts tương ứng và kích hoạt hiệu ứng chớp màu (`.flash-update`) với độ trễ dưới $16\text{ms}$ (chuẩn 60 FPS).

### 3. Cơ chế Khởi tạo Nhanh 0ms (0ms Cold-Start Rendering)
- Ngay khi người dùng mở trang web hoặc bấm F5: Kịch bản JavaScript gửi đồng thời 2 yêu cầu REST `GET /api/heatmap` và `GET /api/indices`.
- `app.py` đọc trực tiếp từ bộ nhớ RAM `MarketStateStore` và trả về gói dữ liệu toàn thị trường chỉ trong $0\text{ms}$ mà không cần chờ đợi luồng stream, giúp giao diện bản đồ nhiệt xuất hiện tức thì không có màn hình chờ.

### 4. Cơ chế Chuyển Đổi Đường Truyền (FASTCONNECT LIVE vs POLLING LIVE)
Trên thanh Header của giao diện web luôn có đèn tín hiệu thông minh phản ánh trạng thái mạng:
- **🟢 FASTCONNECT LIVE (Chế độ chính thức)**: Kết nối WebSocket hai chiều đang mở thông suốt. Máy chủ chủ động "bắn" (push) từng tick giá sống ngay khi khớp lệnh với độ trễ $< 16\text{ms}$.
- **🟡 POLLING LIVE (Chế độ phao cứu sinh / Failover)**: Khi WebSocket bị ngắt kết nối (do mạng chập chờn hoặc máy chủ restart), giao diện lập tức chuyển sang chế độ này. Cứ mỗi $2.5\text{s}$, trình duyệt tự động gọi REST API nạp lại bảng giá để bản đồ nhiệt vẫn tiếp tục nhảy số bình thường, đồng thời chạy ngầm thử kết nối lại WebSocket.

### 5. Cơ chế Quản lý Server & Socket Hiện Đại
- **1-Click Play Restart**: Khi người dùng nhấn nút "Play" (Run Python File) trong VS Code, `app.py` tự động quét cổng 8050, đóng tiến trình cũ và chạy tiến trình mới ngay lập tức mà không bao giờ gặp lỗi `[Errno 48] address already in use`.
- **Thoát Ctrl+C tức thời (0.05s)**: Nhờ có `fast_exit_signal_handler` trực tiếp can thiệp vào tầng hệ điều hành, khi bạn nhấn `Ctrl + C`, tiến trình sẽ đóng sạch các socket ngầm và nhả lại dòng lệnh Terminal ngay lập tức.

---

## PHẦN 2: MA TRẬN PHỐI HỢP GIỮA CÁC FILE (FILE ORCHESTRATION)

| Tên File | Ngôn ngữ | Vai trò cốt lõi | Phối hợp với các file khác |
| :--- | :---: | :--- | :--- |
| [`config.json`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/config.json) | JSON | Chứa khóa định danh ConsumerID, ConsumerSecret và PrivateKey RSA. | Được nạp trực tiếp bởi `market_service.py` và `stream_hub.py`. |
| [`market_service.py`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/market_service.py) | Python | Tầng dịch vụ dữ liệu & Bảo mật: Tự động lấy và duy trì AccessToken SSI, nạp 15 nhóm ngành chuẩn VS-Sector, lùi ngày nghỉ lễ, lấy snapshot giá và chỉ số từ SSI/VNDirect. | Cung cấp dữ liệu nền tảng cho `stream_hub.py` và danh mục ngành cho `app.py`. |
| [`stream_hub.py`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/stream_hub.py) | Python | Bộ não điều phối thời gian thực: Quản lý In-Memory RAM Store, kết nối SignalR SSI và phát sóng WebSocket tới clients. | Nhận dữ liệu nền từ `market_service.py`, được kích hoạt và điều phối bởi `app.py`. |
| [`app.py`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/app.py) | Python | **Tập tin khởi chạy chính (Entry Point)**: Máy chủ web `aiohttp`, 1-Click Play Restart, thoát Ctrl+C tức thời, định tuyến REST APIs, WebSocket `/ws`. | Nhúng và phục vụ `bauhaus-ui.html`, kết nối với `stream_hub.py` và `market_service.py`. |
| [`bauhaus-ui.html`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/bauhaus-ui.html) | HTML/CSS/JS | Giao diện người dùng SPA: Bản đồ Treemap ECharts 100% trọng tâm, ngăn kéo Drawer responsive, font Be Vietnam Pro, 2 chế độ Live. | Nhận dữ liệu khởi tạo qua REST API và nhận tick giá trực tiếp từ WebSocket của `app.py`. |
| [`diagram.mmd`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/diagram.mmd) | Mermaid | Mã nguồn sơ đồ kiến trúc 5 Section chuẩn Mermaid mới nhất. | Được sử dụng để xuất ảnh vector hoặc xem trực tiếp trên Mermaid Live / IDE. |
| [`DIAGRAM.md`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/DIAGRAM.md) | Markdown | Tài liệu trực quan hóa sơ đồ kiến trúc Mermaid kèm bảng đối soát. | Tài liệu tham khảo kiến trúc chính thức của dự án. |
| [`clean_svg.py`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/clean_svg.py) | Python | Tiện ích chuyển đổi thẻ `<foreignObject>` sang `<text>`/`<tspan>` chuẩn để mở trên Adobe Illustrator không bị văng. | Xử lý các file SVG xuất từ `mmdc`. |
| [`Diagram_Workflow.py`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/Diagram_Workflow.py) | Python | Script độc lập dùng Matplotlib xuất poster kiến trúc chuẩn in ấn A4 (300 DPI) cả 2 chủ đề Dark & Light. | Xuất ra các file ảnh chất lượng cao `market_heatmap_architecture.png/jpg`. |

---

## PHẦN 3: BẢNG TRA CỨU CHI TIẾT TỪNG CODE REGION Ở CÁC FILE

Mỗi file mã nguồn trong dự án được tổ chức nghiêm ngặt theo các **Code Region** có đánh số và tên gọi rõ ràng, giúp việc bảo trì, tra cứu và mở rộng cực kỳ thuận tiện:

---

### 📂 File 1: [`app.py`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/app.py) (Tầng Máy Chủ Web & Điều Phối)

| Region | Phạm vi dòng | Tên Region | Chức năng kỹ thuật chi tiết |
| :---: | :---: | :--- | :--- |
| **`# region 1`** | L1 – L27 | **Imports & Initialization** | Nạp framework `aiohttp.web`, thư viện `sys`, `time`, `signal`, `subprocess`, `asyncio`, JSON, trình duyệt `webbrowser`, import các hàm điều phối từ `stream_hub.py` và `market_service.py`, thiết lập biến đường dẫn tĩnh `HTML_FILE` và `ASSETS_DIR`. |
| **`# region 2`** | L29 – L46 | **CORS Middleware & Security Headers** | Thiết lập middleware bảo mật kiểm soát CORS (`Access-Control-Allow-Origin: *`, hỗ trợ `OPTIONS`), đảm bảo trình duyệt có thể gọi API và kết nối WebSocket mà không bị chặn chính sách bảo mật mạng. |
| **`# region 3`** | L48 – L72 | **Web Server Setup & REST Endpoints** | Khởi tạo các hàm xử lý REST request: `handle_index` (phục vụ file HTML), `handle_api_heatmap` (lấy dữ liệu treemap theo sàn/ngành), `handle_api_summary` (tổng quan thanh khoản), `handle_api_indices` (điểm số VN-Index), `handle_api_sectors` (danh mục ngành). |
| **`# region 4`** | L74 – L119 | **WebSocket Real-time Endpoint** | Hàm `handle_websocket`: Xử lý bắt tay kết nối WebSocket hai chiều tại `/ws`, duy trì heartbeat 20s, đăng ký client vào danh sách phát sóng của `StreamHub`, ngay lập tức gửi gói tin `SNAPSHOT` và xử lý lệnh `GET_SNAPSHOT`/`PING`. |
| **`# region 5`** | L121 – L151 | **Lifecycle & Stream Hub Bootstrapper** | Quản lý vòng đời ứng dụng: Hàm `init_app()` thiết lập các tuyến đường, đăng ký hook sự kiện `on_startup` (kích hoạt luồng StreamHub chạy ngầm và đồng bộ dữ liệu) và `on_cleanup` (đóng an toàn các socket). |
| **`# region 6`** | L153 – L217 | **Main Execution, Auto-Restart & Auto-Browser** | Điểm khởi chạy chính: Tích hợp hàm `kill_existing_instance(8050)` tự động quét và tắt tiến trình cũ đang chiếm cổng 8050 giúp thao tác bấm nút **'Play' (Run File)** trong IDE hoạt động như một cơ chế **1-Click Restart** hoàn hảo; hàm `fast_exit_signal_handler` ngắt Ctrl+C tức thời; hàm `open_browser` tự mở trình duyệt sau 1.2s; hàm `web.run_app()` lắng nghe tại `127.0.0.1:8050`. |

---

### 📂 File 2: [`stream_hub.py`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/stream_hub.py) (Tầng Streaming & Bộ Nhớ RAM State)

| Region | Phạm vi dòng | Tên Region | Chức năng kỹ thuật chi tiết |
| :---: | :---: | :--- | :--- |
| **`# region 1`** | L1 – L27 | **Imports & Configuration** | Nạp các module đa luồng `threading`, xử lý bất đồng bộ `asyncio`, bộ thư viện kết nối SignalR của SSI, import đối tượng `MarketService` để nạp dữ liệu khởi tạo. |
| **`# region 2`** | L29 – L242 | **Real-time In-memory Store & State Management** | Lớp `MarketStateStore`: Quản trị toàn bộ dữ liệu 700+ mã cổ phiếu và các chỉ số trên RAM; hàm `update_stock()` cập nhật tick giá siêu tốc $O(1)$; hàm tính toán độ rộng thị trường (Trần, Tăng, TC, Giảm, Sàn); sử dụng `threading.Lock()` bảo vệ an toàn đa luồng. |
| **`# region 3`** | L244 – L437 | **FastConnect WebSocket Stream Connector** | Lớp `StreamHub`: Quản lý luồng worker kết nối SignalR WebSocket tới máy chủ SSI DataHub (`fc-datahub.ssi.com.vn`), đăng ký kênh `X:ALL` và `MI:ALL`, cơ chế tự động kết nối lại khi rớt mạng (Auto-reconnect) và luồng đồng bộ định kỳ fallback. |
| **`# region 4`** | L439 – L465 | **Stream Message Parser & Data Validation Pipeline** | Bóc tách và kiểm thực dữ liệu luồng: Giải mã các gói tin `MI` (Chỉ số sàn) và `X` (Khớp lệnh thời gian thực), chuẩn hóa dữ liệu số thực, tính lại % biến động theo giá tham chiếu và đẩy vào RAM Store. |
| **`# region 5`** | L467 – L470 | **Client WebSocket Hub & Broadcasting** | Quản trị danh sách các WebSocket client đang kết nối và triển khai hàm `broadcast_tick()` để phân phối tức thì các sự kiện giá tới trình duyệt người dùng với độ trễ dưới 16ms. |

---

### 📂 File 3: [`market_service.py`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/market_service.py) (Tầng Dịch Vụ Dữ Liệu & Phân Ngành)

| Region | Phạm vi dòng | Tên Region | Chức năng kỹ thuật chi tiết |
| :---: | :---: | :--- | :--- |
| **`# region 1`** | L1 – L62 | **Imports & Configuration** | Nạp `pandas`, `requests`, thư viện `ssi_fc_data.model`, cấu hình thư mục cache cục bộ `/cache`, nạp thông tin khóa từ `config.json` và định nghĩa các URL máy chủ SSI FastConnect. |
| **`# region 2`** | L64 – L127 | **Authentication & FastConnect Client Vault** | Quản lý phiên làm việc bảo mật: Khởi tạo singleton `MarketDataClient`, ký số RSA PrivateKey, tự động cấp phát và làm mới Access Token định kỳ, lưu cache token vào file tránh gọi lại nhiều lần. |
| **`# region 3`** | L129 – L329 | **Dynamic Sector Processing** | Tầng phân ngành chuyên nghiệp: Định nghĩa tĩnh `_default_sectors` cho ~250 mã cốt lõi thuộc 15 nhóm ngành chuẩn SSI/Vietstock; hàm `get_dynamic_sectors()` quét động 3,000+ mã từ VNDirect API; hàm `_normalize_industry()` chuẩn hóa từ khóa tiếng Việt. |
| **`# region 4`** | L331 – L591 | **SSI Market Data & Indices Fetcher** | Hàm `get_ssi_indices()` lấy điểm số chuẩn xác của VN-Index, HNX, UPCoM từ SSI kết hợp dự phòng VNDirect finfo; hàm `get_ssi_live_stocks()` lấy giá khớp, giá tham chiếu và thanh khoản kèm thuật toán trượt 10 ngày lùi phiên khi thị trường nghỉ lễ. |
| **`# region 5`** | L593 – L662 | **Data Pipeline & Heatmap Dataset Generator** | Pipeline chuẩn hóa dữ liệu sang DataFrame của Pandas: Tính giá trị giao dịch theo tỷ đồng (`traded_value = raw_val / 1 tỷ`), tính % biến động thô, lọc bỏ mã rác thanh khoản nhỏ hơn 0.02 tỷ đồng. |
| **`# region 6`** | L664 – L688 | **UI Controllers & Summary Accessors** | Cung cấp các hàm giao tiếp tầng ngoài: `get_unique_sectors()` phục vụ dropdown ngành trên giao diện và hàm cấp phát singleton `get_market_service_instance()`. |

---

### 📂 File 4: [`bauhaus-ui.html`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/bauhaus-ui.html) (Tầng Giao Diện Client SPA)

| Region | Phạm vi dòng | Tên Region | Chức năng kỹ thuật chi tiết |
| :---: | :---: | :--- | :--- |
| **`# Region [1]`** | L15 – L620 | **Design System Tokens & Dark Theme** | Định nghĩa biến CSS (Màu tăng `#00c073`, giảm `#ef4444`, tham chiếu `#facc15`, trần `#a855f7`, sàn `#06b6d4`), nhúng Google Font `Be Vietnam Pro`, hệ thống layout Flexbox Responsive Drawer (`.sidebar-open`, `.sidebar-backdrop`, `@media <= 1024px`). |
| **`# Region [2]`** | L625 – L675 | **Header & Navigation Bar** | Thanh điều hướng trên cùng: Nút Toggle `[ ◀ Bảng chỉ số ]` / `[ 📊 Bảng chỉ số ]`, các tab chọn sàn (Tất cả, HOSE, HNX, UPCoM), menu chọn ngành, chọn tiêu chí diện tích (GTGD / KLGD), ô tìm kiếm mã, đèn trạng thái kết nối stream (`FASTCONNECT LIVE` / `POLLING LIVE`). |
| **`# Region [3]`** | L677 – L805 | **Main Grid Layout (Left Sidebar & Treemap)** | Cột trái (Thẻ 3 chỉ số thị trường, Thanh đo tỷ lệ độ rộng Tăng/Đứng/Giảm, Top 6 nhóm ngành dẫn dắt dòng tiền, Live Inspector soi chi tiết mã) và Cột phải (`#treemap-canvas` chiếm 100% không gian trung tâm). |
| **`# Region [4]`** | L810 – L840 | **Footer & Market Color Legend** | Thanh dưới đáy hiển thị số lượng mã phân bổ theo 5 màu thị trường (Trần, Tăng, Đứng giá, Giảm, Sàn), chú giải bản quyền kết nối trực tiếp SSI FastConnect và đồng hồ thời gian thực. |
| **`# Region [5]`** | L845 – L945 | **Libraries & Geometry-Driven ZRender Hook** | Nạp ECharts 5.4.3 CDN và kích hoạt cơ chế can thiệp đồ họa **ZRender Hook** (`Rect.prototype.setTextContent`): Đo kích thước pixel ô chữ nhật $W 	imes H$, căn giữa tuyệt đối nhãn chữ tại trọng tâm hình học (`Centroid`), tự động ẩn chữ ở ô nhỏ $< 38	ext{px}$ để chống tràn viền. |
| **`# Region [6]`** | L949 – L1130 | **Real-time WebSocket Client & Data Pipeline** | Khởi tạo đối tượng `AppState`, thiết lập kết nối WebSocket `/ws`, chuyển đổi trạng thái `FASTCONNECT LIVE` và `POLLING LIVE`, cơ chế tự động kết nối lại (Auto-reconnect), nạp nhanh dữ liệu ban đầu qua REST `fetchInitialRest()`, hàm định dạng tỷ lệ `formatPct()`. |
| **`# Region [7]`** | L1135 – L1718 | **Market UI Controller & Interaction Handlers** | Khởi tạo Treemap ECharts đa tầng, hàm `toggleSidebar()` điều khiển ngăn kéo Drawer khi co màn hình, bộ theo dõi `ResizeObserver` co dãn mượt mà, sự kiện click mã soi thông tin, click ngành để zoom sâu và phím `Esc` quay lại toàn cảnh. |
