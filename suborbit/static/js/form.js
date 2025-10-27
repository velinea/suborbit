document.addEventListener("DOMContentLoaded", () => {
  const startBtn = document.getElementById("start-btn");
  const stopForm = document.getElementById("stop-form");
  const form = document.getElementById("runForm");
  const statusText = document.getElementById("status-text");
  const statusDot = document.getElementById("status-dot");

  // --- Dynamic Start ---
  startBtn?.addEventListener("click", async () => {
    const formData = new FormData(form);

    startBtn.disabled = true;
    startBtn.classList.add("opacity-50", "cursor-not-allowed");
    statusText.textContent = "Starting…";
    statusText.className = "text-yellow-400";
    statusDot.className = "w-3 h-3 rounded-full bg-yellow-400";

    try {
      const res = await fetch("/start", { method: "POST", body: formData });
      const data = await res.json();

      if (data.status === "started") {
        statusText.textContent = "Running…";
        statusText.className = "text-green-400";
        statusDot.className = "w-3 h-3 rounded-full bg-green-400 shadow-sm";
        stopForm.style.display = "inline";
      } else {
        throw new Error(data.status || "Unknown error");
      }
    } catch (err) {
      console.error("Failed to start discovery:", err);
      statusText.textContent = "Error";
      statusText.className = "text-red-400";
      statusDot.className = "w-3 h-3 rounded-full bg-red-500";
      startBtn.disabled = false;
      startBtn.classList.remove("opacity-50", "cursor-not-allowed");
    }

    updateStatus();
  });

  // --- Stop ---
  stopForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const res = await fetch("/stop", { method: "POST" });
      const data = await res.json();

      if (data.status === "stopped") {
        statusText.textContent = "Idle";
        statusText.className = "text-gray-400";
        statusDot.className = "w-3 h-3 rounded-full bg-gray-400";
        stopForm.style.display = "none";
        startBtn.disabled = false;
        startBtn.classList.remove("opacity-50", "cursor-not-allowed");
      }
    } catch (err) {
      console.error("Failed to stop discovery:", err);
    }
    updateStatus();
  });

  // --- Polling ---
  async function updateStatus() {
    try {
      const res = await fetch("/status");
      const data = await res.json();

      if (data.running) {
        statusText.textContent = "Running…";
        statusText.className = "text-green-400";
        statusDot.className = "w-3 h-3 rounded-full bg-green-400 shadow-sm";
        stopForm.style.display = "inline";
        startBtn.disabled = true;
        startBtn.classList.add("opacity-50", "cursor-not-allowed");
      } else {
        statusText.textContent = "Idle";
        statusText.className = "text-gray-400";
        statusDot.className = "w-3 h-3 rounded-full bg-gray-500";
        stopForm.style.display = "none";
        startBtn.disabled = false;
        startBtn.classList.remove("opacity-50", "cursor-not-allowed");
      }
    } catch (err) {
      console.error("Status update failed:", err);
      statusText.textContent = "Error";
      statusText.className = "text-red-400";
      statusDot.className = "w-3 h-3 rounded-full bg-red-500";
    }
  }

    // --- Reset filters ---
  const resetBtn = document.getElementById("reset-filters");
  if (resetBtn) {
    resetBtn.addEventListener("click", (e) => {
      e.preventDefault();

      // Clear persisted values
      document.querySelectorAll(".persist").forEach((el) => {
        if (el.type === "checkbox") {
          el.checked = false;
        } else {
          el.value = "";
        }
        localStorage.removeItem("persist_" + el.name);
      });

      // Also clear Trakt and genre selections if they exist
      localStorage.removeItem("persist_trakt_user");
      localStorage.removeItem("persist_trakt_list");
      localStorage.removeItem("persist_genres");

      // Reset form fields to defaults without full page reload
      form.reset();

      // Optional: update chip colors and UI
      if (typeof updateChipColors === "function") {
        updateChipColors();
      }

      // Give a quick visual feedback
      resetBtn.classList.add("animate-pulse");
      setTimeout(() => resetBtn.classList.remove("animate-pulse"), 500);
    });
  }
  // Initial status update

  updateStatus();
  setInterval(updateStatus, 2000);
});
