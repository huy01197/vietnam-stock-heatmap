# Vietnam Stock Market Real-Time Heatmap
### Bản Đồ Nhiệt Thị Trường Chứng Khoán Việt Nam Thời Gian Thực (< 16ms)

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Web Framework](https://img.shields.io/badge/aiohttp-3.9%2B-green.svg?style=for-the-badge&logo=aiohttp&logoColor=white)](https://docs.aiohttp.org/)
[![Visualization](https://img.shields.io/badge/Apache_ECharts-5.4-red.svg?style=for-the-badge&logo=apacheecharts&logoColor=white)](https://echarts.apache.org/)
[![Stream Engine](https://img.shields.io/badge/SSI_FastConnect-SignalR-orange.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fc-data.ssi.com.vn/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> **Vietnam Stock Heatmap** là nền tảng trực quan hóa dòng tiền và biến động giá cổ phiếu thời gian thực được thiết kế theo phong cách **Finviz** và ngôn ngữ đồ họa **Bauhaus & Neo-Dark**. Hệ thống kết nối trực tiếp dòng dữ liệu khớp lệnh sống từ các sàn giao dịch **HOSE, HNX, UPCoM** thông qua hạ tầng **SSI FastConnect SignalR DataHub**, lưu trữ trạng thái tại **In-Memory RAM Store** với độ trễ microsecond ($O(1)$) và phát sóng dữ liệu trực tiếp tới trình duyệt web.

---

## Sơ Đồ Kiến Trúc Hệ Thống (System Architecture)

![Vietnam Stock Heatmap Architecture](Branch/Heatmap_Dark_1280x640.jpg)

> **Xem bài viết phân tích kiến trúc chi tiết:** [**SYSTEM_OVERVIEW.md**](Branch/SYSTEM_OVERVIEW.md)  
> *(Bao gồm chi tiết 5 tầng công nghệ, cơ chế giải phóng socket 1-Click Restart, luồng SignalR SSI độ trễ < 16ms và ma trận điều phối tệp tin).*

---

## Tính Năng Nổi Bật (Key Features)

### 1. Real-time Sub-16ms Streaming (SignalR + WebSocket)
- Bắt tay trực tiếp với máy chủ SSI DataHub (`fc-datahub.ssi.com.vn`).
- Đăng ký song song 2 kênh dữ liệu:
  - `X:ALL`: Khớp lệnh từng lô cổ phiếu tức thời của toàn bộ sàn giao dịch.
  - `MI:ALL`: Chỉ số biến động thị trường (VN-Index, VN30, HNX-Index, UPCoM).
- Máy chủ `aiohttp` phân phối luồng dữ liệu hai chiều qua kênh WebSocket `/ws` tới hàng loạt client đồng thời với độ trễ $< 16\text{ms}$ (chuẩn 60 FPS).

### 2. ECharts Treemap Đột Phá (Hook ZRender Centroid)
- **100% Focused Viewport**: Bản đồ nhiệt Treemap chiếm trọn không gian chính, hiển thị trực quan tỷ trọng thanh khoản (GTGD) và sắc màu biến động giá.
- **ZRender Centroid Hook**: Can thiệp trực tiếp vào tọa độ trọng tâm hình học của từng khối chữ nhật, căn giữa tiêu chuẩn và tự động ẩn nhãn ô nhỏ ($< 38\text{px}$) nhằm chống tràn chữ và vỡ khung hình.
- **Bảng màu 5 cấp độ chuẩn Vietstock**:
  - **Tím**: Giá trần (Ceiling)
  - **Xanh lá**: Tăng giá (Advance)
  - **Vàng**: Tham chiếu / Đứng giá (Unchanged)
  - **Đỏ**: Giảm giá (Decline)
  - **Xanh lơ**: Giá sàn (Floor)

### 3. Phân Loại 15 Nhóm Ngành Chuẩn VS-Sector
- Chuẩn hóa hơn 700 mã cổ phiếu vào 15 nhóm ngành tài chính chính thống: *Ngân hàng, Bất động sản, Dịch vụ tài chính, Bán lẻ, Thực phẩm & Đồ uống, Tài nguyên cơ bản (Thép), Hóa chất, Dầu khí, Điện nước & Xăng dầu khí đốt, Hàng & Dịch vụ công nghiệp, Xây dựng & Vật liệu, Công nghệ thông tin, Du lịch & Giải trí, Y tế, Bảo hiểm*.
- Tự động quét bổ sung từ API VNDirect finfo cho 3,000+ mã niêm yết mới.

### 4. Responsive Drawer & Finviz Sidebar Toggle
- **Desktop**: Cung cấp nút Toggle `[ ◀ Bảng chỉ số ]` / `[ 📊 Bảng chỉ số ]` cho phép thu gọn toàn bộ Sidebar về `0px`, mở rộng bản đồ ra $100\%$ không gian làm việc.
- **Tablet / Mobile / Chia đôi màn hình**: Tự động chuyển đổi cột chỉ số thành ngăn kéo trượt (Off-canvas Drawer) mượt mà có backdrop mờ, tối ưu hóa thao tác chạm trên màn hình cảm ứng.

### 5. Cơ Chế Chuyển Tuyến Kép (Dual Connection Resiliency)
- **FASTCONNECT LIVE**: Trạng thái WebSocket kết nối thông suốt, máy chủ chủ động bắn (push) từng tick giá sống ngay khi sàn khớp lệnh.
- **POLLING LIVE (Phao cứu sinh Failover)**: Khi mạng nội bộ hoặc socket gặp sự cố, giao diện tự động chuyển sang chế độ Polling REST API mỗi 2.5s để biểu đồ không bao giờ bị dừng lại, đồng thời thử kết nối lại WebSocket ngầm.

### 6. 0ms Cold-Start & 1-Click Play Restart
- **0ms Cold-Start**: Người dùng truy cập trang web là có dữ liệu ngay lập tức từ bộ nhớ RAM `MarketStateStore` mà không cần đợi bắt tay socket.
- **1-Click Play Restart**: Khi nhấn nút Run/Play trong IDE, `app.py` tự động quét cổng `8050`, đóng các tiến trình cũ đang chiếm giữ để tái khởi động tức thì mà không gặp lỗi `Address already in use`.
- **Thoát Terminal tức thời**: Đăng ký `SIGINT` (Ctrl+C) can thiệp tầng OS nhả terminal trong 0.05s.

---

## Kiến Trúc Hệ Thống (Architecture Flow)

```mermaid
flowchart TD
    subgraph S1 ["1. NGUỒN CẤP DỮ LIỆU GỐC & XÁC THỰC"]
        A1["config.json (RSA Key & API Secret)"]
        A2["SSI FastConnect REST API"]
        A3["SSI DataHub SignalR (X:ALL, MI:ALL)"]
        A4["External / VNDirect Finfo (15 Ngành)"]
    end

    subgraph S2 ["2. DỊCH VỤ DỮ LIỆU & BẢO MẬT (market_service.py)"]
        B1["FastConnect Vault (Quản lý Token Cache)"]
        B2["Dynamic Sector Processor (15 Nhóm Ngành)"]
        B3["Snapshot & Fallback Fetcher (Lùi ngày nghỉ lễ)"]
    end

    subgraph S3 ["3. STREAMING & IN-MEMORY RAM STORE (stream_hub.py)"]
        C1["SignalR Connector Client"]
        C2["IN-MEMORY RAM STORE (700+ Stocks, Thread-Safe)"]
        C3["WebSocket Broadcaster Hub"]
    end

    subgraph S4 ["4. TẦNG MÁY CHỦ WEB (app.py :8050)"]
        D1["HTTP REST APIs (/api/heatmap, /api/indices)"]
        D2["Route /ws (Two-Way WebSocket)"]
        D3["Auto-Restart & Port Cleaner"]
    end

    subgraph S5 ["5. GIAO DIỆN CLIENT SPA (bauhaus-ui.html)"]
        E1["MAIN CANVAS: ECharts Treemap 100%"]
        E2["Responsive Drawer (3 Chỉ số sàn & Top dòng tiền)"]
    end

    A1 & A2 --> B1 & B3
    A4 --> B2
    B1 & B2 & B3 -->|Snapshot Data| C2
    A3 -->|Tick sống X & MI| C1
    C1 --> C2
    C2 --> C3
    C3 --> D2
    C2 --> D1
    D1 -->|0ms Initial Boot| E1 & E2
    D2 -->|Tick Realtime < 16ms| E1 & E2
```

---

## Cấu Trúc Mã Nguồn (Project Structure)

```
Heatmap Stocks/
│
├── app.py                      # Máy chủ aiohttp, REST APIs, WebSocket Hub & 1-Click Play Restart
├── stream_hub.py               # SignalR Streaming Hub & In-Memory RAM Store (MarketStateStore)
├── market_service.py           # Dịch vụ dữ liệu SSI, Vault quản lý Token, Phân loại 15 ngành
├── bauhaus-ui.html             # Giao diện SPA Single-File: Treemap ECharts + Responsive Drawer
├── config.example.json         # File mẫu cấu hình API (an toàn cho Open Source)
├── requirements.txt            # Danh sách thư viện phụ thuộc của dự án
├── .gitignore                  # Bảo vệ tuyệt đối thông tin nhạy cảm (config.json, cache/)
├── assets/                     # Định dạng CSS / hiệu ứng bổ trợ cho giao diện
│   ├── bauhaus.css
│   ├── animations.css
│   └── custom_animation.js
├── cache/                      # Bộ nhớ đệm cục bộ (tự động tạo, lưu SSI Token)
│
└── Branch/                     # THƯ MỤC TÀI LIỆU KIẾN TRÚC & SƠ ĐỒ HỆ THỐNG
    ├── SYSTEM_OVERVIEW.md      # Bài viết phân tích kiến trúc toàn diện & chuyên sâu
    ├── SYSTEM_OVERVIEW.docx    # Bản Word định dạng chuẩn cho báo cáo/in ấn
    ├── SYSTEM_OVERVIEW_GoogleDocs.html # Bản HTML tương thích Google Docs
    ├── Heatmap_Dark_1280x640.jpg       # Ảnh sơ đồ kiến trúc (chuẩn ngang 1280x640)
    ├── Heatmap_Dark_3x4.jpg            # Ảnh sơ đồ kiến trúc (chuẩn dọc A4 300 DPI)
    └── diagram.mmd             # Mã nguồn sơ đồ 5 Section Mermaid
```

---

## Hướng Dẫn Cài Đặt & Khởi Chạy (Quick Start)

### 1. Yêu cầu hệ thống (Prerequisites)
- **Python**: Phiên bản `>= 3.10`
- **Tài khoản SSI FastConnect**: Đăng ký tại [SSI FastConnect Portal](https://fc-data.ssi.com.vn/) để được cấp `ConsumerID`, `ConsumerSecret` và cặp khóa RSA `PrivateKey`.

### 2. Tải mã nguồn về máy (Clone Repository)
```bash
git clone https://github.com/huy01197/vietnam-stock-heatmap.git
cd "vietnam-stock-heatmap"
```

### 3. Tạo môi trường ảo & Cài đặt thư viện
```bash
# Tạo môi trường ảo
python3 -m venv .venv

# Kích hoạt môi trường (macOS / Linux)
source .venv/bin/activate

# Kích hoạt môi trường (Windows PowerShell)
# & .venv\Scripts\Activate.ps1

# Cài đặt toàn bộ thư viện cần thiết
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Cấu hình thông tin API
Sao chép tệp mẫu `config.example.json` thành `config.json` và điền thông tin của bạn:
```bash
cp config.example.json config.json
```

Chỉnh sửa `config.json` với khóa được SSI cấp:
```json
{
  "client_id": "YOUR_CLIENT_ID",
  "api_key": "YOUR_SSI_CONSUMER_ID",
  "api_secret": "YOUR_SSI_CONSUMER_SECRET",
  "private_key": "-----BEGIN RSA PRIVATE KEY-----\nYOUR_RSA_PRIVATE_KEY_HERE\n-----END RSA PRIVATE KEY-----"
}
```

> [!IMPORTANT]
> Tệp `config.json` đã được đưa vào `.gitignore` để bảo đảm tuyệt đối khóa bí mật không bao giờ bị đẩy lên GitHub.

### 5. Khởi chạy ứng dụng
```bash
python3 app.py
```
- Trình duyệt mặc định sẽ tự động mở trang web tại địa chỉ: `http://127.0.0.1:8050/`.
- Khi cần tắt: Bấm `Ctrl + C` trên terminal để đóng server ngay lập tức.

---

## Đặc Tả Giao Tiếp REST & WebSocket (API Reference)

| Phương thức | Đường dẫn (Endpoint) | Mô tả phản hồi |
| :---: | :--- | :--- |
| `GET` | `/` | Phục vụ trang giao diện chính `bauhaus-ui.html`. |
| `GET` | `/api/heatmap?market=ALL&sector=ALL` | Trả về mảng JSON dữ liệu 700+ mã cổ phiếu toàn thị trường từ RAM Store. |
| `GET` | `/api/indices` | Lấy dữ liệu điểm số, thanh khoản, độ rộng thị trường của VN-Index, HNX, UPCoM. |
| `GET` | `/api/summary` | Lấy tổng quan độ rộng thị trường (Số mã Trần / Tăng / Đứng / Giảm / Sàn). |
| `GET` | `/api/sectors` | Trả về danh sách 15 nhóm ngành chuẩn VS-Sector cho bộ lọc giao diện. |
| `WS` | `/ws` | Kênh WebSocket hai chiều truyền phát gói tin `SNAPSHOT`, `TICK` và `INDEX_UPDATE`. |

---

## Công Nghệ Sử Dụng (Tech Stack)

- **Backend & Network**: Python 3.10+, `aiohttp`, `asyncio`, `urllib3`, `requests`.
- **Data Engineering**: `pandas`, SSI FastConnect SDK (`ssi-fc-data`).
- **Real-time Protocol**: SignalR (SSI MarketHub), WebSocket RFC 6455.
- **Frontend Visualization**: Apache ECharts 5.4, ZRender Engine, Vanilla JavaScript ES6+.
- **Typography & Styling**: Google Font `Be Vietnam Pro`, Bauhaus Flat Design, CSS3 Flexbox & Grid.

---

## Bản Quyền & Miễn Trừ Trách Nhiệm (License & Disclaimer)

- **Bản quyền**: Phát hành theo giấy phép [MIT License](LICENSE).
- **Miễn trừ trách nhiệm**: Dự án được xây dựng phục vụ mục đích nghiên cứu, học tập kỹ thuật lập trình tài chính và trực quan hóa dữ liệu. Người dùng tự chịu trách nhiệm về các quyết định đầu tư dựa trên dữ liệu hiển thị.
