/* ── LoRaWAN AI-Edge Gateway Web Controller App ──────────────────────────── */

let g_currentSessionName = "";
let g_isSessionInputFocused = false;

// Format Uptime (seconds -> HH:MM:SS)
function formatUptime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return [h, m, s].map(v => v < 10 ? "0" + v : v).join(":");
}

// Tính toán mức sóng 4 vạch từ RSSI
function getSignalBarsClass(rssi) {
  if (rssi >= -75) return "level-4";
  if (rssi >= -95) return "level-3";
  if (rssi >= -110) return "level-2";
  return "level-1";
}

// Hiển thị thông báo Toast
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ── Hàm cập nhật dữ liệu định kỳ từ Gateway (Polling /api/status) ───────────
async function fetchGatewayStatus() {
  try {
    const res = await fetch("/api/status", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    document.getElementById("gw-status-text").textContent = "DISCONNECTED";
    const pill = document.querySelector(".status-pill");
    if (pill) {
      pill.className = "status-pill";
      pill.style.background = "rgba(239, 68, 68, 0.2)";
      pill.style.color = "#f87171";
      pill.style.border = "1px solid rgba(239, 68, 68, 0.4)";
    }
  }
}

// ── Render Giao diện từ dữ liệu JSON ─────────────────────────────────────────
function renderDashboard(data) {
  // 1. Gateway Status & Uptime
  document.getElementById("gw-status-text").textContent = "GATEWAY ONLINE";
  const pill = document.querySelector(".status-pill");
  if (pill) {
    pill.className = "status-pill status-online";
    pill.style.background = "";
    pill.style.color = "";
    pill.style.border = "";
  }
  document.getElementById("gw-uptime").textContent = formatUptime(data.gateway.uptime_sec || 0);

  // 2. Session Name & Paths
  if (data.gateway.session_name) {
    g_currentSessionName = data.gateway.session_name;
    const sessionInput = document.getElementById("session-name-input");
    if (!g_isSessionInputFocused && sessionInput) {
      sessionInput.value = g_currentSessionName;
    }
    document.getElementById("path-csv").textContent = `csv/${g_currentSessionName}.csv`;
    document.getElementById("path-txt").textContent = `logs/${g_currentSessionName}.txt`;
  }

  // 3. Stats Counters
  document.getElementById("stat-total-packets").textContent = data.gateway.total_packets || 0;
  document.getElementById("stat-control-packets").textContent = data.gateway.control_packets || 0;
  document.getElementById("stat-crc-errors").textContent = data.gateway.total_crc_errors || 0;

  // Channels distribution
  if (data.gateway.channels && data.gateway.channels.length >= 3) {
    document.getElementById("ch1-pkts").textContent = `${data.gateway.channels[0].packets} gói`;
    document.getElementById("ch2-pkts").textContent = `${data.gateway.channels[1].packets} gói`;
    document.getElementById("ch3-pkts").textContent = `${data.gateway.channels[2].packets} gói`;
  }

  // 4. Render Các Node
  if (data.nodes) {
    data.nodes.forEach(node => {
      const id = node.id;
      // Online status badge
      const statusBadge = document.getElementById(`badge-status-${id}`);
      if (statusBadge) {
        if (node.online) {
          statusBadge.className = "node-status-badge online";
          statusBadge.querySelector(".status-text").textContent = "ONLINE";
        } else {
          statusBadge.className = "node-status-badge offline";
          statusBadge.querySelector(".status-text").textContent = "OFFLINE";
        }
      }

      // State pill
      const statePill = document.getElementById(`state-pill-${id}`);
      if (statePill) {
        let text = "CHỜ LỆNH";
        let cls = "node-state-pill";
        if (node.state === "TX") {
          text = "ĐANG PHÁT";
          cls = "node-state-pill tx";
        } else if (node.state === "FINISHED" || node.state === "DONE") {
          text = "HOÀN THÀNH";
          cls = "node-state-pill done";
        }
        statePill.textContent = text;
        statePill.className = cls;
      }

      // Frequency
      const freqElem = document.getElementById(`freq-${id}`);
      if (freqElem) {
        freqElem.textContent = `${Number(node.frequency).toFixed(3)} MHz (CH${node.channel_id || 1})`;
      }

      // RSSI & Signal Bars
      const rssiElem = document.getElementById(`rssi-${id}`);
      const barsElem = document.getElementById(`sig-bars-${id}`);
      if (rssiElem) {
        if (node.online && node.rssi > -150) {
          rssiElem.textContent = `${node.rssi} dBm`;
          if (barsElem) barsElem.className = `signal-bars ${getSignalBarsClass(node.rssi)}`;
        } else {
          rssiElem.textContent = "-- dBm";
          if (barsElem) barsElem.className = "signal-bars";
        }
      }

      // SNR
      const snrElem = document.getElementById(`snr-${id}`);
      if (snrElem) {
        snrElem.textContent = (node.online && node.rssi > -150) ? `${Number(node.snr).toFixed(1)} dB` : "-- dB";
      }

      // Packets count
      const pktsElem = document.getElementById(`pkts-${id}`);
      if (pktsElem) {
        pktsElem.textContent = `${node.packets || 0} / 600`;
      }

      // OTA Confirmed status
      const otaBadge = document.getElementById(`ota-badge-${id}`);
      if (otaBadge) {
        if (node.cfg_confirmed) {
          otaBadge.className = "ota-badge stable";
          otaBadge.textContent = "ỔN ĐỊNH ✓";
        } else {
          otaBadge.className = "ota-badge pending";
          otaBadge.textContent = "CHỜ XÁC NHẬN ⏳";
        }
      }
    });
  }

  // 5. Render Recent Events Log
  if (data.recent_events) {
    const terminal = document.getElementById("terminal-body");
    const autoscroll = document.getElementById("chk-autoscroll").checked;

    terminal.innerHTML = "";
    data.recent_events.forEach(ev => {
      const line = document.createElement("div");
      let typeClass = "sys";
      let prefix = "[SYS]";

      if (ev.type === "DATA") {
        typeClass = "data";
        prefix = `[DATA ${ev.node} #${ev.pkt_id}]`;
      } else if (ev.type === "DOWNLINK") {
        typeClass = "downlink";
        prefix = "[DOWNLINK]";
      } else if (ev.type === "CTRL") {
        typeClass = "ctrl";
        prefix = "[CONTROL]";
      } else if (ev.type === "OTA") {
        typeClass = "ota";
        prefix = "[OTA CONFIG]";
      }

      line.className = `log-line ${typeClass}`;
      let text = `${ev.time} ${prefix} ${ev.msg}`;
      if (ev.type === "DATA") {
        text += ` | ${Number(ev.freq).toFixed(3)}MHz | ${ev.size}B | RSSI:${ev.rssi} SNR:${Number(ev.snr).toFixed(1)}`;
      }
      line.textContent = text;
      terminal.appendChild(line);
    });

    if (autoscroll) {
      terminal.scrollTop = terminal.scrollHeight;
    }
  }
}

// ── Tác Vụ 1: Đổi Tên Phiên Đo Đạc (Session Renaming) ────────────────────────
async function applySessionName() {
  const input = document.getElementById("session-name-input");
  const newName = input.value.trim();
  if (!newName) {
    showToast("Vui lòng nhập tên phiên đo đạc!", "error");
    return;
  }

  try {
    const res = await fetch("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newName })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Đã đổi phiên đo thành công: "${newName}"`, "success");
      g_currentSessionName = newName;
      document.getElementById("path-csv").textContent = `csv/${newName}.csv`;
      document.getElementById("path-txt").textContent = `logs/${newName}.txt`;
    } else {
      showToast(`Lỗi: ${data.message}`, "error");
    }
  } catch (err) {
    showToast("Không thể kết nối tới Gateway!", "error");
  }
}

// ── Tác Vụ 2: Kích Hoạt / Dừng Các Node Được Chọn (Multi-Node Trigger) ───────
async function triggerSelectedNodes(action) {
  const checkedBoxes = document.querySelectorAll(".node-select-chk:checked");
  if (checkedBoxes.length === 0) {
    showToast("Vui lòng tích chọn ít nhất 1 Node để phát!", "error");
    return;
  }

  const selectedNodes = Array.from(checkedBoxes).map(cb => cb.value).join(",");
  await triggerNode(selectedNodes, action);
}

// ── Tác Vụ 3: Phát Lệnh Downlink Tới Node (START hoặc STOP) ─────────────────
async function triggerNode(target, action) {
  try {
    const res = await fetch("/api/node/trigger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target: target, action: action })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, action === "START" ? "success" : "info");
    } else {
      showToast(`Lỗi: ${data.message}`, "error");
    }
  } catch (err) {
    showToast("Không thể gửi lệnh tới Gateway!", "error");
  }
}

// ── Tác Vụ 4: Cấu Hình Tần Số OTA (OTA Frequency Tuning) ───────────────────
async function applyOtaConfig(node) {
  const select = document.getElementById(`select-freq-${node}`);
  const freq = parseFloat(select.value);

  const badge = document.getElementById(`ota-badge-${node}`);
  if (badge) {
    badge.className = "ota-badge pending";
    badge.textContent = "ĐANG GỬI ⏳";
  }

  try {
    const res = await fetch("/api/node/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ node: node, freq: freq })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Đã gửi lệnh đổi tần số Node ${node} sang ${freq} MHz. Chờ xác nhận...`, "info");
    } else {
      showToast(`Lỗi cấu hình: ${data.message}`, "error");
    }
  } catch (err) {
    showToast("Không thể gửi yêu cầu cấu hình OTA!", "error");
  }
}

// ── Tác Vụ 5: Ping Kiểm Tra Online / Offline ────────────────────────────────
async function pingNodes(target = "ALL") {
  try {
    const res = await fetch("/api/node/ping", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target: target })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Đã gửi yêu cầu Ping (${target}). Đang chờ phản hồi...`, "info");
    }
  } catch (err) {
    showToast("Không thể gửi yêu cầu Ping!", "error");
  }
}

// ── Tác Vụ Chọn / Bỏ Chọn Tất Cả Checkbox ───────────────────────────────────
function toggleSelectAllNodes(checked) {
  const checkboxes = document.querySelectorAll(".node-select-chk");
  checkboxes.forEach(cb => cb.checked = checked);
}

// ── Xóa Nhật Ký Console ────────────────────────────────────────────────────
function clearConsole() {
  document.getElementById("terminal-body").innerHTML = "";
  showToast("Đã xóa nhật ký giao diện.", "info");
}

// Khởi tạo các sự kiện khi tải trang
document.addEventListener("DOMContentLoaded", () => {
  const sessionInput = document.getElementById("session-name-input");
  if (sessionInput) {
    sessionInput.addEventListener("focus", () => g_isSessionInputFocused = true);
    sessionInput.addEventListener("blur", () => g_isSessionInputFocused = false);
    sessionInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") applySessionName();
    });
  }

  // Bắt đầu chu kỳ thăm dò trạng thái mỗi 1 giây
  fetchGatewayStatus();
  setInterval(fetchGatewayStatus, 1000);
});
