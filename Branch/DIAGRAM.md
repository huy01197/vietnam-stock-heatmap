# SƠ ĐỒ KIẾN TRÚC HỆ THỐNG HEATMAP STOCKS
*(Vietnamese Stock Realtime Heatmap Architecture • SSI FastConnect & ECharts Engine)*

---

## 1. SƠ ĐỒ DÒNG DỮ LIỆU & KIẾN TRÚC TỔNG THỂ (MERMAID FLOWCHART)

Sơ đồ thể hiện luồng dữ liệu 5 tầng từ nguồn cấp sàn chứng khoán, qua tầng xử lý Python Backend, lưu trữ RAM Store và phân phối thời gian thực tới giao diện người dùng:

```mermaid
flowchart TD
    %% ─────────────────────────────────────────────────────────────
    %% STYLING DEFINITIONS (BẢNG MÀU DARK CHUẨN TÀI CHÍNH)
    %% ─────────────────────────────────────────────────────────────
    classDef secBox fill:#0d1017,stroke:#1e2433,stroke-width:1.5px,stroke-dasharray: 4 4,color:#94a3b8;
    classDef cardDark fill:#131722,stroke:#2b3447,stroke-width:1.2px,color:#ffffff;
    classDef hubStore fill:#0f1c2e,stroke:#0284c7,stroke-width:2px,color:#38bdf8;
    classDef clientMain fill:#091e17,stroke:#10b981,stroke-width:2px,color:#ffffff;
    classDef clientSub fill:#161922,stroke:#64748b,stroke-width:1.2px,color:#cbd5e1;

    %% ─────────────────────────────────────────────────────────────
    %% SECTION 1: NGUỒN CẤP DỮ LIỆU GỐC & XÁC THỰC
    %% ─────────────────────────────────────────────────────────────
    subgraph SEC1 ["1. NGUỒN CẤP DỮ LIỆU GỐC & XÁC THỰC (EXTERNAL APIS)"]
        A1["🔑 config.json & SSI Auth<br/>• ConsumerID & Secret<br/>• Ký số RSA PrivateKey<br/>• Cấp & Gia hạn AccessToken"]:::cardDark
        A2["🌐 SSI FastConnect REST<br/>• DailyStockPrice (Giá thô)<br/>• DailyIndex (Điểm số)<br/>• Quét lùi 10 ngày nghỉ lễ"]:::cardDark
        A3["⚡ SSI Stream Hub (SignalR)<br/>• Kênh X:ALL (Khớp lệnh sống)<br/>• Kênh MI:ALL (Chỉ số sàn)<br/>• Socket trực tiếp sàn HOSE/HNX"]:::cardDark
        A4["📊 External & VNDirect API<br/>• 15 Nhóm ngành chuẩn hóa<br/>• Dự phòng VNDirect finfo<br/>• 3,000+ mã niêm yết"]:::cardDark
    end

    %% ─────────────────────────────────────────────────────────────
    %% SECTION 2: TẦNG DỊCH VỤ DỮ LIỆU (PYTHON)
    %% ─────────────────────────────────────────────────────────────
    subgraph SEC2 ["2. TẦNG DỊCH VỤ DỮ LIỆU (market_service.py)"]
        B1["🏷️ Dynamic Sector Processor<br/>• 15 Nhóm ngành VS-Sector<br/>• Sắp xếp theo thanh khoản<br/>• Fallback 'Khác' neo ở đáy"]:::cardDark
        B2["📥 SSI Snapshot & Fallback Fetcher<br/>• get_ssi_indices() + VNDirect<br/>• get_ssi_live_stocks()<br/>• Sliding 10-Day Window"]:::cardDark
        B3["🛡️ FastConnect Vault<br/>• Singleton Client Instance<br/>• Tự động refresh Access Token<br/>• Quản lý chứng chỉ bảo mật RSA"]:::cardDark
    end

    %% ─────────────────────────────────────────────────────────────
    %% SECTION 3: TẦNG STREAMING & RAM STATE
    %% ─────────────────────────────────────────────────────────────
    subgraph SEC3 ["3. TẦNG STREAMING & BỘ NHỚ RAM (stream_hub.py)"]
        C1["📡 SignalR Connector<br/>• Lắng nghe song song X & MI<br/>• Parser gói tin X và M<br/>• Tự động reconnect khi rớt mạng"]:::cardDark
        C2["💾 IN-MEMORY RAM STORE (Hub)<br/>• 700+ Cổ phiếu (HOSE/HNX/UPCoM)<br/>• Độ rộng: Trần / Tăng / TC / Giảm / Sàn<br/>• Thanh khoản GTGD & KLGD tức thời<br/>• Thread-Safe Mutex Lock"]:::hubStore
        C3["📢 WebSocket Broadcaster<br/>• Phát sóng TICK thời gian thực (< 16ms)<br/>• Gửi SNAPSHOT ngay khi mở web<br/>• Đẩy INDEX_UPDATE định kỳ"]:::cardDark
    end

    %% ─────────────────────────────────────────────────────────────
    %% SECTION 4: TẦNG MÁY CHỦ WEB (AIOHTTP)
    %% ─────────────────────────────────────────────────────────────
    subgraph SEC4 ["4. TẦNG MÁY CHỦ WEB & ĐIỀU PHỐI (app.py :8050)"]
        D1["🌐 HTTP REST & Auto-Restart<br/>• GET / (Phục vụ file bauhaus-ui.html)<br/>• GET /api/heatmap | /api/indices<br/>• 1-Click Play Restart (Kill port 8050)<br/>• Thoát Ctrl+C tức thời (SIGINT 0.05s)"]:::cardDark
        D2["🔌 Route /ws (Two-Way WebSocket)<br/>• Bắt tay kết nối Client trình duyệt<br/>• Snapshot khởi tạo 0ms tức thì<br/>• Truyền phát luồng Tick liên tục"]:::cardDark
    end

    %% ─────────────────────────────────────────────────────────────
    %% SECTION 5: TẦNG TRÌNH DUYỆT CLIENT (SPA)
    %% ─────────────────────────────────────────────────────────────
    subgraph SEC5 ["5. GIAO DIỆN TRÌNH DUYỆT CLIENT (bauhaus-ui.html)"]
        E1["🗺️ MAIN CANVAS: ECHARTS TREEMAP (TRỌNG TÂM 100%)<br/>• 100% Khung nhìn trung tâm, không bị che khuất<br/>• Font Be Vietnam Pro sắc nét chuẩn tiếng Việt<br/>• Màu phẳng Vietstock: Tím / Xanh / Vàng / Đỏ / Lơ<br/>• Hook ZRender Centroid căn giữa nhãn chữ<br/>• Tự ẩn chữ ô nhỏ (< 38px) chống tràn viền<br/>• Chế độ: FASTCONNECT LIVE / POLLING LIVE"]:::clientMain

        E2["📋 CỘT PHỤ / RESPONSIVE DRAWER<br/>• 3 Chỉ số sàn: VN-Index, HNX, UPCoM<br/>• Thanh tỷ lệ độ rộng 3 màu: Tăng / Đứng / Giảm<br/>• Top 6 nhóm ngành dẫn dắt dòng tiền thị trường<br/>• Live Inspector: Soi chi tiết mã tức thời<br/>• Desktop: Nút Toggle thu gọn về 0px (Finviz-style)<br/>• Nửa màn hình/Tablet/Mobile: Ngăn kéo Drawer trượt"]:::clientSub
    end

    %% ─────────────────────────────────────────────────────────────
    %% DATA FLOW CONNECTIONS (LUỒNG DỮ LIỆU)
    %% ─────────────────────────────────────────────────────────────
    A1 -->|Xác thực RSA| B3
    A2 -->|Snapshot REST| B2
    A3 -->|SignalR Stream| C1
    A4 -->|15 Nhóm ngành & Fallback| B1

    B1 -->|Metadata phân ngành| B2
    B2 -->|Đổ Snapshot khởi tạo| C2
    B3 -->|Cấp quyền API Client| B2

    C1 -->|Cập nhật Tick thô| C2
    C2 -->|Truy xuất Snapshot REST| D1
    C2 -->|Phát sóng Realtime Event| C3
    C3 -->|Truyền tin 2 chiều| D2

    D1 -->|HTTP REST Bootstrap| E1
    D1 -->|HTTP REST Bootstrap| E2
    D2 -->|WebSocket Stream Realtime| E1
    D2 -->|WebSocket Stream Realtime| E2

    %% ─────────────────────────────────────────────────────────────
    %% GÁN CLASS STYLE CHO SUBGRAPHS
    %% ─────────────────────────────────────────────────────────────
    class SEC1,SEC2,SEC3,SEC4,SEC5 secBox;
```

