document.addEventListener("DOMContentLoaded", () => {
  const carousel = document.getElementById("poster-carousel");
  const refreshBtn = document.getElementById("refresh-posters");

  async function loadRecent() {
    if (!carousel) return;

    carousel.innerHTML = "<p class='text-gray-400 text-sm'>Loading...</p>";

    try {
      const res = await fetch("/api/radarr/recent");
      const data = await res.json();
      carousel.innerHTML = "";

      if (data.error) {
        carousel.innerHTML = `<p class='text-sm text-red-400'>${data.error}</p>`;
        return;
      }

      for (const m of data) {
        if (!m.poster) continue;

        const year = m.year || "—";
        const rating = m.rating ? `⭐ ${m.rating.toFixed(1)}` : "⭐ —";
        const overview = m.overview
          ? m.overview.replace(/"/g, "&quot;").substring(0, 300)
          : "No description available.";

        const card = document.createElement("div");
        card.className = "relative group h-64 w-44 flex-shrink-0 cursor-pointer snap-start";

        card.innerHTML = `
          <!-- Poster -->
          <a href="${m.radarr || '#'}" target="_blank" rel="noopener noreferrer"
            class="relative block h-64 w-44 flex-shrink-0 snap-start group">
            <img src="${m.poster}" alt="${m.title}"
                class="h-full w-full object-cover rounded-lg shadow-lg transition
                        duration-300 group-hover:opacity-70" />

            <!-- Static info bar -->
            <div class="absolute bottom-0 left-0 right-0 bg-gray-900/80 text-gray-100 text-xs p-2 rounded-b-lg z-10">
              <p class="font-semibold text-sm truncate">${m.title}</p>
              <p class="text-yellow-400 text-xs mt-0.5">${year} &nbsp; ${rating}</p>
            </div>

            <!-- Hover overlay -->
            <div class="absolute inset-0 bg-gray-900/90 text-gray-100 text-xs p-3 rounded-lg opacity-0
                        group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end z-20">
              <p class="font-semibold text-sm mb-1 truncate">${m.title}</p>
              <p class="text-yellow-400 text-xs mb-2">${year} &nbsp; ${rating}</p>
              <p class="leading-snug line-clamp-6">${overview}</p>
            </div>

            <!-- Top-right icons -->
            <div class="absolute top-1 right-1 flex space-x-1 opacity-0 group-hover:opacity-100
                        transition-opacity z-30">
              ${m.tmdb ? `
                <a href="${m.tmdb}" target="_blank" rel="noopener noreferrer"
                  class="bg-gray-900/70 hover:bg-gray-900/90 rounded p-1 shadow">
                  <img src="/static/icons/tmdb.png" class="h-4 w-4" alt="TMDB">
                </a>` : ""}
              ${m.imdb ? `
                <a href="${m.imdb}" target="_blank" rel="noopener noreferrer"
                  class="bg-gray-900/70 hover:bg-gray-900/90 rounded p-1 shadow">
                  <img src="/static/icons/imdb.png" class="h-4 w-4" alt="IMDb">
                </a>` : ""}
            </div>
          </a>
        `;

        card.style.animationDelay = `${Math.random() * 0.3}s`;
        card.style.opacity = "0";
        carousel.appendChild(card);
        setTimeout(() => { card.style.transition = "opacity 0.4s"; card.style.opacity = "1"; }, 10);
      }
    } catch (err) {
      console.error("Radarr fetch failed:", err);
      carousel.innerHTML = `<p class='text-red-400 text-sm'>Error loading posters.</p>`;
    }
  }

  // Load on page ready
  loadRecent();

  // Manual refresh
  refreshBtn?.addEventListener("click", loadRecent);
});
