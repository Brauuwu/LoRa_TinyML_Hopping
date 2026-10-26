#include "http_server.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fstream>
#include <sstream>
#include <iostream>
#include <algorithm>

HttpServer::HttpServer(int port)
    : m_port(port), m_serverFd(-1), m_running(false) {}

HttpServer::~HttpServer() {
    stop();
}

bool HttpServer::start() {
    m_serverFd = socket(AF_INET, SOCK_STREAM, 0);
    if (m_serverFd < 0) {
        perror("[HTTP] Không thể tạo socket");
        return false;
    }

    int opt = 1;
    setsockopt(m_serverFd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in address;
    memset(&address, 0, sizeof(address));
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY; // Lắng nghe trên mọi interface (0.0.0.0)
    address.sin_port = htons(m_port);

    if (bind(m_serverFd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        perror("[HTTP] Lỗi bind cổng");
        close(m_serverFd);
        m_serverFd = -1;
        return false;
    }

    if (listen(m_serverFd, 32) < 0) {
        perror("[HTTP] Lỗi listen");
        close(m_serverFd);
        m_serverFd = -1;
        return false;
    }

    m_running = true;
    m_thread = std::thread(&HttpServer::serverLoop, this);
    printf("[HTTP] Webserver Daemon đã khởi động trên cổng %d (http://0.0.0.0:%d)\n", m_port, m_port);
    return true;
}

void HttpServer::stop() {
    if (m_running.load()) {
        m_running = false;
        if (m_serverFd >= 0) {
            shutdown(m_serverFd, SHUT_RDWR);
            close(m_serverFd);
            m_serverFd = -1;
        }
        if (m_thread.joinable()) {
            m_thread.join();
        }
        printf("[HTTP] Webserver Daemon đã tắt.\n");
    }
}

void HttpServer::serverLoop() {
    while (m_running.load()) {
        struct sockaddr_in clientAddr;
        socklen_t clientLen = sizeof(clientAddr);
        int clientFd = accept(m_serverFd, (struct sockaddr*)&clientAddr, &clientLen);

        if (clientFd < 0) {
            if (!m_running.load()) break;
            usleep(10000);
            continue;
        }

        // Xử lý client trên thread độc lập (detach)
        std::thread([this, clientFd]() {
            this->handleClient(clientFd);
        }).detach();
    }
}

// Hàm đọc file tĩnh từ thư mục web/
static bool readStaticFile(const std::string& relativePath, std::string& outContent, std::string& outMime) {
    std::string filePath = "web/" + relativePath;
    if (relativePath == "" || relativePath == "/") {
        filePath = "web/index.html";
        outMime = "text/html; charset=utf-8";
    } else if (relativePath.find(".css") != std::string::npos) {
        outMime = "text/css; charset=utf-8";
    } else if (relativePath.find(".js") != std::string::npos) {
        outMime = "application/javascript; charset=utf-8";
    } else if (relativePath.find(".json") != std::string::npos) {
        outMime = "application/json; charset=utf-8";
    } else {
        outMime = "text/plain; charset=utf-8";
    }

    std::ifstream file(filePath, std::ios::binary);
    if (!file.is_open()) {
        // Thử tìm tại /var/www/loragw/ nếu web/ cục bộ không có
        std::string fallbackPath = "/var/www/loragw/" + relativePath;
        if (relativePath == "" || relativePath == "/") fallbackPath = "/var/www/loragw/index.html";
        file.open(fallbackPath, std::ios::binary);
        if (!file.is_open()) return false;
    }

    std::stringstream ss;
    ss << file.rdbuf();
    outContent = ss.str();
    return true;
}

// Trích xuất giá trị trường JSON đơn giản từ chuỗi raw
static std::string extractJsonField(const std::string& json, const std::string& key) {
    std::string needle = "\"" + key + "\"";
    size_t pos = json.find(needle);
    if (pos == std::string::npos) return "";

    pos += needle.length();
    while (pos < json.length() && (json[pos] == ' ' || json[pos] == ':' || json[pos] == '\t')) pos++;

    if (pos >= json.length()) return "";

    if (json[pos] == '\"') {
        pos++;
        size_t endPos = json.find('\"', pos);
        if (endPos == std::string::npos) return "";
        return json.substr(pos, endPos - pos);
    } else {
        size_t endPos = json.find_first_of(",}\r\n ", pos);
        if (endPos == std::string::npos) endPos = json.length();
        return json.substr(pos, endPos - pos);
    }
}

HttpResponse HttpServer::processRequest(const HttpRequest& req) {
    HttpResponse res;

    // 1. OPTIONS CORS Preflight
    if (req.method == "OPTIONS") {
        res.statusCode = 204;
        res.contentType = "text/plain";
        res.body = "";
        return res;
    }

    // 2. GET /api/status - Trạng thái Gateway, các Node, và Kênh
    if (req.method == "GET" && (req.path == "/api/status" || req.path == "/api/status/")) {
        res.statusCode = 200;
        res.contentType = "application/json; charset=utf-8";
        if (m_statusHandler) {
            res.body = m_statusHandler();
        } else {
            res.body = "{\"error\": \"No status handler\"}";
        }
        return res;
    }

    // 3. POST /api/session - Đổi tên phiên đo đạc (Session Name)
    if (req.method == "POST" && (req.path == "/api/session" || req.path == "/api/session/")) {
        std::string name = extractJsonField(req.body, "name");
        std::string msg;
        bool ok = false;
        if (m_sessionHandler && !name.empty()) {
            ok = m_sessionHandler(name, msg);
        } else {
            msg = "Thiếu tên phiên đo 'name'";
        }
        res.statusCode = ok ? 200 : 400;
        res.contentType = "application/json; charset=utf-8";
        res.body = "{\"success\": " + std::string(ok ? "true" : "false") +
                   ", \"message\": \"" + msg + "\", \"session\": \"" + name + "\"}";
        return res;
    }

    // 4. POST /api/node/trigger - Kích hoạt phát (START) hoặc Dừng/Reset (STOP)
    if (req.method == "POST" && (req.path == "/api/node/trigger" || req.path == "/api/node/trigger/")) {
        std::string target = extractJsonField(req.body, "target"); // "ALL", "A", "B", "A,B", ...
        std::string action = extractJsonField(req.body, "action"); // "START" hoặc "STOP"
        if (target.empty()) target = "ALL";
        if (action.empty()) action = "START";

        std::string msg;
        bool ok = false;
        if (m_triggerHandler) {
            ok = m_triggerHandler(target, action, msg);
        }
        res.statusCode = ok ? 200 : 500;
        res.contentType = "application/json; charset=utf-8";
        res.body = "{\"success\": " + std::string(ok ? "true" : "false") +
                   ", \"target\": \"" + target + "\", \"action\": \"" + action +
                   "\", \"message\": \"" + msg + "\"}";
        return res;
    }

    // 5. POST /api/node/config - Cấu hình tần số OTA cho Node
    if (req.method == "POST" && (req.path == "/api/node/config" || req.path == "/api/node/config/")) {
        std::string nodeStr = extractJsonField(req.body, "node"); // "A", "B", "C"
        std::string freqStr = extractJsonField(req.body, "freq"); // "433.175"
        char nodeChar = (!nodeStr.empty()) ? nodeStr[0] : 'A';
        double freqVal = (!freqStr.empty()) ? atof(freqStr.c_str()) : 433.175;

        std::string msg;
        bool ok = false;
        if (m_configHandler) {
            ok = m_configHandler(nodeChar, freqVal, msg);
        }
        res.statusCode = ok ? 200 : 500;
        res.contentType = "application/json; charset=utf-8";
        res.body = "{\"success\": " + std::string(ok ? "true" : "false") +
                   ", \"node\": \"" + std::string(1, nodeChar) + "\", \"freq\": " +
                   std::to_string(freqVal) + ", \"message\": \"" + msg + "\"}";
        return res;
    }

    // 6. POST /api/node/ping - Kiểm tra trạng thái Online / Offline
    if (req.method == "POST" && (req.path == "/api/node/ping" || req.path == "/api/node/ping/")) {
        std::string target = extractJsonField(req.body, "target");
        if (target.empty()) target = "ALL";
        std::string msg;
        bool ok = false;
        if (m_pingHandler) {
            ok = m_pingHandler(target, msg);
        }
        res.statusCode = ok ? 200 : 500;
        res.contentType = "application/json; charset=utf-8";
        res.body = "{\"success\": " + std::string(ok ? "true" : "false") +
                   ", \"message\": \"" + msg + "\"}";
        return res;
    }

    // 7. Fallback: Trả về file tĩnh Web UI nếu truy cập trực tiếp cổng 8080
    std::string staticContent, mimeType;
    std::string relPath = req.path;
    if (relPath.length() > 0 && relPath[0] == '/') relPath = relPath.substr(1);
    if (readStaticFile(relPath, staticContent, mimeType)) {
        res.statusCode = 200;
        res.contentType = mimeType;
        res.body = staticContent;
        return res;
    }

    // 8. 404 Not Found
    res.statusCode = 404;
    res.contentType = "application/json; charset=utf-8";
    res.body = "{\"error\": \"Endpoint not found\"}";
    return res;
}

void HttpServer::handleClient(int clientFd) {
    char buffer[4096];
    int bytesRead = recv(clientFd, buffer, sizeof(buffer) - 1, 0);
    if (bytesRead <= 0) {
        close(clientFd);
        return;
    }
    buffer[bytesRead] = '\0';

    HttpRequest req;
    char method[16], path[256], proto[16];
    if (sscanf(buffer, "%15s %255s %15s", method, path, proto) < 2) {
        close(clientFd);
        return;
    }
    req.method = method;
    req.path = path;

    // Tách body (nếu có sau \r\n\r\n)
    const char* bodyStart = strstr(buffer, "\r\n\r\n");
    if (bodyStart) {
        req.body = bodyStart + 4;
    }

    HttpResponse res = processRequest(req);

    // Gửi Header và Body
    std::string responseStr;
    responseStr += "HTTP/1.1 " + std::to_string(res.statusCode) + " OK\r\n";
    responseStr += "Content-Type: " + res.contentType + "\r\n";
    responseStr += "Content-Length: " + std::to_string(res.body.length()) + "\r\n";
    responseStr += "Access-Control-Allow-Origin: *\r\n";
    responseStr += "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n";
    responseStr += "Access-Control-Allow-Headers: Content-Type\r\n";
    responseStr += "Connection: close\r\n\r\n";
    responseStr += res.body;

    send(clientFd, responseStr.c_str(), responseStr.length(), 0);
    close(clientFd);
}
