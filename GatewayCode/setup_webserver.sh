#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# SCRIPT CÀI ĐẶT & THIẾT LẬP NGINX WEBSERVER CHO LORA GATEWAY TRÊN CM4
# ═══════════════════════════════════════════════════════════════════════════

set -e

echo "=========================================================="
echo "   THIẾT LẬP NGINX WEBSERVER CHO LORAWAN GATEWAY (CM4)    "
echo "=========================================================="

# Kiểm tra quyền root
if [ "$EUID" -ne 0 ]; then
  echo "[LỖI] Vui lòng chạy script này với quyền sudo: sudo ./setup_webserver.sh"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Cài đặt Nginx nếu chưa có
echo "[1/5] Đang kiểm tra và cài đặt Nginx..."
if ! command -v nginx >/dev/null 2>&1; then
    apt-get update
    apt-get install -y nginx
fi

# 2. Tạo thư mục Web root và sao chép giao diện Dashboard
echo "[2/5] Đang sao chép giao diện Web Dashboard vào /var/www/loragw..."
mkdir -p /var/www/loragw
cp -r "${SCRIPT_DIR}/web/"* /var/www/loragw/
chown -R www-data:www-data /var/www/loragw
chmod -R 755 /var/www/loragw

# 3. Cài đặt file cấu hình Nginx Virtual Host
echo "[3/5] Đang cấu hình Nginx (Port 80 -> Proxy tới C++ Daemon :8080)..."
cp "${SCRIPT_DIR}/nginx/loragw.conf" /etc/nginx/sites-available/loragw.conf

# Vô hiệu hóa cấu hình mặc định cũ của Nginx để tránh xung đột Port 80
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm -f /etc/nginx/sites-enabled/default
fi

# Kích hoạt site loragw
ln -sf /etc/nginx/sites-available/loragw.conf /etc/nginx/sites-enabled/loragw.conf

# 4. Kiểm tra cú pháp cấu hình Nginx
echo "[4/5] Đang kiểm tra cú pháp Nginx..."
nginx -t

# 5. Khởi động lại Nginx
echo "[5/5] Đang khởi động lại dịch vụ Nginx..."
systemctl restart nginx
systemctl enable nginx

# Lấy địa chỉ IP mạng Wi-Fi hiện tại của CM4
WIFI_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=========================================================="
echo "   CÀI ĐẶT THÀNH CÔNG NGINX WEBSERVER CHO LORA GATEWAY!   "
echo "=========================================================="
echo "  • Cổng truy cập : 80 (HTTP chuẩn, không cần gõ cổng)"
echo "  • Địa chỉ Web   : http://${WIFI_IP}/"
echo "  • Dự phòng cục bộ: http://${WIFI_IP}:8080/"
echo ""
echo "HƯỚNG DẪN KHỞI CHẠY GATEWAY DAEMON:"
echo "  1. Biên dịch Gateway: make clean && make"
echo "  2. Chạy Gateway     : sudo ./lora_gw_3ch"
echo "  3. Mở trình duyệt trên máy tính/điện thoại cùng mạng Wi-Fi:"
echo "     ==> Truy cập: http://${WIFI_IP}/"
echo "=========================================================="
