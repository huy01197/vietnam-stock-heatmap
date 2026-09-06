# TÀI LIỆU KIẾN TRÚC & HỆ THỐNG BẢN ĐỒ THỊ TRƯỜNG CHỨNG KHOÁN (HEATMAP STOCKS)

---

## 1. TỔNG QUAN HỆ THỐNG & ĐẶC TẢ KỸ THUẬT

Hệ thống **Heatmap Stocks** là nền tảng phân tích và trực quan hóa bản đồ nhiệt thị trường chứng khoán Việt Nam theo thời gian thực (Real-time Market Heatmap), được xây dựng theo chuẩn mực thiết kế tài chính chuyên nghiệp (Bloomberg / Vietstock / Finviz).

### ✨ Các đặc tính nổi bật:
1. **100% Dữ liệu động thực tế từ SSI FastConnect**:
   - Điểm số và % biến động của các chỉ số: **VN-Index, VN30, HNX-Index, HNX30, UPCOM-Index**.
   - Dữ liệu giá khớp lệnh, giá tham chiếu, giá trần/sàn, khối lượng và giá trị giao dịch của hơn **469+ cổ phiếu đạt chuẩn**.
2. **Bộ điều khiển hình học độc quyền (Geometry-Driven Typography Engine)**:
   - Can thiệp trực tiếp vào nhân đồ họa **ZRender của Apache ECharts** (`Rect.prototype.setTextContent`).
   - Tên mã và % biến động được **căn giữa tuyệt đối tại trọng tâm (Centroid)** của từng ô chữ nhật.
   - Tự động co giãn kích thước chữ theo tỷ lệ diện tích ô thực tế ($W \times H$), không dùng ngưỡng thanh khoản thô cứng để lọc chữ.
   - Tự động ẩn chữ ở các ô siêu nhỏ ($W < 38\text{px}$ hoặc $H < 24\text{px}$) để triệt tiêu hoàn toàn hiện tượng tràn viền hoặc ký tự cắt cụt `...`.
3. **Cơ chế Streaming Thời Gian Thực (SignalR & WebSockets)**:
   - Kết nối song song tới cổng SignalR `fc-datahub.ssi.com.vn` (kênh `X:ALL`, `MI:ALL`).
   - Phân phối tick giá tới trình duyệt qua kết nối WebSocket `/ws` với độ trễ dưới $50\text{ms}$.
   - Hiệu ứng nhấp nháy đổi màu (`.flash-update`) tức thì khi có biến động giá.
4. **Giải thuật xử lý Ngày nghỉ & Cuối tuần (Sliding 10-Day Window Fallback)**:
   - Tự động quét lùi 10 ngày để lấy phiên giao dịch gần nhất khi hệ thống khởi động ngoài giờ hoặc vào ngày nghỉ, đảm bảo dữ liệu luôn đầy đủ.

---

## 2. CẤU TRÚC THƯ MỤC DỰ ÁN (PROJECT STRUCTURE)

```
Heatmap Stocks/
├── app.py                      # Máy chủ web aiohttp, REST APIs, WebSocket Hub & Điều phối hệ thống
├── market_service.py           # Dịch vụ dữ liệu SSI FastConnect REST API, Token Vault, Phân ngành ICB
├── stream_hub.py               # SignalR Streaming Client, Lưu trữ RAM State (MarketStateStore)
├── config.json                 # Thông tin khóa API (Consumer ID, Consumer Secret, Private Key)
├── bauhaus-ui.html             # Giao diện SPA chuẩn Dark Theme tích hợp ECharts Treemap Engine
├── cache/                      # Thư mục lưu cache cục bộ (SSI Access Token, Metadata Ngành nghề)
│   ├── ssi_token_cache.json
│   └── stocks_cache.json
├── assets/                     # Các file định dạng phong cách giao diện bổ trợ (CSS/JS)
│   ├── bauhaus.css
│   ├── animations.css
│   └── custom_animation.js
└── DOCS.md                     # Tài liệu kiến trúc toàn diện của hệ thống
```

---

