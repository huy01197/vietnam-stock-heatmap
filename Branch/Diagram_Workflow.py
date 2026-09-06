# File: Diagram_Workflow.py
"""
Script tạo sơ đồ kiến trúc hệ sinh thái Heatmap Stocks chuẩn hóa theo thiết kế Mermaid:
- Phân tách 5 Section riêng biệt với Header Pill Box độc lập
- Tất cả nhãn chữ (Labels, Tags, Titles) đều có Box bao bọc riêng, triệt tiêu 100% va chạm đường kẻ
- Khổ giấy A4 dọc chuẩn 300 DPI, bố cục thoáng đãng, sắc nét
- Hỗ trợ 2 chủ đề tối giản: Neo-Dark (mặc định) & Neo-Light
"""

import os
import sys

# Thiết lập thư mục cache tạm thời cho Matplotlib:
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_cache"

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

def generate_diagram(theme="neo-dark"):
    # ─── 1. BẢNG MÀU TỐI GIẢN CHUẨN CÔNG NGHỆ (DESIGN TOKENS) ───
    if theme == "neo-dark":
        c_canvas     = "#08090d"  # Nền canvas sâu thẳm
        c_section_bg = "#0d1017"  # Nền Section
        c_section_bd = "#1e2433"  # Viền Section nét đứt
        c_sec_hdr_bg = "#161b26"  # Nền Header Box của Section
        c_sec_hdr_bd = "#2b3447"  # Viền Header Box của Section
        c_sec_hdr_tt = "#94a3b8"  # Chữ Header Section (Slate 400)
        
        c_card_bg    = "#131722"  # Nền Card
        c_card_bd    = "#22293a"  # Viền Card
        c_card_tag   = "#38bdf8"  # Tag badge (Sky blue)
        c_card_tt    = "#ffffff"  # Tiêu đề Card (Trắng tinh)
        c_card_desc  = "#94a3b8"  # Chữ mô tả Card
        
        c_hub_bg     = "#0f1c2e"  # Nền RAM Store trung tâm
        c_hub_bd     = "#0284c7"  # Viền RAM Store (Cyan)
        c_hub_tt     = "#38bdf8"  # Tiêu đề RAM Store
        c_hub_desc   = "#cbd5e1"
        
        c_arrow_line = "#334155"  # Thân mũi tên
        c_arrow_head = "#38bdf8"  # Đầu mũi tên
        c_badge_bg   = "#0f172a"  # Nền Box của nhãn mũi tên (Solid 100%)
        c_badge_bd   = "#0284c7"  # Viền Box của nhãn mũi tên
        c_badge_tt   = "#38bdf8"  # Chữ trong nhãn mũi tên
        
        c_header_main = "#ffffff"
        c_header_sub  = "#38bdf8"
    else:
        # neo-light (Bản in ấn giấy trắng A4)
        c_canvas     = "#f8fafc"
        c_section_bg = "#f1f5f9"
        c_section_bd = "#cbd5e1"
        c_sec_hdr_bg = "#e2e8f0"
        c_sec_hdr_bd = "#94a3b8"
        c_sec_hdr_tt = "#334155"
        
        c_card_bg    = "#ffffff"
        c_card_bd    = "#d1d5db"
        c_card_tag   = "#0284c7"
        c_card_tt    = "#0f172a"
        c_card_desc  = "#475569"
        
        c_hub_bg     = "#f0f9ff"
        c_hub_bd     = "#0284c7"
        c_hub_tt     = "#0369a1"
        c_hub_desc   = "#334155"
        
        c_arrow_line = "#94a3b8"
        c_arrow_head = "#0284c7"
        c_badge_bg   = "#ffffff"
        c_badge_bd   = "#0284c7"
        c_badge_tt   = "#0369a1"
        
        c_header_main = "#0f172a"
        c_header_sub  = "#0284c7"

    # ─── 2. THIẾT LẬP CANVAS KHỔ A4 DỌC (8.27 x 11.69 INCH, 300 DPI) ───
    fig_width = 8.27
    fig_height = 11.69
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=300)
    fig.patch.set_facecolor(c_canvas)
    ax.set_facecolor(c_canvas)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 175)
    ax.axis('off')

    # ─── 3. HÀM VẼ KHUNG PHÂN VÙNG SECTION (CÓ HEADER PILL BOX RIÊNG) ───
    def draw_section(x, y, w, h, title):
        # 1. Khung Section nền mờ nét đứt
        sec_box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.6,rounding_size=1.5",
            linewidth=0.9,
            linestyle='--',
            edgecolor=c_section_bd,
            facecolor=c_section_bg,
            zorder=1
        )
        ax.add_patch(sec_box)

        # 2. Header Box riêng biệt nằm trên đỉnh Section (Không bị đè)
        hdr_w = len(title) * 0.95 + 4.0
        hdr_x = x + (w - hdr_w) / 2.0
        hdr_y = y + h - 1.8
        
        hdr_box = patches.FancyBboxPatch(
            (hdr_x, hdr_y), hdr_w, 2.8,
            boxstyle="round,pad=0.2,rounding_size=0.6",
            linewidth=0.8,
            edgecolor=c_sec_hdr_bd,
            facecolor=c_sec_hdr_bg,
            zorder=2
        )
        ax.add_patch(hdr_box)
        
        ax.text(
            x + w / 2.0, hdr_y + 1.4, title,
            ha='center', va='center',
            fontsize=6.8, fontweight='bold',
            color=c_sec_hdr_tt, zorder=3,
            fontfamily='sans-serif'
        )

    # ─── 4. HÀM VẼ UI CARD VỚI BOX TYPO RÕ RÀNG ───
    def draw_card(x, y, w, h, tag, title, bullets, is_hub=False):
        bg = c_hub_bg if is_hub else c_card_bg
        bd = c_hub_bd if is_hub else c_card_bd
        tt_col = c_hub_tt if is_hub else c_card_tt
        tag_col = c_card_tag
        desc_col = c_hub_desc if is_hub else c_card_desc

        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.5,rounding_size=1.0",
            linewidth=1.2 if is_hub else 0.8,
            edgecolor=bd,
            facecolor=bg,
            zorder=3
        )
        ax.add_patch(rect)

        cur_y = y + h - 1.4
        if tag:
            ax.text(
                x + 1.4, cur_y, tag.upper(),
                ha='left', va='top',
                fontsize=5.2, fontweight='bold',
                color=tag_col, zorder=4,
                fontfamily='monospace'
            )
            cur_y -= 1.6

        ax.text(
            x + 1.4, cur_y, title,
            ha='left', va='top',
            fontsize=7.4 if not is_hub else 8.0, fontweight='bold',
            color=tt_col, zorder=4,
            fontfamily='sans-serif'
        )
        cur_y -= 2.2

        line = patches.Rectangle(
            (x + 1.4, cur_y + 0.3), w - 2.8, 0.12,
            facecolor=bd, edgecolor='none', alpha=0.5, zorder=4
        )
        ax.add_patch(line)
        cur_y -= 1.0

        if bullets:
            avail_h = cur_y - y - 0.6
            spacing = avail_h / max(len(bullets), 1)
            for i, b_text in enumerate(bullets):
                item_y = cur_y - (i * spacing)
                ax.text(
                    x + 1.4, item_y, f"• {b_text}",
                    ha='left', va='top',
                    fontsize=5.8, fontweight='normal',
                    color=desc_col, zorder=4,
                    fontfamily='sans-serif'
                )

    # ─── 5. HÀM VẼ MŨI TÊN KẾT NỐI VỚI BOX RIÊNG CHO NHÃN (LABEL PILL BOX) ───
    def draw_arrow(start, end, label=None, label_pos=0.5, offset_x=0, offset_y=0):
        arrow = patches.FancyArrowPatch(
            start, end,
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=1.0,
            edgecolor=c_arrow_line,
            facecolor=c_arrow_head,
            zorder=5
        )
        ax.add_patch(arrow)

        if label:
            mid_x = start[0] + (end[0] - start[0]) * label_pos + offset_x
            mid_y = start[1] + (end[1] - start[1]) * label_pos + offset_y
            
            # Box riêng biệt bao bọc Typo (100% Solid, không lẫn vào đường line)
            ax.text(
                mid_x, mid_y, label,
                ha='center', va='center',
                fontsize=5.6, fontweight='bold',
                color=c_badge_tt, zorder=7,
                bbox=dict(
                    boxstyle="round,pad=0.35,rounding_size=0.5",
                    facecolor=c_badge_bg,
                    edgecolor=c_badge_bd,
                    linewidth=0.8,
                    alpha=1.0
                ),
                fontfamily='sans-serif'
            )

    # ─── 6. HEADER CHÍNH CỦA BẢN VẼ ───
    ax.text(50, 172.0, "KIẾN TRÚC HỆ THỐNG BẢN ĐỒ THỊ TRƯỜNG CHỨNG KHOÁN", ha='center', va='top', fontsize=11.5, fontweight='black', color=c_header_main, fontfamily='sans-serif')
    ax.text(50, 169.2, "VIETNAMESE STOCK REALTIME HEATMAP ARCHITECTURE  •  SSI FASTCONNECT ENGINE", ha='center', va='top', fontsize=6.8, fontweight='bold', color=c_header_sub, fontfamily='sans-serif')

    # ═══════════════════════════════════════════════════════════════════
    # SECTION 1: NGUỒN DỮ LIỆU GỐC & XÁC THỰC (y: 139 -> 165, h: 26)
    # ═══════════════════════════════════════════════════════════════════
    draw_section(3, 139, 94, 26, "1. NGUỒN DỮ LIỆU GỐC FASTCONNECT & EXTERNAL APIS")

    draw_card(5.5, 141.5, 20.5, 19.0, "AUTH VAULT", "config.json", [
        "ConsumerID & Secret",
        "Ký số RSA PrivateKey",
        "Cấp Token xác thực"
    ])

    draw_card(28.2, 141.5, 20.5, 19.0, "REST SERVICE", "SSI FastConnect", [
        "DailyIndex (Điểm số)",
        "DailyStockPrice (Giá thô)",
        "Lùi ngày khi nghỉ lễ"
    ])

    draw_card(51.0, 141.5, 20.5, 19.0, "DATA STREAM", "SSI Stream Hub", [
        "SignalR kênh X:ALL",
        "SignalR kênh MI:ALL",
        "Socket khớp lệnh sống"
    ])

    draw_card(73.8, 141.5, 20.5, 19.0, "SECTOR & FALLBACK", "External & VNDirect", [
        "Phân ngành 15 nhóm chuẩn",
        "VNDirect finfo indices",
        "3,000+ mã niêm yết"
    ])

    # ═══════════════════════════════════════════════════════════════════
    # SECTION 2: TẦNG DỊCH VỤ DỮ LIỆU (market_service.py) (y: 105 -> 132, h: 27)
    # ═══════════════════════════════════════════════════════════════════
    draw_section(3, 105, 94, 27, "2. TẦNG DỊCH VỤ DỮ LIỆU (market_service.py)")

    draw_card(5.5, 107.5, 27.5, 20.0, "SECTOR PROCESSOR", "VS-Sector Taxonomy", [
        "15 Nhóm ngành chuẩn hóa",
        "Fallback 'Khác' an toàn",
        "Sắp xếp thanh khoản ngành"
    ])

    draw_card(36.2, 107.5, 27.5, 20.0, "DATA FETCHER", "SSI & Fallback Fetcher", [
        "get_ssi_indices() + VNDirect",
        "get_ssi_live_stocks()",
        "Sliding 10-Day Window"
    ])

    draw_card(67.0, 107.5, 27.5, 20.0, "AUTH MANAGER", "FastConnect Vault", [
        "Singleton Client Instance",
        "Tự động làm mới Token",
        "Quản lý chứng chỉ bảo mật"
    ])

    # ═══════════════════════════════════════════════════════════════════
    # SECTION 3: TẦNG STREAMING & RAM STATE (stream_hub.py) (y: 71 -> 98, h: 27)
    # ═══════════════════════════════════════════════════════════════════
    draw_section(3, 71, 94, 27, "3. TẦNG STREAMING & BỘ NHỚ RAM (stream_hub.py)")

    draw_card(5.5, 73.5, 26.5, 20.0, "SIGNALR CONNECTOR", "MarketDataStream", [
        "Lắng nghe X:ALL, MI:ALL",
        "Parser gói tin X và M",
        "Bắt lỗi ngắt kết nối"
    ])

    # RAM Store Trung Tâm (Hub) với màu Accent nổi bật
    draw_card(35.0, 72.5, 30.0, 22.0, "IN-MEMORY RAM STORE", "MarketStateStore", [
        "700+ Cổ phiếu (HOSE/HNX/UPCoM)",
        "Độ rộng: Trần/Tăng/TC/Giảm/Sàn",
        "Thanh khoản GTGD & KLGD",
        "Thread-Safe Mutex Lock"
    ], is_hub=True)

    draw_card(68.0, 73.5, 26.5, 20.0, "SOCKET BROADCASTER", "WebSocket Hub", [
        "Phát sóng TICK thời gian thực",
        "Đẩy INDEX_UPDATE định kỳ",
        "Gửi SNAPSHOT khi kết nối"
    ])

    # ═══════════════════════════════════════════════════════════════════
    # SECTION 4: TẦNG MÁY CHỦ WEB (app.py) (y: 41 -> 64, h: 23)
    # ═══════════════════════════════════════════════════════════════════
    draw_section(3, 41, 94, 23, "4. TẦNG MÁY CHỦ WEB & PHÂN PHỐI (aiohttp Server :8050)")

    draw_card(6.5, 43.0, 41.0, 16.0, "REST & CONTROLLER", "HTTP REST & Auto-Restart", [
        "GET /  |  /api/heatmap  |  /api/indices",
        "1-Click Play Restart (Kill port 8050)",
        "Thoát Ctrl+C tức thời (SIGINT 0.05s)"
    ])

    draw_card(52.5, 43.0, 41.0, 16.0, "WEBSOCKET ENDPOINT", "Route /ws (Two-Way)", [
        "Bắt tay Client WebSocket",
        "Gửi trọn bộ SNAPSHOT khi mở trang",
        "Truyền phát luồng Tick giá tức thì"
    ])

    # ═══════════════════════════════════════════════════════════════════
    # SECTION 5: TẦNG TRÌNH DUYỆT CLIENT (bauhaus-ui.html) (y: 6 -> 34, h: 28)
    # ═══════════════════════════════════════════════════════════════════
    draw_section(3, 6, 94, 28, "5. TẦNG TRÌNH DUYỆT CLIENT (bauhaus-ui.html)")

    draw_card(5.5, 8.0, 42.0, 22.0, "LEFT PANEL / DRAWER", "Bảng Thống Kê & Chỉ Số Phụ", [
        "3 Chỉ số sàn: VN-Index, HNX, UPCoM",
        "Thanh tỉ lệ độ rộng: Tăng / Đứng / Giảm",
        "Top 6 dòng tiền ngành dẫn dắt thị trường",
        "Live Inspector: Soi chi tiết mã tức thời",
        "Responsive Drawer: Trượt ẩn khi mở nửa màn hình"
    ])

    draw_card(52.5, 8.0, 42.0, 22.0, "MAIN CANVAS (100% FOCUS)", "Bản Đồ Nhiệt ECharts Treemap", [
        "100% Trọng tâm màn hình, không bị che khuất",
        "Font Be Vietnam Pro sắc nét chuẩn tiếng Việt",
        "Màu phẳng chuẩn Vietstock/SSI (Tím/Xanh/Vàng/Đỏ/Lơ)",
        "Hook ZRender căn giữa Centroid, ẩn chữ ô nhỏ",
        "Chế độ: FASTCONNECT LIVE / POLLING LIVE"
    ])

    # ═══════════════════════════════════════════════════════════════════
    # CÁC MŨI TÊN ĐỊNH TUYẾN THẲNG ĐỨNG (CÓ BOX NHÃN 100% SOLID)
    # ═══════════════════════════════════════════════════════════════════
    # Section 1 -> Section 2 (Khoảng cách y: 141.5 -> 127.5)
    draw_arrow((15.7, 141.5), (15.7, 127.5), label="Xác thực RSA", label_pos=0.5)
    draw_arrow((38.4, 141.5), (50.0, 127.5), label="Snapshot REST", label_pos=0.5)
    draw_arrow((61.2, 141.5), (61.2, 94.5), label="SignalR X:ALL", label_pos=0.5, offset_x=12)
    draw_arrow((84.0, 141.5), (80.7, 127.5), label="15 Nhóm ngành", label_pos=0.5)

    # Section 2 -> Section 3 (Khoảng cách y: 107.5 -> 94.5)
    draw_arrow((50.0, 107.5), (50.0, 94.5), label="Nạp Snapshot vào RAM", label_pos=0.5)

    # Section 3 -> Section 4 (Khoảng cách y: 72.5 -> 59.0)
    draw_arrow((40.0, 72.5), (27.0, 59.0), label="Truy xuất REST", label_pos=0.5)
    draw_arrow((60.0, 72.5), (73.0, 59.0), label="Đẩy Tick Realtime", label_pos=0.5)

    # Section 4 -> Section 5 (Khoảng cách y: 43.0 -> 30.0)
    draw_arrow((27.0, 43.0), (26.5, 30.0), label="HTTP REST (0ms khởi tạo)", label_pos=0.5)
    draw_arrow((73.0, 43.0), (73.5, 30.0), label="WebSocket /ws (Tick sống)", label_pos=0.5)

    # ─── 7. LƯU ẢNH RA FILE VỚI ĐỘ PHÂN GIẢI CAO 300 DPI ───
    out_dir = Path(__file__).resolve().parent
    out_png = out_dir / "market_heatmap_neo_light.png"

    plt.savefig(out_png, format='png', dpi=300, bbox_inches='tight', pad_inches=0.18, facecolor=c_canvas)
    plt.close()

    print(f"🎉 Đã xuất thành công duy nhất 1 file ảnh:")
    print(f"   - PNG (300 DPI): {out_png.resolve()}")

if __name__ == '__main__':
    # Chỉ tạo duy nhất 1 hình ảnh market_heatmap_neo_light.png
    generate_diagram(theme="neo-light")





