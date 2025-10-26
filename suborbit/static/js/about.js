document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("about-modal");
  const card = document.getElementById("about-card");
  const versionEl = document.getElementById("about-version");
  const buildEl = document.getElementById("about-build");
  const repoEl = document.getElementById("about-repo");
  const servicesEl = document.getElementById("about-services");
  const appVersionEl = document.getElementById("app-version");

  async function loadAbout() {
    servicesEl.innerHTML = `
      <p class="text-xs text-gray-400">Checking integrations...</p>
    `;

    try {
      const res = await fetch("/api/config/status");
      const info = await res.json();

      versionEl.textContent = info.suborbit.version;
      buildEl.textContent = info.suborbit.build;
      repoEl.href = "https://github.com/velinea/suborbit";
      appVersionEl.textContent = `SubOrbit ${info.suborbit.version}`;

      const services = ["radarr", "trakt", "opensubtitles"];
      const statusHTML = services.map(s => {
        const svc = info[s];
        const color = svc.ok ? "text-green-400" : "text-red-400";
        return `<p class="text-xs ${color}">
          ${s.charAt(0).toUpperCase() + s.slice(1)}: ${svc.details}
        </p>`;
      }).join("");

      servicesEl.innerHTML = `
        <div class="mt-2">${statusHTML}</div>
        <p class="text-xs text-gray-500 mt-2 italic">${info.summary}</p>
      `;
    } catch (err) {
      console.error("About info fetch failed:", err);
      servicesEl.innerHTML = `<p class="text-xs text-red-400">Error loading system info</p>`;
    }
  }

  // open modal
  appVersionEl.addEventListener("click", () => {
    modal.classList.remove("hidden");
    modal.classList.add("flex");
    setTimeout(() => {
      card.classList.remove("scale-95", "opacity-0");
      card.classList.add("scale-100", "opacity-100");
    }, 20);
    loadAbout();
  });

  // close modal
  function closeModal() {
    card.classList.remove("scale-100", "opacity-100");
    card.classList.add("scale-95", "opacity-0");
    setTimeout(() => {
      modal.classList.add("hidden");
      modal.classList.remove("flex");
    }, 250);
  }

  document.getElementById("about-close").addEventListener("click", closeModal);
  window.addEventListener("click", e => {
    if (e.target.id === "about-modal") closeModal();
  });
});