## 3. GIẢI THÍCH CHI TIẾT CÁC CODE REGION Ở TỪNG FILE

### 📂 File 1: `market_service.py` (Tầng Dịch vụ Dữ liệu & Xử lý Thị trường)

| Region | Tên Region | Vai trò & Chức năng kỹ thuật |
| :--- | :--- | :--- |
| **`# region 1`** | **Imports & Configuration** | Nạp các thư viện `pandas`, `requests`, `ssi_fc_data.model`, `MarketDataClient`, cấu hình thư mục lưu cache `/cache`, đọc file `config.json` và thiết lập các URL máy chủ SSI FastConnect. |
| **`# region 2`** | **Authentication & FastConnect Vault** | Quản lý phiên xác thực, tự động khởi tạo và lưu giữ đối tượng `MarketDataClient` singleton cùng AccessToken của SSI để tái sử dụng xuyên suốt phiên làm việc. |
| **`# region 3`** | **Dynamic Sector Processing** | Tự động kết nối API phân ngành chứng khoán để lấy ngành nghề chuẩn ICB của hơn 3,000 mã cổ phiếu; có sẵn tầng lưu cache cục bộ và cơ chế tự động gán vào nhóm `"Khác"` nếu gặp mã mới chưa phân loại. |
| **`# region 4`** | **SSI Market Data & Indices Fetcher** | Gọi trực tiếp API SSI FastConnect: `get_ssi_indices()` lấy chuẩn xác điểm số, % thay đổi và số mã Tăng/Giảm của các chỉ số; `get_ssi_live_stocks()` lấy toàn bộ giá khớp, giá tham chiếu và thanh khoản kèm thuật toán lùi ngày khi nghỉ lễ. |
| **`# region 5`** | **Data Pipeline & Heatmap Dataset Generator** | Pipeline chuẩn hóa dữ liệu: tính toán diện tích theo tỷ đồng (`traded_value = raw_val / 1,000,000,000`), tính % biến động thô từ giá khớp và giá tham chiếu, áp dụng bộ lọc thanh khoản $> 0.02$ tỷ đồng. |
| **`# region 6`** | **UI Controllers & Summary Accessors** | Cung cấp các hàm tiền xử lý phục vụ các API REST: lọc theo sàn, lọc theo ngành, tìm kiếm mã, sắp xếp danh sách và lấy tóm tắt thị trường. |

---

### 📂 File 2: `stream_hub.py` (Tầng Streaming Real-time & Quản lý Trạng thái RAM)

| Region | Tên Region | Vai trò & Chức năng kỹ thuật |
| :--- | :--- | :--- |
| **`# region 1`** | **Imports & Configuration** | Nạp các module đa luồng `threading`, `asyncio` và kết nối với các hàm dịch vụ từ `market_service`. |
| **`# region 2`** | **Real-time In-memory Store** | Lớp `MarketStateStore`: Lưu trữ toàn bộ dữ liệu 469+ cổ phiếu và chỉ số thị trường trực tiếp trong bộ nhớ RAM, đảm bảo thread-safe (an toàn đa luồng) với `threading.Lock()`. |
| **`# region 3`** | **FastConnect WebSocket Stream Connector** | Lớp `StreamHub`: Khởi chạy luồng kết nối WebSocket SignalR tới máy chủ `https://fc-datahub.ssi.com.vn` (kênh `X:ALL`, `B:ALL`, `MI:ALL`), đồng thời duy trì luồng đồng bộ dữ liệu định kỳ. |
| **`# region 4`** | **Stream Message Parser & Data Validation** | Bộ bóc tách thông điệp stream: Giải mã các gói tin `MI` (Chỉ số), `X` (Khớp lệnh realtime), tính toán lại % biến động và cập nhật trạng thái mới nhất vào RAM. |
| **`# region 5`** | **Client WebSocket Hub & Broadcasting** | Quản lý danh sách các trình duyệt Web đang kết nối và phát sóng (`broadcast`) tức thì dữ liệu `SNAPSHOT`, `TICK` và `INDEX_UPDATE` tới người dùng. |

