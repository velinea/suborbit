// static/js/genres.js
document.addEventListener("DOMContentLoaded", () => {
  const popup = document.getElementById("genres-popup");
  const list = document.getElementById("genres-list");
  const btn = document.getElementById("genres-info-btn");
  const input = document.querySelector("input[name='genres']");
  const storageKey = "persist_genres";
  const genresUrl = window.SubOrbitConfig?.urls?.genres;

  if (!popup || !list || !btn || !input || !genresUrl) return;

  function updateChipColors() {
    const current = input.value.split(",").map(s => s.trim().toLowerCase()).filter(Boolean);
    list.querySelectorAll("button").forEach(button => {
      const g = button.textContent.toLowerCase();
      if (current.includes(g)) {
        button.className = "px-2 py-1 rounded bg-blue-600 text-white text-xs";
      } else if (current.includes("!" + g)) {
        button.className = "px-2 py-1 rounded bg-red-600 text-white text-xs";
      } else {
        button.className = "px-2 py-1 rounded bg-gray-700 hover:bg-blue-600 text-xs";
      }
    });
  }

  function insertGenre(genre) {
    let current = input.value.split(",").map(s => s.trim()).filter(Boolean);
    const idx = current.findIndex(g => g.toLowerCase() === genre.toLowerCase());
    const exIdx = current.findIndex(g => g.toLowerCase() === "!" + genre.toLowerCase());

    if (idx >= 0) current[idx] = "!" + genre;
    else if (exIdx >= 0) current.splice(exIdx, 1);
    else current.push(genre);

    input.value = current.join(", ");
    localStorage.setItem(storageKey, input.value);
    updateChipColors();
  }

  // Load genres once
  btn.addEventListener("click", () => {
    if (!list.hasChildNodes()) {
      fetch(genresUrl)
        .then(r => r.json())
        .then(genres => {
          genres.forEach(g => {
            const button = document.createElement("button");
            button.type = "button";
            button.textContent = g;
            button.className = "px-2 py-1 rounded bg-gray-700 hover:bg-blue-600 text-xs";
            button.addEventListener("click", () => insertGenre(g));
            list.appendChild(button);
          });
          updateChipColors();
        })
        .catch(err => console.error("Failed to fetch genres:", err));
    }
    popup.classList.toggle("hidden");
  });

  // Close popup when clicking outside
  document.addEventListener("click", e => {
    if (!popup.contains(e.target) && !btn.contains(e.target)) popup.classList.add("hidden");
  });

  // Restore persisted
  const saved = localStorage.getItem(storageKey);
  if (saved) input.value = saved;

  input.addEventListener("input", () => {
    localStorage.setItem(storageKey, input.value);
    updateChipColors();
  });
});
