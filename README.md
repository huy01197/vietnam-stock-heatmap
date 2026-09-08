# Vietnam Stock Market Real-Time Heatmap
### Hệ Thống Trực Quan Hóa Dòng Tiền & Bản Đồ Nhiệt Thị Trường Chứng Khoán Thời Gian Thực (< 16ms)

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Web Framework](https://img.shields.io/badge/aiohttp-3.9%2B-green.svg?style=for-the-badge&logo=aiohttp&logoColor=white)](https://docs.aiohttp.org/)
[![Visualization](https://img.shields.io/badge/Apache_ECharts-5.4-red.svg?style=for-the-badge&logo=apacheecharts&logoColor=white)](https://echarts.apache.org/)
[![Stream Engine](https://img.shields.io/badge/SSI_FastConnect-SignalR-orange.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fc-data.ssi.com.vn/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> **Vietnam Stock Heatmap** là nền tảng trực quan hóa dòng tiền và biến động giá cổ phiếu thời gian thực được thiết kế theo phong cách **Finviz** và ngôn ngữ đồ họa **Bauhaus & Neo-Dark**. Hệ thống kết nối trực tiếp dòng dữ liệu khớp lệnh sống từ các sàn giao dịch **HOSE, HNX, UPCoM** thông qua hạ tầng **SSI FastConnect SignalR DataHub**, lưu trữ trạng thái tại **In-Memory RAM Store** với độ trễ microsecond ($O(1)$) và phát sóng dữ liệu trực tiếp tới trình duyệt web.

---

## Tổng Quan Trực Quan (Visual Showcase)

### 1. Bản Đồ Nhiệt Thị Trường Thực Tế (Live Market Heatmap Interface)

![Vietnam Stock Market Heatmap Interface](Branch/Heatmap_Interface_Preview.png)

*Giao diện Neo-Dark chuẩn Institutional Financial Terminal: 15 nhóm ngành VS-Sector, Treemap trọng tâm 100%, tỷ lệ dòng tiền theo quy mô ô, thanh độ rộng thị trường và Live Inspector theo con trỏ chuột.*

### 2. Sơ Đồ Kiến Trúc Hệ Thống 5 Tầng (System Architecture Blueprint)

![Vietnam Stock Heatmap Architecture](Branch/Heatmap_Dark_1280x640.jpg)

> **Tài liệu phân tích kiến trúc chuyên sâu:** [**SYSTEM_OVERVIEW.md**](Branch/SYSTEM_OVERVIEW.md) | [**SYSTEM_OVERVIEW.docx**](Branch/SYSTEM_OVERVIEW.docx)  
> *(Bao gồm chi tiết 5 tầng công nghệ, cơ chế giải phóng socket 1-Click Restart, luồng SignalR SSI độ trễ < 16ms và ma trận điều phối tệp tin).*

---

## Đo Lường Hiệu Năng Hệ Thống (Performance Benchmarks)

Hệ thống được thiết kế tối ưu hóa độ trễ ở từng khâu xử lý:

| Chỉ tiêu kỹ thuật (Metric) | Kết quả đo đạc (Measured) | Chuẩn mục tiêu | Ghi chú kiến trúc |
| :--- | :---: | :---: | :--- |
| Tốc độ truy vấn RAM Store | < 0.12 ms | < 1.00 ms | Cấu trúc Hash-Map In-Memory truy xuất $O(1)$ |
| Độ trễ luồng SSI SignalR -> WebSocket | ~12 - 16 ms | < 16.6 ms | Chuẩn 60 FPS, không gây giật lag giao diện |
| Tốc độ khởi động nguội (Cold-Start) | 0 ms | < 100 ms | Phục vụ tức thì từ RAM Store khi mở trình duyệt |
| Dung lượng RAM vận hành (Footprint) | ~85 MB | < 256 MB | Tiến trình Python đơn, không cần database trung gian |
| Mức tải vi xử lý (CPU Utilization) | < 2.5% | < 10.0% | Vòng lặp I/O bất đồng bộ non-blocking với aiohttp |
| Khả năng chịu tải gói tin (Throughput) | 2,500+ tick/s | 1,000 tick/s | Đảm bảo không nghẽn trong phiên ATO / ATC |
| Quy mô mã cổ phiếu theo dõi | 700+ mã | Toàn thị trường | Đồng bộ song song 3 sàn HOSE, HNX, UPCoM |

---

## Quy Chuẩn Bảng Màu & Ngữ Nghĩa Tài Chính (Design System Tokens)

Hệ thống tuân thủ bảng màu 5 cấp độ chuẩn Vietstock & TradingView, cân bằng độ tương phản thị giác trong không gian làm việc Neo-Dark:

| Trạng thái biến động | Mã màu (HEX) | Điều kiện kích hoạt | Ngữ nghĩa nghiệp vụ tài chính |
| :--- | :---: | :--- | :--- |
| Giá Trần (Ceiling) | `#a855f7` | `price == ceil` hoặc `change_pct >= +6.8%` | Cổ phiếu tăng kịch biên độ trần cho phép |
| Tăng giá (Advance) | `#00c073` | `change_pct > 0.00%` | Giá khớp lệnh cao hơn mức giá tham chiếu |
| Tham chiếu (Unchanged) | `#facc15` | `change_pct == 0.00%` | Thị trường cân bằng, giá bằng tham chiếu ngày |
| Giảm giá (Decline) | `#ef4444` | `change_pct < 0.00%` | Giá khớp lệnh thấp hơn mức giá tham chiếu |
| Giá Sàn (Floor) | `#06b6d4` | `price == floor` hoặc `change_pct <= -6.8%` | Cổ phiếu giảm kịch biên độ sàn cho phép |

---

## Phân Loại 15 Nhóm Ngành Chuẩn VS-Sector (Taxonomy Matrix)

Toàn bộ 700+ mã cổ phiếu được phân nhóm tự động vào 15 ngành tài chính chính thống:

| STT | Nhóm ngành (Sector Name) | Mã cổ phiếu tiêu biểu | Phạm vi sàn niêm yết |
| :---: | :--- | :--- | :--- |
| 01 | Ngân hàng | VCB, BID, CTG, TCB, VPB, MBB, ACB, STB, HDB, LPB | HOSE, HNX |
| 02 | Bất động sản | VIC, VHM, VRE, NVL, KDH, NLG, PDR, DIG, DXG, CEO | HOSE, HNX, UPCoM |
| 03 | Dịch vụ tài chính (Chứng khoán) | SSI, VND, VCI, SHS, HCM, VIX, MBS, CTS, FTS, BSI | HOSE, HNX |
| 04 | Tài nguyên cơ bản (Thép & Kim loại) | HPG, HSG, NKG, VGS, TLH, SMC | HOSE, HNX |
| 05 | Thực phẩm & Đồ uống | VNM, MSN, SAB, BAF, DBC, KDC, VHC, ANV, PAN | HOSE, HNX, UPCoM |
| 06 | Hóa chất & Phân bón | DGC, DPM, DCM, CSV, BFC, LAS, DDV | HOSE, HNX, UPCoM |
| 07 | Dầu khí | BSR, PLX, PVS, PVD, PVT, OIL, PVC | HOSE, HNX, UPCoM |
| 08 | Bán lẻ | MWG, PNJ, FRT, DGW, PET | HOSE |
| 09 | Công nghệ thông tin | FPT, CMG, ELC, ITD, FOX, SAM | HOSE, HNX, UPCoM |
| 10 | Điện, nước & Xăng dầu khí đốt | GAS, POW, PGV, NT2, REE, GEG, VSH, HDG | HOSE, UPCoM |
| 11 | Hàng & Dịch vụ công nghiệp | GEX, VSC, GMD, HAH, ACV, VTP, VOS | HOSE, HNX, UPCoM |
| 12 | Xây dựng & Vật liệu | CII, CTD, VCG, HHV, FCN, HT1, BCC, LCG | HOSE, HNX |
| 13 | Du lịch & Giải trí | VJC, HVN, DSN, DAH, SKG, VNG | HOSE, UPCoM |
| 14 | Y tế & Dược phẩm | DHG, TRA, IMP, DVN, DBD, JVC | HOSE, UPCoM |
| 15 | Bảo hiểm | BVH, PVI, BMI, MIG, BIC, PTI | HOSE, HNX |

---

## Cơ Chế Đáp Ứng Giao Diện Đa Thiết Bị (Responsive Viewport Behavior)

Giao diện áp dụng triết lý ECharts-First: Treemap luôn là trọng tâm trung tâm và không bao giờ bị che khuất hoặc co cụm.

| Tiêu chí tương tác | Màn hình lớn (Desktop > 1024px) | Nửa màn hình / Tablet (641px - 1024px) | Điện thoại (Mobile <= 640px) |
| :--- | :--- | :--- | :--- |
| Khung Treemap chính | 100% không gian làm việc | 100% chiều rộng & chiều cao | 100% chiều rộng & chiều cao |
| Bảng chỉ số (Sidebar) | Cố định 260px (nút Toggle thu gọn về 0px) | Chuyển thành Off-canvas Drawer có backdrop mờ | Off-canvas Drawer trượt toàn chiều ngang |
| Nút kích hoạt Bảng chỉ số | Nút Toggle `[ ◀ Bảng chỉ số ]` | Nút `[ Bảng chỉ số ]` trên thanh điều hướng | Nút `[ Bảng chỉ số ]` trên thanh điều hướng |
| Cơ chế đóng ngăn kéo | Bấm Toggle mở lại 260px | Bấm nút đóng, bấm vùng backdrop, hoặc phím Esc | Bấm nút đóng hoặc bấm vùng backdrop |
| Nhãn khối Treemap | Căn giữa trọng tâm hình học (ZRender hook) | Tự động ẩn nhãn ô diện tích < 38px | Ưu tiên nhãn cho cổ phiếu thanh khoản lớn |
| Live Inspector | Cập nhật tức thời theo con trỏ chuột | Cập nhật khi chạm vào từng ô cổ phiếu | Hiển thị dạng thẻ chi tiết khi chạm |

---

## Cấu Trúc Dữ Liệu Giao Tiếp (Wire Protocol & Data Schemas)

### 1. WebSocket TICK Packet (Khớp lệnh thời gian thực)
```json
{
  "type": "TICK",
  "data": {
    "symbol": "VIC",
    "price": 44.50,
    "change": 1.55,
    "change_pct": 3.60,
    "vol": 624500,
    "val": 27.79,
    "ref": 42.95,
    "ceil": 45.95,
    "floor": 39.95,
    "market": "HOSE",
    "sector": "Bất động sản"
  }
}
```

### 2. WebSocket INDEX_UPDATE Packet (Chỉ số & độ rộng sàn)
```json
{
  "type": "INDEX_UPDATE",
  "data": {
    "index": "VNINDEX",
    "value": 1282.72,
    "change": -0.84,
    "change_pct": -0.24,
    "advances": 90,
    "declines": 234,
    "unchanged": 49,
    "ceiling": 3,
    "floor": 2,
    "total_val": 16826.80
  }
}
```

### 3. REST API Snapshot (`GET /api/heatmap?market=HOSE&sector=Ngân%20hàng`)
```json
[
  {
    "symbol": "TCB",
    "market": "HOSE",
    "sector": "Ngân hàng",
    "price": 24.10,
    "change": -0.95,
    "change_pct": -3.89,
    "traded_value": 1045.28,
    "volume": 43372000,
    "ref_price": 25.05,
    "ceiling_price": 26.80,
    "floor_price": 23.30
  }
]
```

---

## Kiến Trúc Luồng Dữ Liệu (Architecture Flow)

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
├── app.py                          # Máy chủ aiohttp, REST APIs, WebSocket Hub & 1-Click Play Restart
├── stream_hub.py                   # SignalR Streaming Hub & In-Memory RAM Store (MarketStateStore)
├── market_service.py               # Dịch vụ dữ liệu SSI, Vault quản lý Token, Phân loại 15 ngành
├── bauhaus-ui.html                 # Giao diện SPA Single-File: Treemap ECharts + Responsive Drawer
├── config.example.json             # File mẫu cấu hình API (an toàn cho Open Source)
├── requirements.txt                # Danh sách thư viện phụ thuộc của dự án
├── .gitignore                      # Bảo vệ tuyệt đối thông tin nhạy cảm (config.json, cache/)
├── assets/                         # Định dạng CSS / hiệu ứng bổ trợ cho giao diện
│   ├── bauhaus.css
│   ├── animations.css
│   └── custom_animation.js
├── cache/                          # Bộ nhớ đệm cục bộ (tự động tạo, lưu SSI Token)
│
└── Branch/                         # THƯ MỤC TÀI LIỆU KIẾN TRÚC & TÀI NGUYÊN HÌNH ẢNH
    ├── Heatmap_Interface_Preview.png   # Ảnh chụp giao diện thực tế (Live UI Preview)
    ├── Heatmap_Dark_1280x640.jpg       # Ảnh sơ đồ kiến trúc (chuẩn ngang 1280x640)
    ├── Heatmap_Dark_3x4.jpg            # Ảnh sơ đồ kiến trúc (chuẩn dọc A4 300 DPI)
    ├── SYSTEM_OVERVIEW.md              # Bài viết phân tích kiến trúc toàn diện & chuyên sâu
    ├── SYSTEM_OVERVIEW.docx            # Bản Word định dạng chuẩn cho báo cáo/in ấn
    ├── SYSTEM_OVERVIEW_GoogleDocs.html # Bản HTML tương thích Google Docs
    └── diagram.mmd                     # Mã nguồn sơ đồ 5 Section Mermaid
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

# Cài đặt toàn bộ thư viện phụ thuộc
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

### 6. Nhật Ký Khởi Chạy Thực Tế (Execution Log)
```
$ python3 app.py
[System] Rà soát cổng 8050: Sẵn sàng khởi chạy.
[MarketService] Khởi tạo phân ngành VS-Sector từ bộ nhớ đệm (15 nhóm ngành).
[FastConnect] Bắt tay thành công SSI DataHub SignalR v2.0
[StreamHub] Đăng ký kênh truyền dữ liệu: X:ALL, MI:ALL
[MarketStateStore] Nạp thành công 712 mã cổ phiếu (HOSE: 398, HNX: 182, UPCoM: 132)
[MarketStateStore] Bộ nhớ RAM Store sẵn sàng. Phục vụ dữ liệu tức thời 0ms.
[Server] Máy chủ aiohttp đang lắng nghe tại: http://127.0.0.1:8050/
[Web] Tự động kích hoạt trình duyệt mặc định: http://127.0.0.1:8050/
(Nhấn Ctrl+C để thoát máy chủ tức thời không treo socket)
```

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
