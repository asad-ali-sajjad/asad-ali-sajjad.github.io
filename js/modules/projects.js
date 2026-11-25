import { PROJECTS } from "../data/portfolio-data.js";

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value;
  return div.innerHTML;
}

function createProjectCard(project) {
  const demoButton = project.demoUrl
    ? `<a href="${project.demoUrl}" target="_blank" rel="noopener noreferrer"
          class="inline-flex items-center justify-center py-2.5 px-3.5 rounded-xl text-xs font-mono font-semibold bg-sky-500/15 hover:bg-sky-400 text-sky-300 hover:text-slate-950 border border-sky-500/30 hover:border-sky-400 transition">
         Live Demo &nearr;
       </a>`
    : "";

  return `
    <article class="project-card rounded-2xl p-6 flex flex-col justify-between">
      <div>
        <div class="flex items-center justify-between gap-2 mb-4">
          <span class="px-2.5 py-1 rounded-md text-xs font-mono bg-sky-500/10 text-sky-300 border border-sky-500/20">
            ${project.badge}
          </span>
          <span class="flex items-center gap-1.5 text-xs font-mono text-slate-400">
            <span class="w-2.5 h-2.5 rounded-full" style="background-color: ${project.langColor}"></span>
            ${project.language}
          </span>
        </div>

        <h3 class="text-lg font-bold text-white mb-2 font-mono break-words">
          <a href="${project.repoUrl}" target="_blank" rel="noopener noreferrer" class="hover:text-sky-400 transition">
            ${project.title}
          </a>
        </h3>

        <p class="text-sm text-slate-400 leading-relaxed mb-5">
          ${project.description}
        </p>
      </div>

      <div>
        <div class="flex flex-wrap gap-1.5 mb-5">
          ${project.tags
            .map(
              (tag) => `
                <span class="px-2 py-0.5 rounded bg-slate-800/90 text-slate-300 font-mono text-[11px]">
                  ${tag}
                </span>
              `
            )
            .join("")}
        </div>

        <div class="flex items-center gap-2">
          <a href="${project.repoUrl}" target="_blank" rel="noopener noreferrer"
             class="flex-1 inline-flex items-center justify-center py-2.5 px-4 rounded-xl text-xs font-mono font-semibold bg-slate-800/80 hover:bg-sky-400 hover:text-slate-950 text-white border border-slate-700 hover:border-sky-400 transition">
            Source on GitHub &nearr;
          </a>
          ${demoButton}
        </div>
      </div>
    </article>
  `;
}

export function initProjects() {
  const grid = document.getElementById("projects-grid");
  const filterBtns = document.querySelectorAll(".filter-btn");
  const searchInput = document.getElementById("project-search");

  if (!grid) return;

  let activeCategory = "all";
  let searchQuery = "";

  // Populate dynamic project counts on filter buttons
  filterBtns.forEach((btn) => {
    const category = btn.dataset.filter;
    const count =
      category === "all"
        ? PROJECTS.length
        : PROJECTS.filter((p) => p.category === category).length;
    btn.textContent = `${btn.textContent.trim()} (${count})`;
  });

  const render = () => {
    const query = searchQuery.trim().toLowerCase();

    const filtered = PROJECTS.filter((project) => {
      const matchesCategory =
        activeCategory === "all" || project.category === activeCategory;
      const matchesSearch =
        !query ||
        project.title.toLowerCase().includes(query) ||
        project.description.toLowerCase().includes(query) ||
        project.language.toLowerCase().includes(query) ||
        project.tags.some((tag) => tag.toLowerCase().includes(query));

      return matchesCategory && matchesSearch;
    });

    if (filtered.length === 0) {
      grid.innerHTML = `
        <div class="col-span-full text-center py-12 px-4 rounded-2xl border border-slate-800 bg-slate-900/40">
          <p class="font-mono text-sm text-slate-300 mb-2">
            No matching projects found for "<span class="text-sky-400">${escapeHtml(searchQuery)}</span>".
          </p>
          <p class="text-xs text-slate-500 mb-5">Try another keyword or reset your active filters.</p>
          <button id="reset-filters-btn" type="button"
                  class="px-4 py-2 rounded-lg text-xs font-mono font-semibold bg-slate-800 hover:bg-sky-400 text-white hover:text-slate-950 border border-slate-700 hover:border-sky-400 transition">
            Reset Filters
          </button>
        </div>
      `;

      document.getElementById("reset-filters-btn")?.addEventListener("click", () => {
        activeCategory = "all";
        searchQuery = "";
        if (searchInput) searchInput.value = "";
        filterBtns.forEach((b) => {
          const isAll = b.dataset.filter === "all";
          b.classList.toggle("active", isAll);
          b.setAttribute("aria-pressed", String(isAll));
        });
        render();
      });
      return;
    }

    grid.innerHTML = filtered.map(createProjectCard).join("");
  };

  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      filterBtns.forEach((b) => {
        b.classList.remove("active");
        b.setAttribute("aria-pressed", "false");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-pressed", "true");
      activeCategory = btn.dataset.filter;
      render();
    });
  });

  if (searchInput) {
    searchInput.addEventListener("input", (event) => {
      searchQuery = event.target.value;
      render();
    });
  }

  render();
}