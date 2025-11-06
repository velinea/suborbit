async function checkForPosterUpdate() {
  try {
    const res = await fetch("/api/radarr/check_update");
    const data = await res.json();
    if (data.update) {
      console.log("🔄 Radarr updated — reloading carousel");
      loadRecent();
    }
  } catch (err) {
    console.error("Failed to check poster update:", err);
  }
}

// only poll while discovery running
setInterval(() => {
  const running = document.getElementById("status-text").textContent.includes("Running");
  if (running) checkForPosterUpdate();
}, 5000);

let lastState = "Idle";

async function updateStatus() {
  const res = await fetch("/status");
  const data = await res.json();
  const running = data.running;

  updateStatusDisplay(running);

  if (running) {
    checkForPosterUpdate();
  } else if (lastState === "Running" && !running) {
    // 🚀 Discovery just finished → refresh one last time
    console.log("Discovery completed — refreshing posters");
    loadRecent();
  }

  lastState = running ? "Running" : "Idle";
}
