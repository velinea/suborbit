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
  const startBtn = document.getElementById("start-btn");
  if (startBtn) {
    startBtn.addEventListener("click", () => form.submit());
  }

  console.debug("[SubOrbit] form.js initialized");
});