---

### 📂 File 3: `app.py` (Tầng Web Server & Điều phối Hệ thống)

| Region | Tên Region | Vai trò & Chức năng kỹ thuật |
| :--- | :--- | :--- |
| **`# region 1`** | **Imports & Initialization** | Khởi tạo framework `aiohttp.web`, nạp cấu hình đường dẫn file HTML và thư mục tĩnh `assets`. |
| **`# region 2`** | **CORS Middleware & Security Headers** | Middleware thiết lập đầy đủ CORS headers (`Access-Control-Allow-Origin: *`), cho phép giao tiếp API và WebSocket thông suốt. |
| **`# region 3`** | **Web Server Setup & REST Endpoints** | Thiết lập các đường dẫn REST API: `/` (phục vụ file HTML), `/api/heatmap`, `/api/summary`, `/api/indices`, `/api/sectors`. |
| **`# region 4`** | **WebSocket Real-time Endpoint** | Xử lý route `/ws`: Bắt tay kết nối WebSocket với trình duyệt, lập tức gửi gói dữ liệu ban đầu `SNAPSHOT` và duy trì phản hồi lệnh `PING`/`GET_SNAPSHOT`. |
| **`# region 5`** | **Lifecycle & Stream Hub Bootstrapper** | Quản lý sự kiện khởi động server `on_startup` (gắn event loop và bật StreamHub) và sự kiện tắt server an toàn `on_cleanup`. |
| **`# region 6`** | **Main Execution & Auto-Browser** | Điểm khởi chạy ứng dụng tại địa chỉ `http://127.0.0.1:8050` và kích hoạt tự động mở trình duyệt. |

---

### 📂 File 4: `bauhaus-ui.html` (Tầng Giao diện Người dùng & Engine ECharts)

| Region | Tên Region | Vai trò & Chức năng kỹ thuật |
| :--- | :--- | :--- |
| **`# Region [1]`** | **Design System Tokens & Dark Theme** | Khởi tạo bảng màu tài chính tương phản cao chuẩn Vietstock: Tím trần (`#a855f7`), Xanh tăng (`#00c073`), Vàng TC (`#facc15`), Đỏ giảm (`#ef4444`), Xanh lơ sàn (`#06b6d4`). |
| **`# Region [2]`** | **Header & Navigation Bar** | Thanh công cụ: Các nút chọn sàn (Tất cả / HOSE / HNX / UPCOM), menu lọc ngành (sắp xếp theo thanh khoản, `Khác` ở đáy cùng), tiêu chí diện tích (GTGD / KLGD), tìm kiếm mã và đèn trạng thái stream. |
| **`# Region [3]`** | **Main Responsive Layout** | Cột trái / Drawer phụ (Thẻ 3 chỉ số thị trường, Thanh tỉ lệ độ rộng Tăng/Đứng/Giảm, Top 6 dòng tiền ngành, Khối chi tiết mã Live Inspector; tự thu gọn thành Drawer trên mobile/tablet hoặc qua nút Toggle) và Cột phải (Bản đồ nhiệt ECharts Treemap 100% trọng tâm). |
| **`# Region [4]`** | **Footer & Market Color Legend** | Chân trang hiển thị số lượng mã theo 5 màu thị trường (Trần, Tăng, Đứng giá, Giảm, Sàn) và đồng hồ cập nhật. |
| **`# Region [5]`** | **Libraries & ECharts Engine Patch** | Nạp ECharts 5.4.3 CDN và kích hoạt **Geometry-Driven ZRender Hook** (`echarts.graphic.Rect.prototype.setTextContent`) để đo toạ độ pixel $W \times H$, căn giữa văn bản và chống tràn chữ. |
| **`# Region [6]`** | **Real-time WebSocket Client** | Duy trì kết nối WebSocket Client `/ws`, tự động kết nối lại khi mất mạng, xử lý cập nhật dữ liệu và hàm `formatPct` định dạng `#.#%` / `+#.##%` / `+0%`. |
| **`# Region [7]`** | **Market UI Controller & Interaction Handlers** | Khởi tạo Treemap ECharts đa tầng, vẽ các ô cổ phiếu căn giữa bên trong từng khối ngành, hỗ trợ nhấp chọn mã xem chi tiết, nhấp vào ngành để Zoom chi tiết, và phím `Esc` để quay lại toàn cảnh tức thời ($0\text{ms}$). |

