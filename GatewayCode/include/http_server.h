#ifndef HTTP_SERVER_H
#define HTTP_SERVER_H

#include <string>
#include <functional>
#include <atomic>
#include <thread>
#include <map>

// Cấu trúc Request HTTP cơ bản
struct HttpRequest {
    std::string method;  // "GET", "POST", "OPTIONS"
    std::string path;    // "/api/status", "/api/node/trigger", ...
    std::string body;
    std::map<std::string, std::string> headers;
};

// Cấu trúc Response HTTP
struct HttpResponse {
    int statusCode = 200;
    std::string contentType = "application/json";
    std::string body = "{}";
};

class HttpServer {
public:
    HttpServer(int port = 8080);
    ~HttpServer();

    // Thiết lập các hàm callback xử lý REST API
    void setStatusHandler(std::function<std::string()> handler) { m_statusHandler = handler; }
    void setSessionHandler(std::function<bool(const std::string&, std::string&)> handler) { m_sessionHandler = handler; }
    void setTriggerHandler(std::function<bool(const std::string&, const std::string&, std::string&)> handler) { m_triggerHandler = handler; }
    void setConfigHandler(std::function<bool(char, double, std::string&)> handler) { m_configHandler = handler; }
    void setPingHandler(std::function<bool(const std::string&, std::string&)> handler) { m_pingHandler = handler; }

    bool start();
    void stop();

private:
    void serverLoop();
    void handleClient(int clientSocket);
    HttpResponse processRequest(const HttpRequest& req);

    int m_port;
    int m_serverFd;
    std::atomic<bool> m_running;
    std::thread m_thread;

    std::function<std::string()> m_statusHandler;
    std::function<bool(const std::string&, std::string&)> m_sessionHandler;
    std::function<bool(const std::string&, const std::string&, std::string&)> m_triggerHandler;
    std::function<bool(char, double, std::string&)> m_configHandler;
    std::function<bool(const std::string&, std::string&)> m_pingHandler;
};

#endif // HTTP_SERVER_H
