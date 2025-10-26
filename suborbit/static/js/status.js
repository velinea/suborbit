// static/js/status.js
document.addEventListener("DOMContentLoaded", () => {
  const logDiv = document.getElementById("log");
  const statusSpan = document.getElementById("status-text");
  const startBtn = document.getElementById("start-btn");
  const stopForm = document.getElementById("stop-form");
  const autoscroll = document.getElementById("autoscroll");

  if (!logDiv || !statusSpan) return;

  const STATUS_INTERVAL = 2000;
  const LOG_INTERVAL = 2000;

  // ----------------------------------------
  // 1️⃣ Autoscroll persistence
  // ----------------------------------------
  const savedScroll = localStorage.getItem("autoscroll");
  if (savedScroll !== null) {
    autoscroll.checked = savedScroll === "true";
  }

  autoscroll.addEventListener("change", () => {
    localStorage.setItem("autoscroll", autoscroll.checked);
  });

  // ----------------------------------------
  // 2️⃣ Log coloring helper
  // ----------------------------------------
  function colorizeLogs(lines) {
    return lines.map(line => {
      if (line.startsWith("❌")) return `<span class="text-red-400">${line}</span>`;
      if (line.startsWith("✅")) return `<span class="text-green-400">${line}</span>`;
      if (line.startsWith("📀")) return `<span class="text-yellow-400">${line}</span>`;
      if (line.startsWith("🎬")) return `<span class="text-blue-400">${line}</span>`;
      return line;
    }).join("<br>");
  }

  // ----------------------------------------
  // 3️⃣ Fetch logs
  // ----------------------------------------
  async function fetchLogs() {
    try {
      const r = await fetch("/core/logs");
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const lines = await r.json();
      logDiv.innerHTML = colorizeLogs(lines);

      if (autoscroll.checked) {
        logDiv.scrollTop = logDiv.scrollHeight;
      }
    } catch (err) {
      console.error("Log fetch failed:", err);
      logDiv.innerHTML = `<p class='text-red-400 text-sm'>Error loading logs.</p>`;
    }
  }

  // ----------------------------------------
  // 4️⃣ Fetch core status
  // ----------------------------------------
  async function updateStatus() {
    try {
      const r = await fetch("/core/status");
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();

      if (data.running) {
        statusSpan.textContent = "Running...";
        statusSpan.className = "font-mono text-green-400";

        startBtn.disabled = true;
        startBtn.classList.add("opacity-50", "cursor-not-allowed");

        stopForm.style.display = "inline";
      } else {
        statusSpan.textContent = "Idle";
        statusSpan.className = "font-mono text-gray-400";

        startBtn.disabled = false;
        startBtn.classList.remove("opacity-50", "cursor-not-allowed");

        stopForm.style.display = "none";
      }
    } catch (err) {
      console.error("Status fetch failed:", err);
      statusSpan.textContent = "Error";
      statusSpan.className = "font-mono text-red-400";
    }
  }

  // ----------------------------------------
  // 5️⃣ Polling setup
  // ----------------------------------------
  fetchLogs();
  updateStatus();
  setInterval(fetchLogs, LOG_INTERVAL);
  setInterval(updateStatus, STATUS_INTERVAL);

  console.debug("[SubOrbit] status.js initialized");
});