---

## 4. SƠ ĐỒ KIẾN TRÚC & LUỒNG KẾT NỐI DỮ LIỆU (SYSTEM ARCHITECTURE MAP)

```mermaid
flowchart TD
    subgraph S1["1. Nguồn Dữ Liệu Gốc (SSI FastConnect & External APIs)"]
        CFG["config.json\n(API Key, Secret, PrivateKey)"]
        SSI_REST["SSI FastConnect REST API\n(DailyIndex, DailyStockPrice, AccessToken)"]
        SSI_STREAM["SSI FastConnect DataHub\n(SignalR WebSocket: X:ALL, MI:ALL)"]
        SEC_API["External & VNDirect API\n(Phân ngành 15 nhóm & Fallback Chỉ số)"]
    end

    subgraph S2["2. Tầng Dịch Vụ Dữ Liệu (market_service.py)"]
        AUTH["FastConnect Vault\nget_ssi_client() / get_ssi_token()"]
        SECTOR_PROC["Dynamic Sector Processor\n15 Nhóm ngành chuẩn hóa + Fallback 'Khác'"]
        DATA_FETCHER["SSI & Fallback Fetcher\nget_ssi_indices() + VNDirect / get_ssi_live_stocks()"]
        DATA_PIPELINE["Data Pipeline & Normalizer\ngenerate_heatmap_dataset()\n(Quy đổi Tỷ VNĐ, % thô, Lọc > 0.02 Tỷ)"]
    end

    subgraph S3["3. Tầng Streaming & RAM State (stream_hub.py)"]
        SIGNALR_CLIENT["MarketDataStream Connector\n(Lắng nghe X:ALL, MI:ALL)"]
        STREAM_PARSER["Stream Message Parser\n(Bóc tách DataType X, MI)"]
        RAM_STORE[("MarketStateStore (RAM)\n- Danh sách 700+ Cổ phiếu\n- Chỉ số VN-Index, HNX, UPCoM\n- Thanh tỉ lệ Độ rộng & Top dòng tiền")]
        WS_BROADCASTER["WebSocket Broadcaster\n(Đẩy TICK, SNAPSHOT, INDEX_UPDATE)"]
    end

    subgraph S4["4. Tầng Máy Chủ Web (app.py)"]
        AIOHTTP_APP["aiohttp Web Server (Port 8050)"]
        REST_ROUTES["REST Endpoints\n- GET / (Phục vụ HTML)\n- GET /api/heatmap\n- GET /api/indices\n- GET /api/summary\n- GET /api/sectors"]
        WS_ROUTE["WebSocket Endpoint\n- /ws (Kết nối thời gian thực 2 chiều)"]
    end

    subgraph S5["5. Tầng Trình Duyệt Web Client (bauhaus-ui.html)"]
        WS_CLIENT["Client WebSocket Manager\n(Nhận SNAPSHOT, TICK, INDEX_UPDATE)"]
        REST_INIT["Initial REST Fetcher\n(Nạp nhanh dữ liệu tức thì khi mở trang)"]
        LEFT_PANEL["Cột Phụ / Responsive Drawer\n- Chỉ số VN-Index, HNX, UPCoM\n- Thanh tỉ lệ độ rộng Tăng/Đứng/Giảm\n- Top 6 dòng tiền ngành & Live Inspector\n- Ẩn/Hiện Drawer trên mobile/tablet"]
        TREEMAP_ENGINE["ECharts Treemap (Trọng tâm 100%)\n- Level 1: Khung 15 Nhóm ngành\n- Level 2: Ô Cổ phiếu (Font Be Vietnam Pro)\n- Màu phẳng chuẩn Vietstock & Centroid Hook\n- Co dãn mượt mà với ResizeObserver"]
    end

    %% Kết nối luồng dữ liệu
    CFG --> AUTH
    AUTH --> SSI_REST
    AUTH --> SIGNALR_CLIENT
    SSI_STREAM --> SIGNALR_CLIENT
    SEC_API --> SECTOR_PROC

    SSI_REST --> DATA_FETCHER
    SECTOR_PROC --> DATA_PIPELINE
    DATA_FETCHER --> DATA_PIPELINE

    DATA_PIPELINE --> RAM_STORE
    SIGNALR_CLIENT --> STREAM_PARSER
    STREAM_PARSER --> RAM_STORE
    RAM_STORE --> WS_BROADCASTER

    RAM_STORE --> REST_ROUTES
    WS_BROADCASTER --> WS_ROUTE

    AIOHTTP_APP --> REST_ROUTES
    AIOHTTP_APP --> WS_ROUTE

    REST_ROUTES -.->|HTTP JSON| REST_INIT
    WS_ROUTE <==>|Realtime WebSocket| WS_CLIENT

    REST_INIT --> LEFT_PANEL
    REST_INIT --> TREEMAP_ENGINE
    WS_CLIENT --> LEFT_PANEL
    WS_CLIENT --> TREEMAP_ENGINE
```

