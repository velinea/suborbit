// static/js/form.js
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("runForm");
  if (!form) return;

  const resetBtn = document.getElementById("reset-filters");
  const langInput = document.getElementById("subtitle_lang");
  const langHint = document.getElementById("langHint");

  // ----------------------------------------
  // 1️⃣ LocalStorage persistence
  // ----------------------------------------
  document.querySelectorAll(".persist").forEach((el) => {
    const key = "persist_" + el.name;
    const saved = localStorage.getItem(key);

    // Restore
    if (saved !== null) {
      if (el.type === "checkbox") el.checked = saved === "true";
      else el.value = saved;
    }

    // Save on change
    el.addEventListener("change", () => {
      if (el.type === "checkbox")
        localStorage.setItem(key, el.checked);
      else
        localStorage.setItem(key, el.value);
    });
  });

  // ----------------------------------------
  // 2️⃣ Subtitle language validation
  // ----------------------------------------
  if (langInput) {
    const storageKey = "persist_" + langInput.name;
    const validLangs = [
      "en","fr","es","de","it","pt","ru","zh","ja","ko","sv",
      "fi","no","da","pl","nl","tr","ar","he","cs","el","th",
      "hu","ro","id","uk"
    ];

    function validateLang() {
      let val = langInput.value.replace(/[^a-zA-Z]/g, "")
        .toLowerCase().slice(0, 2);
      langInput.value = val;

      const isValid = /^[a-z]{2}$/.test(val) && validLangs.includes(val);
      langInput.classList.toggle("border-green-500", isValid);
      langInput.classList.toggle("border-red-500", !isValid && val.length > 0);
      langHint.classList.toggle("opacity-100", !isValid && val.length > 0);
      langHint.classList.toggle("opacity-0", isValid || val.length === 0);

      localStorage.setItem(storageKey, val);
    }

    langInput.addEventListener("input", validateLang);
    langInput.addEventListener("blur", () => {
      if (langInput.value.length === 1) {
        langInput.value = "";
        langHint.classList.add("opacity-100");
        localStorage.removeItem(storageKey);
      }
    });

    validateLang();
  }

  // ----------------------------------------
  // 3️⃣ Year validation before submit
  // ----------------------------------------
  form.addEventListener("submit", (e) => {
    const start = parseInt(form.start_year.value);
    const end = parseInt(form.end_year.value);
    if (start > end) {
      e.preventDefault();
      alert("Start year cannot be greater than end year.");
    }
  });

  // ----------------------------------------
  // 4️⃣ Reset filters
  // ----------------------------------------
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      document.querySelectorAll(".persist").forEach((el) => {
        const key = "persist_" + el.name;
        if (el.type === "checkbox") el.checked = false;
        else el.value = "";
        localStorage.removeItem(key);
      });
      location.reload();
    });
  }

  // ----------------------------------------
  // 5️⃣ Hook start button
  // ----------------------------------------
  document.getElementById("start-btn").addEventListener("click", async () => {
    const form = document.getElementById("runForm");
    const formData = new FormData(form);

    const startBtn = document.getElementById("start-btn");
    const stopForm = document.getElementById("stop-form");
    const statusText = document.getElementById("status-text");
    const statusDot = document.getElementById("status-dot");

    startBtn.disabled = true;
    startBtn.classList.add("opacity-50", "cursor-not-allowed");
    statusText.textContent = "Starting...";
    statusText.className = "text-yellow-400";
    statusDot.className = "w-3 h-3 rounded-full bg-yellow-400";

    try {
      const res = await fetch(form.action, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.status === "started") {
        statusText.textContent = "Running...";
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
  });

  document.getElementById("stop-form").addEventListener("submit", async (e) => {
  e.preventDefault();
    try {
      const res = await fetch("/stop", { method: "POST" });
      const data = await res.json();
      if (data.status === "stopped") {
        const statusText = document.getElementById("status-text");
        const statusDot = document.getElementById("status-dot");
        statusText.textContent = "Idle";
        statusText.className = "text-gray-400";
        statusDot.className = "w-3 h-3 rounded-full bg-gray-400";
        document.getElementById("stop-form").style.display = "none";
        const startBtn = document.getElementById("start-btn");
        startBtn.disabled = false;
        startBtn.classList.remove("opacity-50", "cursor-not-allowed");
      }
    } catch (err) {
      console.error("Failed to stop discovery:", err);
    }
  });

  // ----------------------------------------
  // 6️⃣ Show loading overlay on start
  // ---------------------------------------- 
  document.getElementById("start-btn").addEventListener("click", () => {
    const overlay = document.getElementById("loading-overlay");
    overlay.classList.remove("hidden");
    overlay.classList.add("flex", "opacity-0");
    requestAnimationFrame(() => overlay.classList.replace("opacity-0", "opacity-100"));
    document.getElementById("runForm").submit();
  });

});
