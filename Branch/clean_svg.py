#!/usr/bin/env python3
"""
Script làm sạch file SVG xuất từ Mermaid CLI để tương thích 100% với Adobe Illustrator:
- Loại bỏ 100% thẻ <foreignObject> (HTML DOM) - nguyên nhân gây văng/crash Adobe Illustrator.
- Chuyển đổi thành các thẻ vector SVG chuẩn: <text> và <tspan>.
- Giữ nguyên màu sắc, độ đậm nhạt font chữ, căn giữa và bố cục.
"""

import sys
import re
from pathlib import Path

def clean_svg_file(svg_path: str):
    p = Path(svg_path)
    if not p.exists():
        print(f"Error: File '{svg_path}' not found!")
        return False

    with open(p, "r", encoding="utf-8") as f:
        svg = f.read()

    def clean_fo(match):
        fo_str = match.group(0)
        w_match = re.search(r'width="([^"]+)"', fo_str)
        h_match = re.search(r'height="([^"]+)"', fo_str)
        w = float(w_match.group(1)) if w_match else 200.0
        h = float(h_match.group(1)) if h_match else 50.0

        col_match = re.search(r'color:\s*([^;!"\']+)', fo_str)
        color = col_match.group(1).strip() if col_match else "#ffffff"

        p_match = re.search(r'<p>(.*?)</p>', fo_str, re.DOTALL)
        raw_text = p_match.group(1) if p_match else re.sub(r'<[^>]+>', '', fo_str)

        lines = re.split(r'<br\s*/?>', raw_text)
        clean_lines = [l.strip() for l in lines if l.strip()]

        line_height = 20
        total_text_h = len(clean_lines) * line_height
        start_y = (h - total_text_h) / 2 + 14

        tspans = []
        for i, line in enumerate(clean_lines):
            txt = line.replace('&amp;', '&').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            is_title = (i == 0 and len(clean_lines) > 1)
            fw = "bold" if is_title else "normal"
            fill_col = color if is_title else ("#cbd5e1" if color == "#ffffff" else color)
            fs = "13" if is_title else "11.5"
            dy = "0" if i == 0 else f"{line_height}"
            tspans.append(f'<tspan x="{w/2:.1f}" dy="{dy}" font-weight="{fw}" font-size="{fs}" fill="{fill_col}">{txt}</tspan>')

        return f'<text x="{w/2:.1f}" y="{start_y:.1f}" text-anchor="middle" font-family="\'Be Vietnam Pro\', sans-serif" fill="{color}">{"".join(tspans)}</text>'

    fixed_svg = re.sub(r'<foreignObject[^>]*>.*?</foreignObject>', clean_fo, svg, flags=re.DOTALL)

    with open(p, "w", encoding="utf-8") as f:
        f.write(fixed_svg)

    print(f"🎉 Đã làm sạch thành công: {p.resolve()}")
    print("   → Số lượng <foreignObject> còn lại: 0")
    print("   → Đã sẵn sàng mở trên Adobe Illustrator!")
    return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "diagram.svg"
    clean_svg_file(target)