---

## 5. BỘ ĐIỀU KHIỂN HÌNH HỌC & QUY TẮC HIỂN THỊ CHỮ (TYPOGRAPHY ENGINE)

Để giải quyết triệt để lỗi căn lệch dòng và tràn viền chữ trong Apache ECharts, hệ thống tích hợp bộ Hook trực tiếp vào nhân ZRender:

### Bảng phân bổ kích thước chữ theo diện tích ô thực tế ($W \times H$):

| Kích thước ô thực tế trên màn hình | Quyết định hiển thị chữ | Kích thước Font Mã CP | Kích thước Font % Biến động |
| :--- | :--- | :--- | :--- |
| **Ô rất to** ($W \ge 130\text{px}, H \ge 75\text{px}$) | ✅ Hiển thị đầy đủ | **`20px`** (Black 900) | **`14px`** (Bold 800) |
| **Ô to vừa** ($W \ge 80\text{px}, H \ge 48\text{px}$) | ✅ Hiển thị đầy đủ | **`15px`** (Black 900) | **`12px`** (Bold 800) |
| **Ô trung bình** ($W \ge 52\text{px}, H \ge 32\text{px}$) | ✅ Hiển thị đầy đủ | **`12px`** (Bold 800) | **`10px`** (Bold 700) |
| **Ô nhỏ gọn** ($W \ge 38\text{px}, H \ge 24\text{px}$) | ✅ Hiển thị đầy đủ | **`9.5px`** (Bold 800) | **`8px`** (Bold 700) |
| **Ô siêu nhỏ** ($W < 38\text{px}$ hoặc $H < 24\text{px}$) | ⛔ Tự động ẩn chữ | *Không hiện chữ để tránh tràn viền, chỉ để ô màu phẳng* |

---

## 6. HƯỚNG DẪN KHỞI CHẠY & VẬN HÀNH (QUICKSTART)

### 1. Cài đặt môi trường & Thư viện phụ thuộc
```bash
pip install -r requirements.txt
# hoặc cài trực tiếp:
pip install aiohttp pandas requests ssi-fc-data
```

### 2. Cấu hình thông tin xác thực SSI FastConnect
Chỉnh sửa file `config.json` với thông tin được cấp từ SSI:
```json
{
  "consumerID": "YOUR_CONSUMER_ID",
  "consumerSecret": "YOUR_CONSUMER_SECRET",
  "privateKey": "YOUR_PRIVATE_KEY_CONTENT"
}
```

### 3. Khởi chạy hệ thống
```bash
python3 app.py
```
- Server sẽ khởi động tại: **`http://127.0.0.1:8050`**
- Trình duyệt mặc định sẽ tự động mở trang web hiển thị Bản đồ thị trường trực quan theo thời gian thực.


