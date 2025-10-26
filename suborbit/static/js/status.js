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
      const r = await fetch("/logs");
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

  function updateStatusDisplay(running) {
    const dot = document.getElementById("status-dot");
    const text = document.getElementById("status-text");
    const startBtn = document.getElementById("start-btn");

    if (running) {
      dot.className = "w-3 h-3 rounded-full bg-green-500 animate-pulse";
      text.textContent = "Running";
      text.className = "text-sm text-green-400";
      startBtn.disabled = true;
      startBtn.classList.add("opacity-50", "cursor-not-allowed");
    } else {
      dot.className = "w-3 h-3 rounded-full bg-gray-500";
      text.textContent = "Idle";
      text.className = "text-sm text-gray-400";
      startBtn.disabled = false;
      startBtn.classList.remove("opacity-50", "cursor-not-allowed");
    }
  }

  
  function updateStatus() {
  fetch("/core/status")
    .then(r => r.json())
    .then(data => {
      updateStatusDisplay(data.running);
    })
    .catch(err => console.error("Status fetch failed:", err));
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