---

## 2. HƯỚNG DẪN XUẤT SƠ ĐỒ QUA CÁC CÔNG CỤ MERMAID

Bạn có thể sử dụng file [`diagram.mmd`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/diagram.mmd) để xuất ra file hình ảnh:

### Cách 1: Xuất trực tuyến qua Mermaid Live Editor (Khuyên dùng - Nhanh nhất)
1. Truy cập: **[https://mermaid.live](https://mermaid.live)**
2. Mở file [`diagram.mmd`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/diagram.mmd), sao chép toàn bộ nội dung và dán vào khung soạn thảo bên trái.
3. Nhấn nút **Actions** → Chọn định dạng xuất:
   - **Download PNG** (Độ phân giải cao)
   - **Download SVG** (Đồ họa vector sắc nét không vỡ hạt)
   - **Copy Markdown** / **Copy Image URL**

### Cách 2: Xem trực tiếp trong IDE (VS Code / Cursor / Antigravity)
- Nhấn phím `Cmd + Shift + V` trên file `DIAGRAM.md` để mở chế độ xem trước (Markdown Preview). Sơ đồ sẽ được tự động vẽ dưới dạng đồ họa vector tương tác.

### Cách 3: Xuất tự động bằng Mermaid CLI (Dòng lệnh terminal)
```bash
# Xuất ảnh PNG độ nét cao:
mmdc -i diagram.mmd -o diagram.png -b transparent -w 2400

# Xuất ảnh vector SVG chuẩn in ấn:
mmdc -i diagram.mmd -o diagram.svg
python3 clean_svg.py diagram.svg
```

---

## 3. BẢNG ĐỐI SOÁT: SƠ ĐỒ CŨ VS THỰC TẾ DỰ ÁN HIỆN TẠI

| Thành phần | Sơ đồ cũ (Trước đây) | Thực tế dự án hiện tại (Đã chuẩn hóa 100%) | Tình trạng khớp |
| :--- | :--- | :--- | :---: |
| **Trọng tâm giao diện** | ECharts bị kẹp cứng cạnh bảng mã table; co màn hình bị mất ECharts | **ECharts là TRỌNG TÂM 100%**. Chiếm toàn bộ không gian trung tâm trên mọi kích cỡ màn hình. | ✅ 100% Chuẩn xác |
| **Cột bên trái** | Chứa 'Bảng giá danh sách mã (Sort theo GTGD)' dài cồng kềnh | **Loại bỏ bảng table thô**. Thay bằng: **Thanh độ rộng thị trường**, **Top 6 dòng tiền ngành**, và **Live Inspector**. | ✅ 100% Chuẩn xác |
| **Responsive (Nửa màn hình, Tablet, Mobile)** | Bị lỗi xếp chồng dọc (`flex-direction: column`), cột trái chiếm 100vh đẩy ECharts biến mất khỏi màn hình | **Chuyển thành Drawer (Ngăn kéo trượt)** trên màn hình ≤ 1024px. Mặc định ẩn nhường 100% cho ECharts, bấm `[ 📊 Bảng chỉ số ]` trượt ra êm ái. | ✅ 100% Chuẩn xác |
| **Cơ chế 100% Fullscreen Heatmap** | Nút bấm bị lỗi do thiếu dấu phẩy trong JS | **Nút `[ ◀ Bảng chỉ số ]`** thu gọn cột trái về 0px, ECharts tự bung nở 100% không viền (chuẩn Finviz). | ✅ 100% Chuẩn xác |
| **Font chữ & Màu sắc** | Font mặc định, bộ màu neon chói mắt | **Font Be Vietnam Pro** chuẩn tiếng Việt; **Bộ màu phẳng nguyên bản Vietstock & SSI** (`#00c073`, `#ef4444`, `#facc15`, `#a855f7`, `#06b6d4`). | ✅ 100% Chuẩn xác |
| **Chế độ đường truyền & Failover** | Chưa mô tả cơ chế dự phòng | **Hiển thị rõ 2 trạng thái: FASTCONNECT LIVE (WebSocket) và POLLING LIVE (HTTP fallback 2.5s)**. | ✅ 100% Chuẩn xác |
| **Quản lý Server & Socket** | Phải gõ lệnh kill thủ công; bấm Ctrl+C dễ bị treo terminal | **1-Click Play Restart**: Tự giải phóng cổng 8050 khi bấm Run; **Thoát Ctrl+C tức thời (SIGINT 0.05s)**. | ✅ 100% Chuẩn xác |
| **Phân loại ngành nghề** | 13 ngành thô | **15 nhóm ngành chuẩn SSI / Vietstock (VS-Sector)** với nhóm 'Khác' được neo an toàn ở đáy. | ✅ 100% Chuẩn xác |
| **Nguồn dữ liệu chỉ số** | Chỉ phụ thuộc SSI FastConnect | Tích hợp **VNDirect finfo fallback** và trích xuất chỉ số sống đảm bảo không bao giờ rỗng số liệu. | ✅ 100% Chuẩn xác |
| **Quy mô quản lý mã CP** | 469+ cổ phiếu | Quản lý thời gian thực toàn bộ **700+ mã niêm yết** trên cả 3 sàn HOSE, HNX và UPCoM. | ✅ 100% Chuẩn xác |

---

## 4. TỆP POSTER ĐỒ HỌA A4 (300 DPI) CÓ SẴN TRONG DỰ ÁN

Hệ thống cũng duy trì script Python [`Diagram_Workflow.py`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/Diagram_Workflow.py) xuất sẵn 2 file ảnh A4 chuẩn công nghệ cao:
1. **Chủ đề Neo-Dark**: [`market_heatmap_architecture.png`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/market_heatmap_architecture.png) / [`market_heatmap_architecture.jpg`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/market_heatmap_architecture.jpg)
2. **Chủ đề Neo-Light**: [`market_heatmap_neo_light.png`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/market_heatmap_neo_light.png) / [`market_heatmap_neo_light.jpg`](file:///Users/huydang/Machine%20Learning/Heatmap%20Stocks/market_heatmap_neo_light.jpg)
