# Bản Đồ Nhiệt Thị Trường Chứng Khoán Việt Nam Thời Gian Thực
### Hệ Thống Trực Quan Hóa Dòng Tiền & Biến Động Thị Trường Chứng Khoán (< 16ms)

[![Phiên bản Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Khung máy chủ Web](https://img.shields.io/badge/aiohttp-3.9%2B-green.svg?style=for-the-badge&logo=aiohttp&logoColor=white)](https://docs.aiohttp.org/)
[![Thư viện trực quan hóa](https://img.shields.io/badge/Apache_ECharts-5.4-red.svg?style=for-the-badge&logo=apacheecharts&logoColor=white)](https://echarts.apache.org/)
[![Công cụ luồng dữ liệu](https://img.shields.io/badge/SSI_FastConnect-SignalR-orange.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fc-data.ssi.com.vn/)
[![Giấy phép: MIT](https://img.shields.io/badge/Gi%E1%BA%A5y_ph%C3%A9p-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> **Bản Đồ Nhiệt Chứng Khoán Việt Nam** (Vietnam Stock Heatmap) là nền tảng trực quan hóa dòng tiền và biến động giá cổ phiếu thời gian thực theo chuẩn phong cách **Finviz** và ngôn ngữ đồ họa **Bauhaus & Neo-Dark**. Hệ thống kết nối trực tiếp dòng dữ liệu khớp lệnh sống từ các sàn giao dịch **HOSE, HNX, UPCoM** thông qua hạ tầng **SSI FastConnect SignalR DataHub**, lưu trữ trạng thái tại bộ nhớ đệm **In-Memory RAM Store** với độ trễ microsecond ($O(1)$) và phát sóng dữ liệu trực tiếp tới trình duyệt web.

---

## Trực Quan Hóa Giao Diện & Kiến Trúc

### 1. Giao Diện Bản Đồ Nhiệt Thực Tế

![Giao diện Bản đồ nhiệt chứng khoán Việt Nam](Branch/Heatmap_Interface_Preview.png)

*Giao diện Neo-Dark chuẩn màn hình tài chính chuyên nghiệp: 15 nhóm ngành VS-Sector, Treemap chiếm trọn 100% tầm nhìn, quy mô ô theo giá trị giao dịch, thanh tỷ lệ độ rộng thị trường và bảng soi chi tiết theo con trỏ chuột.*

### 2. Sơ Đồ Kiến Trúc Hệ Thống 5 Tầng

![Sơ đồ kiến trúc hệ thống Bản đồ nhiệt](Branch/Heatmap_Architecture_1280x720.png)

> **Sơ đồ kiến trúc tương tác vector (SVG/HTML):** [**diagram_vietnam_stock_heatmap_5tier.html**](diagram_vietnam_stock_heatmap_5tier.html) | [Bản thu gọn (4 tầng)](diagram_vietnam_stock_heatmap.html) | [**SYSTEM_OVERVIEW.md**](Branch/SYSTEM_OVERVIEW.md)  
> *(Bao gồm chi tiết luồng SignalR SSI độ trễ < 16ms, In-Memory Store O(1), bảng màu 5 cấp và Treemap ECharts).*

---

## Đo Lường Hiệu Năng Vận Hành Hệ Thống

Hệ thống được thiết kế tối ưu hóa độ trễ ở từng khâu xử lý:

| Chỉ tiêu kỹ thuật | Kết quả đo đạc thực tế | Tiêu chuẩn mục tiêu | Đánh giá kiến trúc |
| :--- | :---: | :---: | :--- |
| Tốc độ truy vấn RAM Store | < 0.12 ms | < 1.00 ms | Cấu trúc Hash-Map In-Memory truy xuất $O(1)$ |
| Độ trễ luồng SSI SignalR -> WebSocket | ~12 - 16 ms | < 16.6 ms | Chuẩn 60 FPS, không gây giật lag giao diện |
| Tốc độ khởi động nguội (Cold-Start) | 0 ms | < 100 ms | Phục vụ tức thì từ RAM Store khi mở trình duyệt |
| Dung lượng RAM vận hành (Footprint) | ~85 MB | < 256 MB | Tiến trình Python đơn, không cần database trung gian |
| Mức tải vi xử lý (CPU Utilization) | < 2.5% | < 10.0% | Vòng lặp I/O bất đồng bộ non-blocking với aiohttp |
| Khả năng chịu tải gói tin (Throughput) | 2,500+ tick/s | 1,000 tick/s | Đảm bảo không nghẽn trong phiên ATO / ATC |
| Quy mô mã cổ phiếu theo dõi | 700+ mã | Toàn thị trường | Đồng bộ song song 3 sàn HOSE, HNX, UPCoM |

---

## Quy Chuẩn Bảng Màu & Ngữ Nghĩa Tài Chính

Hệ thống tuân thủ bảng màu 5 cấp độ chuẩn Vietstock & TradingView, cân bằng độ tương phản thị giác trong không gian làm việc Neo-Dark:

| Trạng thái biến động | Mã màu (HEX) | Điều kiện kích hoạt | Ngữ nghĩa nghiệp vụ tài chính |
| :--- | :---: | :--- | :--- |
| Giá trần | `#a855f7` | `price == ceil` hoặc `change_pct >= +6.8%` | Cổ phiếu tăng kịch biên độ trần cho phép |
| Tăng giá | `#00c073` | `change_pct > 0.00%` | Giá khớp lệnh cao hơn mức giá tham chiếu |
| Tham chiếu / Đứng giá | `#facc15` | `change_pct == 0.00%` | Thị trường cân bằng, giá bằng tham chiếu ngày |
| Giảm giá | `#ef4444` | `change_pct < 0.00%` | Giá khớp lệnh thấp hơn mức giá tham chiếu |
| Giá sàn | `#06b6d4` | `price == floor` hoặc `change_pct <= -6.8%` | Cổ phiếu giảm kịch biên độ sàn cho phép |

---

## Phân Loại 15 Nhóm Ngành Chuẩn VS-Sector

Toàn bộ 700+ mã cổ phiếu được phân nhóm tự động vào 15 ngành tài chính chính thống:

| STT | Nhóm ngành | Mã cổ phiếu tiêu biểu | Phạm vi niêm yết |
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

## Cơ Chế Tương Thích Giao Diện Đa Thiết Bị

Giao diện áp dụng triết lý ECharts-First: Treemap luôn là trọng tâm trung tâm và không bao giờ bị che khuất hoặc co cụm.

| Tiêu chí hiển thị | Màn hình máy tính (> 1024px) | Nửa màn hình / Máy tính bảng (641px - 1024px) | Màn hình điện thoại (<= 640px) |
| :--- | :--- | :--- | :--- |
| Khung Treemap chính | 100% không gian làm việc | 100% chiều rộng & chiều cao | 100% chiều rộng & chiều cao |
| Bảng chỉ số (Cột trái) | Cố định 260px (nút chuyển đổi thu gọn về 0px) | Chuyển thành ngăn kéo trượt (Drawer) có lớp nền mờ | Ngăn kéo trượt toàn chiều ngang |
| Nút kích hoạt Bảng chỉ số | Nút chuyển đổi `[ ◀ Bảng chỉ số ]` | Nút `[ Bảng chỉ số ]` trên thanh điều hướng | Nút `[ Bảng chỉ số ]` trên thanh điều hướng |
| Cơ chế đóng ngăn kéo | Bấm chuyển đổi mở lại 260px | Bấm nút đóng, bấm vùng nền mờ, hoặc phím Esc | Bấm nút đóng hoặc bấm vùng nền mờ |
| Nhãn khối Treemap | Căn giữa trọng tâm hình học (ZRender hook) | Tự động ẩn nhãn ô diện tích < 38px | Ưu tiên nhãn cho cổ phiếu thanh khoản lớn |
| Bảng soi chi tiết (Inspector) | Cập nhật tức thời theo con trỏ chuột | Cập nhật khi chạm vào từng ô cổ phiếu | Hiển thị dạng thẻ chi tiết khi chạm |

---

## Cấu Trúc Gói Tin Dữ Liệu

### 1. Gói tin khớp lệnh thời gian thực (WebSocket TICK)
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

### 2. Gói tin chỉ số và độ rộng thị trường (WebSocket INDEX_UPDATE)
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

### 3. Ảnh chụp nhanh dữ liệu REST API (/api/heatmap)
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

## Sơ Đồ Luồng Dữ Liệu Hệ Thống

```mermaid
flowchart TD
    subgraph S1 ["1. NGUỒN CẤP DỮ LIỆU GỐC & XÁC THỰC"]
        A1["config.json (Khóa RSA & Mã bí mật API)"]
        A2["SSI FastConnect REST API"]
        A3["SSI DataHub SignalR (X:ALL, MI:ALL)"]
        A4["Nguồn ngoài / VNDirect Finfo (15 Nhóm Ngành)"]
    end

    subgraph S2 ["2. DỊCH VỤ DỮ LIỆU & BẢO MẬT (market_service.py)"]
        B1["FastConnect Vault (Quản lý Bộ Nhớ Đệm Token)"]
        B2["Bộ Xử Lý Phân Ngành Động (15 Nhóm Ngành)"]
        B3["Bộ Thu Thập Dữ Liệu Khởi Tạo & Dự Phòng"]
    end

    subgraph S3 ["3. LUỒNG DỮ LIỆU SỐNG & BỘ NHỚ RAM (stream_hub.py)"]
        C1["Bộ Kết Nối SignalR"]
        C2["BỘ NHỚ RAM TRONG (700+ Cổ Phiếu, Đa Luồng An Toàn)"]
        C3["Trung Tâm Phát Sóng WebSocket"]
    end

    subgraph S4 ["4. TẦNG MÁY CHỦ WEB (app.py :8050)"]
        D1["HTTP REST APIs (/api/heatmap, /api/indices)"]
        D2["Đường Dẫn WebSocket (/ws)"]
        D3["Tự Động Tái Khởi Động & Dọn Cổng"]
    end

    subgraph S5 ["5. GIAO DIỆN NGƯỜI DÙNG CLIENT (bauhaus-ui.html)"]
        E1["KHUNG NHÌN CHÍNH: ECharts Treemap 100%"]
        E2["Ngăn Kéo Trượt (3 Chỉ Số Sàn & Dòng Tiền Hàng Đầu)"]
    end

    A1 & A2 --> B1 & B3
    A4 --> B2
    B1 & B2 & B3 -->|Dữ liệu ảnh chụp nhanh| C2
    A3 -->|Tick khớp lệnh sống X & MI| C1
    C1 --> C2
    C2 --> C3
    C3 --> D2
    C2 --> D1
    D1 -->|Khởi động tức thì 0ms| E1 & E2
    D2 -->|Tick thời gian thực < 16ms| E1 & E2
```

---

## Cấu Trúc Mã Nguồn Dự Án

```
Heatmap Stocks/
│
├── app.py                          # Máy chủ aiohttp, REST APIs, WebSocket Hub & Tái khởi động tức thời
├── stream_hub.py                   # Luồng SignalR & Bộ nhớ đệm RAM Store (MarketStateStore)
├── market_service.py               # Dịch vụ dữ liệu SSI, Quản lý Token, Phân loại 15 nhóm ngành
├── bauhaus-ui.html                 # Giao diện SPA Single-File: Treemap ECharts + Ngăn kéo phụ trợ
├── config.example.json             # Tệp mẫu cấu hình API (an toàn cho mã nguồn mở)
├── requirements.txt                # Danh sách thư viện phụ thuộc của dự án
├── .gitignore                      # Bảo vệ thông tin nhạy cảm (config.json, cache/)
├── assets/                         # Định dạng CSS / hiệu ứng bổ trợ cho giao diện
│   ├── bauhaus.css
│   ├── animations.css
│   └── custom_animation.js
├── cache/                          # Bộ nhớ đệm cục bộ (tự động tạo, lưu Token SSI)
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

## Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Yêu cầu hệ thống
- **Python**: Phiên bản `>= 3.10`
- **Tài khoản SSI FastConnect**: Đăng ký tại [SSI FastConnect Portal](https://fc-data.ssi.com.vn/) để được cấp `ConsumerID`, `ConsumerSecret` và cặp khóa RSA `PrivateKey`.

### 2. Tải mã nguồn về máy
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

### 6. Nhật ký khởi chạy thực tế
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

## Đặc Tả Giao Tiếp REST & WebSocket

| Phương thức | Đường dẫn (Endpoint) | Mô tả phản hồi |
| :---: | :--- | :--- |
| `GET` | `/` | Phục vụ trang giao diện chính `bauhaus-ui.html`. |
| `GET` | `/api/heatmap?market=ALL&sector=ALL` | Trả về mảng JSON dữ liệu 700+ mã cổ phiếu toàn thị trường từ RAM Store. |
| `GET` | `/api/indices` | Lấy dữ liệu điểm số, thanh khoản, độ rộng thị trường của VN-Index, HNX, UPCoM. |
| `GET` | `/api/summary` | Lấy tổng quan độ rộng thị trường (Số mã Trần / Tăng / Đứng / Giảm / Sàn). |
| `GET` | `/api/sectors` | Trả về danh sách 15 nhóm ngành chuẩn VS-Sector cho bộ lọc giao diện. |
| `WS` | `/ws` | Kênh WebSocket hai chiều truyền phát gói tin `SNAPSHOT`, `TICK` và `INDEX_UPDATE`. |

---

## Công Nghệ & Nền Tảng Kỹ Thuật

- **Lõi máy chủ & Mạng**: Python 3.10+, `aiohttp`, `asyncio`, `urllib3`, `requests`.
- **Kỹ thuật dữ liệu**: `pandas`, SSI FastConnect SDK (`ssi-fc-data`).
- **Giao thức thời gian thực**: SignalR (SSI MarketHub), WebSocket RFC 6455.
- **Trực quan hóa đồ họa**: Apache ECharts 5.4, ZRender Engine, Vanilla JavaScript ES6+.
- **Kiểu chữ & Bố cục**: Phông chữ Google `Be Vietnam Pro`, Thiết kế phẳng Bauhaus, CSS3 Flexbox & Grid.

---

## Bản Quyền & Miễn Trừ Trách Nhiệm

- **Bản quyền**: Phát hành theo giấy phép [MIT License](LICENSE).
- **Miễn trừ trách nhiệm**: Dự án được xây dựng phục vụ mục đích nghiên cứu, học tập kỹ thuật lập trình tài chính và trực quan hóa dữ liệu. Người dùng tự chịu trách nhiệm về các quyết định đầu tư dựa trên dữ liệu hiển thị.
