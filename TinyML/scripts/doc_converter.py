#!/usr/bin/env python3
"""
doc_converter.py - Tự động chuyển đổi tài liệu đa định dạng (PDF, DOCX, PPTX) sang Markdown
Sử dụng Docling engine qua uv.
"""

import sys
import subprocess
from pathlib import Path

def convert_document(input_file: str, output_dir: str = None, to_format: str = "md"):
    inp = Path(input_file).resolve()
    if not inp.exists():
        print(f"Error: File không tồn tại: {inp}")
        sys.exit(1)
        
    out = Path(output_dir).resolve() if output_dir else inp.parent
    out.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        r"C:\Users\HieuVi\.local\bin\uv.exe", "tool", "run", "docling",
        "convert", str(inp),
        "--to", to_format,
        "--output", str(out),
        "--device", "cpu"
    ]
    
    print(f"[*] Đang chuyển đổi: {inp.name} -> {to_format} tại {out}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[+] Thành công! File kết quả nằm tại: {out}")
    else:
        print(f"[-] Thất bại: {res.stderr}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cách sử dụng: python doc_converter.py <đường_dẫn_tài_liệu> [thư_mục_xuất] [định_dạng: md|json|html]")
        print("Ví dụ: python doc_converter.py docs/PHAT_BIEU_BAI_TOAN.docx docs/ md")
        sys.exit(1)
        
    in_file = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else None
    fmt = sys.argv[3] if len(sys.argv) > 3 else "md"
    convert_document(in_file, out_dir, fmt)
