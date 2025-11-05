// static/js/trakt.js
document.addEventListener("DOMContentLoaded", () => {
  const cfg = window.SubOrbitConfig?.urls || {};
  const loginBtn = document.getElementById("trakt-login-btn");
  const loginPopup = document.getElementById("trakt-login-popup");
  const authBtn = document.getElementById("start-trakt-auth");
  const statusDiv = document.getElementById("trakt-auth-status");

  const listBtn = document.getElementById("trakt-btn");
  const popup = document.getElementById("trakt-popup");
  const saveBtn = document.getElementById("trakt-save");
  const cancelBtn = document.getElementById("trakt-cancel");

  if (!loginBtn || !authBtn || !saveBtn) return;

  // === LOGIN POPUP ===
  loginBtn.addEventListener("click", () => {
    loginPopup?.classList.toggle("hidden");
  });

  authBtn.addEventListener("click", async e => {
    e.preventDefault();
    e.stopPropagation();
    if (!cfg.traktDevice || !cfg.traktStatus) {
      console.error("Trakt URLs missing from SubOrbitConfig.");
      return;
    }

    statusDiv.textContent = "⏳ Requesting device code...";

    try {
      const res = await fetch(cfg.traktDevice);
      const data = await res.json();
      const activateUrl = `https://trakt.tv/activate?code=${data.user_code}`;

      statusDiv.innerHTML = `
        Go to <a href="${activateUrl}" target="_blank" class="text-blue-400 underline">trakt.tv/activate</a>
        and enter <b>${data.user_code}</b><br>⏳ Waiting for authorization...
      `;

      const poll = setInterval(async () => {
        const r = await fetch(cfg.traktStatus);
        const s = await r.json();

        if (s.state === "done") {
          clearInterval(poll);
          statusDiv.innerHTML = "✅ Connected";
          setTimeout(() => {
            loginPopup.classList.add("hidden");
            location.reload();
          }, 1500);
        } else if (s.state === "error") {
          clearInterval(poll);
          statusDiv.innerHTML = "❌ Authorization failed or timed out.";
        }
      }, 3000);
    } catch (err) {
      console.error("Trakt device code request failed:", err);
      statusDiv.textContent = "❌ Failed to start authentication.";
    }
  });

  // === TRAKT LIST POPUP ===
  listBtn?.addEventListener("click", () => {
    popup?.classList.toggle("hidden");
  });

  cancelBtn?.addEventListener("click", () => {
    popup?.classList.add("hidden");
  });

  saveBtn.addEventListener("click", () => {
    const userInput = document.getElementById("trakt-user-input");
    const listInput = document.getElementById("trakt-list-input");
    const user = userInput?.value.trim();
    const list = listInput?.value.trim();

    if (!user || !list) {
      alert("Please enter both user and list name.");
      return;
    }

    // Hidden form fields for backend
    document.getElementById("trakt_user").value = user;
    document.getElementById("trakt_list").value = list;

    // Persist locally
    localStorage.setItem("persist_trakt_user", user);
    localStorage.setItem("persist_trakt_list", list);

    popup.classList.add("hidden");
  });

  // === STATUS CHECK ===
  async function checkTraktStatus() {
    if (!cfg.traktStatus) return;
    try {
      const res = await fetch(cfg.traktStatus);
      const data = await res.json();

      if (data.authenticated) {
        loginBtn.textContent = "✅ Connected";
        loginBtn.classList.remove("bg-red-600", "hover:bg-red-700");
        loginBtn.classList.add("bg-green-600", "cursor-default");
        loginBtn.disabled = true;
      } else {
        loginBtn.textContent = "🔑 Login";
        loginBtn.classList.remove("bg-green-600", "cursor-default");
        loginBtn.classList.add("bg-red-600", "hover:bg-red-700");
        loginBtn.disabled = false;
      }
    } catch (err) {
      console.error("Trakt status check failed:", err);
    }
  }

  checkTraktStatus();
  setInterval(checkTraktStatus, 60000);
});
