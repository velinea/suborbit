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
    const stopForm = document.getElementById("stop-form");

    if (running) {
      // 🟢 Running
      dot.className = "inline-block w-3 h-3 rounded-full bg-green-500 animate-pulse shadow-sm";
      text.textContent = "Running";
      text.className = "text-sm text-green-400";

      startBtn.style.display = "none";
      stopForm.style.display = "inline";
    } else {
      // ⚪ Idle
      dot.className = "inline-block w-3 h-3 rounded-full bg-gray-500 shadow-sm";
      text.textContent = "Idle";
      text.className = "text-sm text-gray-400";

      startBtn.style.display = "inline";
      stopForm.style.display = "none";
    }
  }

  function updateStatus() {
    fetch("/core/status")
      .then(r => r.json())
      .then(data => updateStatusDisplay(data.running))
      .catch(err => console.error("Status fetch failed:", err));
  }

  // Poll every 2 seconds
  updateStatus();
  setInterval(updateStatus, 2000);

  // Hook Start button to sidebar form
  document.getElementById("start-btn").addEventListener("click", () => {
    const form = document.getElementById("runForm");
    if (form) form.submit();
  });

  // Auto-scroll preference
  const checkbox = document.getElementById("autoscroll");
  const saved = localStorage.getItem("autoscroll");
  if (saved !== null) checkbox.checked = saved === "true";
  checkbox.addEventListener("change", () => {
    localStorage.setItem("autoscroll", checkbox.checked);
  });

  console.debug("[SubOrbit] status.js initialized");
});
