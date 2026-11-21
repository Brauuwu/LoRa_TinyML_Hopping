/* ═══════════════════════════════════════════════════════════════════════════
   LoRa 433 MHz Web Serial & The Things Stack Gateway Dashboard — app.js
   Enhanced with UI/UX Pro Max: Realtime Signal Meter, Quick Filter & Export
   ═══════════════════════════════════════════════════════════════════════════ */

(() => {
  "use strict";

  // ── DOM References ───────────────────────────────────────────────────────
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => document.querySelectorAll(s);

  // Header & Status
  const btnConnect      = $("#btn-connect");
  const statusBadge     = $("#status-badge");
  const wifiBadge       = $("#wifi-badge");
  const valHeaderEui    = $("#val-header-eui");

  // Spectrum channel pills
  const channelPills    = $$(".channel-pill");

  // Stats
  const valPackets      = $("#val-packets");
  const valFwd          = $("#val-fwd");
  const valRssi         = $("#val-rssi");
  const valSnr          = $("#val-snr");
  const valFerr         = $("#val-ferr");
  const signalMeter     = $("#signal-meter");

  // Log Panel
  const logContainer    = $("#log-container");
  const logBody         = $("#log-body");
  const logEmpty        = $("#log-empty");
  const logCount        = $("#log-count");
  const btnScrollBottom = $("#btn-scroll-bottom");
  const chkAutoScroll   = $("#chk-autoscroll");
  const btnClearLog     = $("#btn-clear-log");
  const logSearchInput  = $("#log-search-input");
  const btnExportLog    = $("#btn-export-log");

  // Gateway & TTS panel
  const valGwEui        = $("#val-gw-eui");
  const btnCopyEui      = $("#btn-copy-eui");
  const btnReadGw       = $("#btn-read-gw");
  const ttsForm         = $("#tts-form");
  const ttsServerInput  = $("#tts-server");
  const ttsPortInput    = $("#tts-port");
  const btnSaveTts      = $("#btn-save-tts");
  const btnTriggerAp    = $("#btn-trigger-ap");
  const lblGwStatus     = $("#lbl-gw-status");
  const lblGwIp         = $("#lbl-gw-ip");
  const lblTtsStatus    = $("#lbl-tts-status");
  const lblGwFwd        = $("#lbl-gw-fwd");

  // LoRa Config panel
  const configForm      = $("#config-form");
  const btnApplyCfg     = $("#btn-apply-cfg");
  const btnReadCfg      = $("#btn-read-cfg");
  const presetBtns      = $$(".btn-preset");

  // Chart & Toast
  const chartCanvas     = $("#chart-canvas");
  const toastBox        = $("#toast-container");

  // ── State Variables ──────────────────────────────────────────────────────
  let port = null;
  let reader = null;
  let writer = null;
  let keepReading = false;
  let lineBuffer = "";
  let totalPackets = 0;
  let totalForwarded = 0;

  // Chart rolling window
  const CHART_MAX = 60;
  const rssiData = [];
  const snrData  = [];

  // Memory log store for CSV export
  const packetRecords = [];

  // ── Toast Helper ─────────────────────────────────────────────────────────
  function toast(msg, type = "info", ms = 3500) {
    if (!toastBox) return;
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = msg;
    toastBox.appendChild(el);
    setTimeout(() => {
      el.classList.add("fade-out");
      setTimeout(() => el.remove(), 350);
    }, ms);
  }

  // ── Escape HTML ──────────────────────────────────────────────────────────
  function escHtml(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function nowStr() {
    const d = new Date();
    return d.toTimeString().split(" ")[0] + "." + String(d.getMilliseconds()).padStart(3, "0");
  }

  // ── Web Serial State Helpers ─────────────────────────────────────────────
  function setConnected(connected) {
    if (connected) {
      statusBadge.innerHTML = '<span class="badge-dot"></span> Serial: Connected';
      statusBadge.className = "badge connected";
      btnConnect.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Disconnect`;

      btnApplyCfg.disabled  = false;
      btnReadCfg.disabled   = false;
      btnReadGw.disabled    = false;
      btnSaveTts.disabled   = false;
      btnTriggerAp.disabled = false;
    } else {
      statusBadge.innerHTML = '<span class="badge-dot"></span> Serial: Disconnected';
      statusBadge.className = "badge disconnected";
      btnConnect.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg> Connect Serial`;

      btnApplyCfg.disabled  = true;
      btnReadCfg.disabled   = true;
      btnReadGw.disabled    = true;
      btnSaveTts.disabled   = true;
      btnTriggerAp.disabled = true;
    }
  }

  // ── Serial Connection ────────────────────────────────────────────────────
  async function connectSerial() {
    if (!("serial" in navigator)) {
      toast("Trình duyệt không hỗ trợ Web Serial API. Vui lòng mở bằng Chrome hoặc Edge.", "error");
      return;
    }
    try {
      port = await navigator.serial.requestPort();
      await port.open({ baudRate: 115200 });
      writer = port.writable.getWriter();
      keepReading = true;
      setConnected(true);
      toast("Đã kết nối Serial thành công!", "success");
      readLoop();

      // Query current LoRa and Gateway settings from ESP32
      setTimeout(() => {
        sendCommand({ cmd: "get_cfg" });
        sendCommand({ cmd: "get_gw_info" });
      }, 500);

    } catch (err) {
      if (err.name !== "NotFoundError") {
        toast("Kết nối lỗi: " + err.message, "error");
      }
    }
  }

  async function disconnectSerial() {
    keepReading = false;
    try {
      if (reader) { await reader.cancel(); reader.releaseLock(); reader = null; }
      if (writer) { writer.releaseLock(); writer = null; }
      if (port)   { await port.close(); port = null; }
    } catch (_) { /* already closed */ }
    setConnected(false);
    toast("Đã ngắt kết nối Serial.", "info");
  }

  async function readLoop() {
    const decoder = new TextDecoderStream();
    const readableStreamClosed = port.readable.pipeTo(decoder.writable);
    reader = decoder.readable.getReader();

    try {
      while (keepReading) {
        const { value, done } = await reader.read();
        if (done) break;
        if (value) processChunk(value);
      }
    } catch (err) {
      if (keepReading) toast("Lỗi đọc dữ liệu Serial: " + err.message, "error");
    } finally {
      reader.releaseLock();
      reader = null;
      try { await readableStreamClosed; } catch (_) {}
    }
  }

  function processChunk(chunk) {
    lineBuffer += chunk;
    const lines = lineBuffer.split("\n");
    lineBuffer = lines.pop();
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      parseLine(trimmed);
    }
  }

  // ── JSON Line Dispatcher ─────────────────────────────────────────────────
  function parseLine(line) {
    if (line[0] === "{") {
      try {
        const obj = JSON.parse(line);
        if (obj.type === "rx")           handleRx(obj);
        else if (obj.type === "cfg")     handleCfg(obj);
        else if (obj.type === "gw_info") handleGwInfo(obj);
        else if (obj.type === "wifi_status") handleWifiStatus(obj);
        else if (obj.type === "info")    toast(obj.msg || "", "info");
        else if (obj.type === "err")     handleErr(obj);
        return;
      } catch (_) { /* fallback to plain text */ }
    }

    // Plain line log
    addLogRow({
      pkt: "—",
      ts: nowStr(),
      data: line,
      len: line.length,
      rssi: "",
      snr: "",
      fwd: false
    });
  }

  // ── Signal Strength Meter Helper ─────────────────────────────────────────
  function updateSignalMeter(rssi) {
    if (!signalMeter) return;
    signalMeter.className = "signal-meter";
    if (typeof rssi !== "number") return;

    if (rssi >= -80) {
      signalMeter.classList.add("sig-good");
    } else if (rssi >= -100) {
      signalMeter.classList.add("sig-ok");
    } else if (rssi >= -115) {
      signalMeter.classList.add("sig-weak");
    } else {
      signalMeter.classList.add("sig-bad");
    }
  }

  // ── Incoming LoRa Packet Handler ─────────────────────────────────────────
  function handleRx(obj) {
    totalPackets = obj.pkt || (totalPackets + 1);
    if (obj.fwd != null) totalForwarded = obj.fwd;

    const rssi = obj.rssi ?? "—";
    const snr  = obj.snr  ?? "—";
    const fe   = obj.freqErr ?? "—";

    valPackets.textContent = totalPackets;
    valFwd.textContent     = totalForwarded;
    valRssi.textContent    = typeof rssi === "number" ? rssi.toFixed(1) : rssi;
    valSnr.textContent     = typeof snr  === "number" ? snr.toFixed(2)  : snr;
    valFerr.textContent    = typeof fe   === "number" ? fe.toFixed(1)   : fe;

    // Color coding
    valRssi.className = "stat-value";
    if (typeof rssi === "number") {
      updateSignalMeter(rssi);
      if (rssi > -80)       valRssi.classList.add("rssi-good");
      else if (rssi > -110) valRssi.classList.add("rssi-ok");
      else valRssi.classList.add("rssi-bad");
    }

    valSnr.className = "stat-value";
    if (typeof snr === "number") {
      valSnr.classList.add(snr >= 0 ? "snr-good" : "snr-bad");
    }

    // Highlight current active channel pill if freq reported
    if (obj.freq != null) {
      highlightActiveChannelPill(obj.freq);
    }

    const record = {
      pkt: obj.pkt ?? totalPackets,
      ts: nowStr(),
      data: obj.data ?? "",
      len: obj.len ?? (obj.data ? obj.data.length : 0),
      rssi: typeof rssi === "number" ? rssi.toFixed(1) : rssi,
      snr:  typeof snr  === "number" ? snr.toFixed(2)  : snr,
      fwd: true
    };

    packetRecords.push(record);
    addLogRow(record);

    // Chart trend buffer
    if (typeof rssi === "number") rssiData.push(rssi);
    if (typeof snr  === "number") snrData.push(snr);
    while (rssiData.length > CHART_MAX) rssiData.shift();
    while (snrData.length  > CHART_MAX) snrData.shift();
    drawChart();
  }

  // ── Highlight Active Channel Pill ────────────────────────────────────────
  function highlightActiveChannelPill(freq) {
    const f = parseFloat(freq);
    channelPills.forEach(pill => {
      const pFreq = parseFloat(pill.dataset.freq);
      if (Math.abs(pFreq - f) < 0.05) {
        pill.classList.add("active");
      } else {
        pill.classList.remove("active");
      }
    });
  }

  // ── Config Handler ───────────────────────────────────────────────────────
  function handleCfg(obj) {
    if (obj.freq != null) {
      const freqVal = parseFloat(obj.freq);
      $("#cfg-freq").value = freqVal;
      highlightActiveChannelPill(freqVal);
    }
    if (obj.bw   != null) $("#cfg-bw").value   = obj.bw;
    if (obj.sf   != null) $("#cfg-sf").value   = obj.sf;
    if (obj.cr   != null) $("#cfg-cr").value   = obj.cr;
    if (obj.sw   != null) {
      let swNum = obj.sw;
      if (typeof swNum === "string") swNum = parseInt(swNum, 16);
      $("#cfg-sw").value = swNum;
    }
    if (obj.pwr  != null) $("#cfg-pwr").value  = obj.pwr;
    if (obj.pre  != null) $("#cfg-pre").value  = obj.pre;
    toast("Đã đồng bộ tham số LoRa từ thiết bị.", "success");
  }

  // ── Gateway Info Handler ─────────────────────────────────────────────────
  function handleGwInfo(obj) {
    if (obj.gwEui) {
      valGwEui.textContent     = obj.gwEui;
      valHeaderEui.textContent = obj.gwEui;
    }

    if (obj.server) {
      ttsServerInput.value = obj.server;
      if (lblTtsStatus) lblTtsStatus.textContent = obj.server + (obj.port ? (":" + obj.port) : "");
    }
    if (obj.port) ttsPortInput.value = obj.port;

    if (obj.pkts_rx  != null) valPackets.textContent = obj.pkts_rx;
    if (obj.pkts_fwd != null) {
      valFwd.textContent = obj.pkts_fwd;
      if (lblGwFwd) lblGwFwd.textContent = obj.pkts_fwd;
    }

    lblGwIp.textContent = obj.ip || "—";

    if (obj.wifi_status === "connected") {
      wifiBadge.innerHTML = '<span class="badge-dot"></span> WiFi: ' + (obj.ssid || "Connected");
      wifiBadge.className = "badge connected";
      lblGwStatus.textContent = "Connected (" + (obj.ssid || "") + " · " + (obj.rssi || "") + " dBm)";
    } else if (obj.wifi_status === "ap_mode") {
      wifiBadge.innerHTML = '<span class="badge-dot"></span> AP Mode Active';
      wifiBadge.className = "badge ap_mode";
      lblGwStatus.textContent = "Trạm phát AP: " + (obj.ssid || "LoRa-Gateway-AP");
    } else {
      wifiBadge.innerHTML = '<span class="badge-dot"></span> WiFi: Off';
      wifiBadge.className = "badge disconnected";
      lblGwStatus.textContent = "Chưa kết nối (Nhấn BOOT để bật AP)";
    }
  }

  // ── WiFi Status Message Handler ──────────────────────────────────────────
  function handleWifiStatus(obj) {
    if (obj.status === "connecting") {
      wifiBadge.innerHTML = '<span class="badge-dot"></span> WiFi: Connecting...';
      wifiBadge.className = "badge disconnected";
      lblGwStatus.textContent = "Đang kết nối WiFi " + (obj.ssid || "") + "...";
      toast("Đang kết nối vào WiFi " + (obj.ssid || "") + "...", "info");
    } else if (obj.status === "connected") {
      wifiBadge.innerHTML = '<span class="badge-dot"></span> WiFi: ' + (obj.ssid || "OK");
      wifiBadge.className = "badge connected";
      lblGwStatus.textContent = "Connected (" + (obj.ssid || "") + ")";
      if (obj.ip) lblGwIp.textContent = obj.ip;
      toast("WiFi đã kết nối thành công! IP: " + (obj.ip || ""), "success");
      sendCommand({ cmd: "get_gw_info" });
    } else if (obj.status === "ap_mode") {
      wifiBadge.innerHTML = '<span class="badge-dot"></span> AP Mode Active';
      wifiBadge.className = "badge ap_mode";
      lblGwStatus.textContent = "AP Mode (" + (obj.ssid || "192.168.4.1") + ")";
      if (obj.ip) lblGwIp.textContent = obj.ip;
      toast("Đã bật trạm AP! Mở http://192.168.4.1 để cấu hình", "info", 5000);
    } else if (obj.status === "failed") {
      wifiBadge.innerHTML = '<span class="badge-dot"></span> WiFi: Failed';
      wifiBadge.className = "badge disconnected";
      lblGwStatus.textContent = "Kết nối thất bại";
      toast("Kết nối WiFi thất bại: " + (obj.msg || "Timeout"), "error");
    }
  }

  function handleErr(obj) {
    toast(obj.msg || "Unknown error", "error", 5000);
  }

  // ── Send Command to ESP32 via Serial ─────────────────────────────────────
  async function sendCommand(obj) {
    if (!writer) return;
    const json = JSON.stringify(obj) + "\n";
    const encoder = new TextEncoder();
    try {
      await writer.write(encoder.encode(json));
    } catch (err) {
      toast("Lỗi ghi Serial: " + err.message, "error");
    }
  }

  // ── Log Table Helpers ────────────────────────────────────────────────────
  const MAX_LOG_ROWS = 600;

  function addLogRow({ pkt, ts, data, len, rssi, snr, fwd }) {
    if (logEmpty && !logEmpty.classList.contains("hidden")) {
      logEmpty.classList.add("hidden");
    }
    const tr = document.createElement("tr");

    let rssiClass = "";
    const rssiNum = parseFloat(rssi);
    if (!isNaN(rssiNum)) {
      if (rssiNum > -80) rssiClass = "rssi-good";
      else if (rssiNum > -110) rssiClass = "rssi-ok";
      else rssiClass = "rssi-bad";
    }

    let snrClass = "";
    const snrNum = parseFloat(snr);
    if (!isNaN(snrNum)) {
      snrClass = snrNum >= 0 ? "snr-good" : "snr-bad";
    }

    const ttsTag = fwd ? '<span class="fwd-pill">Forwarded</span>' : '—';
    const payloadText = String(data ?? "");

    tr.innerHTML = `
      <td class="col-pkt">${pkt}</td>
      <td class="col-time">${ts}</td>
      <td class="col-payload"><span class="payload-box"><code>${escHtml(payloadText)}</code></span></td>
      <td class="col-len">${len ?? "—"}</td>
      <td class="col-rssi ${rssiClass}">${rssi}</td>
      <td class="col-snr ${snrClass}">${snr}</td>
      <td class="col-fwd">${ttsTag}</td>
    `;

    // Apply quick search filter if active
    if (logSearchInput && logSearchInput.value.trim() !== "") {
      const q = logSearchInput.value.trim().toLowerCase();
      const match = (String(pkt).toLowerCase().includes(q) ||
                     payloadText.toLowerCase().includes(q) ||
                     String(rssi).toLowerCase().includes(q));
      if (!match) tr.classList.add("hidden-by-filter");
    }

    logBody.appendChild(tr);

    while (logBody.children.length > MAX_LOG_ROWS) {
      logBody.removeChild(logBody.firstChild);
    }

    if (logCount) {
      logCount.textContent = `${logBody.children.length} msgs`;
    }

    if (chkAutoScroll && chkAutoScroll.checked && logContainer) {
      logContainer.scrollTop = logContainer.scrollHeight;
    }
  }

  // ── Quick Filter Event ───────────────────────────────────────────────────
  if (logSearchInput) {
    logSearchInput.addEventListener("input", (e) => {
      const q = e.target.value.trim().toLowerCase();
      const rows = logBody.querySelectorAll("tr");
      rows.forEach(r => {
        if (!q) {
          r.classList.remove("hidden-by-filter");
        } else {
          const text = r.textContent.toLowerCase();
          if (text.includes(q)) {
            r.classList.remove("hidden-by-filter");
          } else {
            r.classList.add("hidden-by-filter");
          }
        }
      });
    });
  }

  // ── Export CSV Handler ───────────────────────────────────────────────────
  if (btnExportLog) {
    btnExportLog.addEventListener("click", () => {
      if (packetRecords.length === 0) {
        toast("Chưa có bản ghi nào để xuất CSV.", "info");
        return;
      }
      let csv = "Packet_ID,Timestamp,Payload,Length,RSSI_dBm,SNR_dB,Forwarded\n";
      packetRecords.forEach(r => {
        const cleanPayload = `"${String(r.data).replace(/"/g, '""')}"`;
        csv += `${r.pkt},${r.ts},${cleanPayload},${r.len},${r.rssi},${r.snr},${r.fwd}\n`;
      });

      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `lora_packets_${new Date().toISOString().slice(0,19).replace(/[:T]/g, "-")}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast(`Đã xuất thành công ${packetRecords.length} gói tin ra CSV!`, "success");
    });
  }

  // ── Enhanced Canvas RSSI / SNR Chart ─────────────────────────────────────
  function drawChart() {
    if (!chartCanvas) return;
    const ctx = chartCanvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = chartCanvas.getBoundingClientRect();
    chartCanvas.width  = rect.width * dpr;
    chartCanvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    ctx.clearRect(0, 0, w, h);

    // Draw Subtle Grid & Axis Lines
    ctx.strokeStyle = "rgba(148, 163, 184, 0.08)";
    ctx.lineWidth = 1;
    for (let y = 30; y < h - 10; y += 38) {
      ctx.beginPath();
      ctx.moveTo(35, y);
      ctx.lineTo(w - 15, y);
      ctx.stroke();
    }

    // Axis Labels
    ctx.font = "10px JetBrains Mono, monospace";
    ctx.fillStyle = "rgba(148, 163, 184, 0.5)";
    ctx.fillText("-50", 10, 40);
    ctx.fillText("-90", 10, 105);
    ctx.fillText("-130", 6, h - 20);

    if (rssiData.length < 2) {
      ctx.font = "12px Inter, sans-serif";
      ctx.fillStyle = "rgba(148, 163, 184, 0.35)";
      ctx.textAlign = "center";
      ctx.fillText("Đang chờ dữ liệu biểu đồ từ các gói tin LoRa tiếp theo...", w / 2, h / 2);
      ctx.textAlign = "left";
      return;
    }

    // Map helpers
    // RSSI: -130 to -30 dBm
    const mapRssi = (val) => {
      const min = -130, max = -30;
      const clamped = Math.max(min, Math.min(max, val));
      return (h - 25) - ((clamped - min) / (max - min)) * (h - 55);
    };

    // SNR: -20 to +15 dB
    const mapSnr = (val) => {
      const min = -20, max = 15;
      const clamped = Math.max(min, Math.min(max, val));
      return (h - 25) - ((clamped - min) / (max - min)) * (h - 55);
    };

    const graphLeft = 40;
    const graphWidth = w - graphLeft - 15;
    const step = graphWidth / (CHART_MAX - 1);
    const offset = graphLeft + graphWidth - (rssiData.length - 1) * step;

    // 1. Plot RSSI Area Gradient + Line (Emerald)
    const rssiGrad = ctx.createLinearGradient(0, 0, 0, h);
    rssiGrad.addColorStop(0, "rgba(16, 185, 129, 0.2)");
    rssiGrad.addColorStop(1, "rgba(16, 185, 129, 0.0)");

    ctx.beginPath();
    for (let i = 0; i < rssiData.length; i++) {
      const x = offset + i * step;
      const y = mapRssi(rssiData[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    // Fill area under RSSI line
    ctx.lineTo(offset + (rssiData.length - 1) * step, h - 25);
    ctx.lineTo(offset, h - 25);
    ctx.closePath();
    ctx.fillStyle = rssiGrad;
    ctx.fill();

    // Draw RSSI stroke
    ctx.beginPath();
    ctx.strokeStyle = "#10b981";
    ctx.lineWidth = 2.2;
    for (let i = 0; i < rssiData.length; i++) {
      const x = offset + i * step;
      const y = mapRssi(rssiData[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // 2. Plot SNR Line (Amber)
    ctx.beginPath();
    ctx.strokeStyle = "#f59e0b";
    ctx.lineWidth = 2.0;
    for (let i = 0; i < snrData.length; i++) {
      const x = offset + i * step;
      const y = mapSnr(snrData[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  window.addEventListener("resize", drawChart);

  // ── Frequency Preset Buttons & Spectrum Pills ────────────────────────────
  function setTargetFrequency(freqStr) {
    const freqInput = $("#cfg-freq");
    if (freqInput) {
      freqInput.value = freqStr;
      toast(`Đã chọn tần số ${freqStr} MHz. Bấm "Apply" để lưu.`, "info");
      highlightActiveChannelPill(freqStr);
    }
  }

  presetBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      if (btn.dataset.freq) setTargetFrequency(btn.dataset.freq);
    });
  });

  channelPills.forEach(pill => {
    pill.addEventListener("click", () => {
      if (pill.dataset.freq) setTargetFrequency(pill.dataset.freq);
    });
  });

  // ── UI Event Listeners ───────────────────────────────────────────────────
  btnConnect.addEventListener("click", () => {
    if (port) disconnectSerial();
    else connectSerial();
  });

  btnClearLog.addEventListener("click", () => {
    logBody.innerHTML = "";
    packetRecords.length = 0;
    if (logEmpty) logEmpty.classList.remove("hidden");
    if (logCount) logCount.textContent = "0 msgs";
    if (btnScrollBottom) btnScrollBottom.classList.add("hidden");
    toast("Đã xóa bảng log.", "info");
  });

  // Scroll monitoring: Show/hide "Scroll to bottom" button
  if (logContainer) {
    logContainer.addEventListener("scroll", () => {
      const distFromBottom = logContainer.scrollHeight - logContainer.scrollTop - logContainer.clientHeight;
      if (distFromBottom > 70) {
        if (btnScrollBottom) btnScrollBottom.classList.remove("hidden");
      } else {
        if (btnScrollBottom) btnScrollBottom.classList.add("hidden");
      }
    });
  }

  if (btnScrollBottom) {
    btnScrollBottom.addEventListener("click", () => {
      if (logContainer) {
        logContainer.scrollTo({ top: logContainer.scrollHeight, behavior: "smooth" });
      }
      btnScrollBottom.classList.add("hidden");
    });
  }

  // Copy Gateway EUI
  btnCopyEui.addEventListener("click", () => {
    const eui = valGwEui.textContent.trim();
    if (!eui || eui.includes("-")) {
      toast("Chưa có Gateway EUI để copy. Hãy kết nối Serial trước.", "error");
      return;
    }
    navigator.clipboard.writeText(eui).then(() => {
      toast(`Đã copy Gateway EUI: ${eui}`, "success");
    }).catch(() => {
      toast(`Gateway EUI: ${eui}`, "info");
    });
  });

  // TTS Cloud Config Form Submit
  ttsForm.addEventListener("submit", (e) => {
    e.preventDefault();
    let server = ttsServerInput.value.trim();
    let portNum = parseInt(ttsPortInput.value, 10);
    if (server.includes(":")) {
      const parts = server.split(":");
      server = parts[0];
      if (!portNum && parts[1]) portNum = parseInt(parts[1], 10);
    }
    ttsServerInput.value = server;

    sendCommand({
      cmd: "set_tts",
      server: server || "eu1.cloud.thethings.network",
      port: portNum || 1700
    });
    toast("Đang lưu cấu hình TTS Cloud tới thiết bị...", "info");
  });

  // Remote AP Mode trigger
  btnTriggerAp.addEventListener("click", () => {
    sendCommand({ cmd: "start_ap" });
    toast("Đang kích hoạt trạm phát AP Mode...", "info");
  });

  btnReadGw.addEventListener("click", () => {
    sendCommand({ cmd: "get_gw_info" });
    toast("Đang làm mới thông tin Gateway...", "info");
  });

  // LoRa Hardware Config Form
  btnReadCfg.addEventListener("click", () => {
    sendCommand({ cmd: "get_cfg" });
  });

  configForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const freq = parseFloat($("#cfg-freq").value);
    const bw   = parseFloat($("#cfg-bw").value);
    const sf   = parseInt($("#cfg-sf").value, 10);
    const cr   = parseInt($("#cfg-cr").value, 10);
    const sw   = parseInt($("#cfg-sw").value, 10);
    const pwr  = parseInt($("#cfg-pwr").value, 10);
    const pre  = parseInt($("#cfg-pre").value, 10);

    sendCommand({
      cmd: "cfg",
      freq, bw, sf, cr, sw, pwr, pre
    });
    toast("Đang gửi tham số LoRa mới tới thiết bị...", "info");
  });

  // Initial draw
  setTimeout(drawChart, 200);

})();
