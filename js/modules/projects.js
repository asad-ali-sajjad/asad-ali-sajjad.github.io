import { PROJECTS } from "../data/portfolio-data.js";

function createProjectCard(project) {
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

        <a href="${project.repoUrl}" target="_blank" rel="noopener noreferrer"
           class="inline-flex items-center justify-center w-full py-2.5 px-4 rounded-xl text-xs font-mono font-semibold bg-slate-800/80 hover:bg-sky-400 hover:text-slate-950 text-white border border-slate-700 hover:border-sky-400 transition">
          View Source on GitHub &nearr;
        </a>
      </div>
    </article>
  `;
}

export function initProjects() {
  const grid = document.getElementById("projects-grid");
  const filterBtns = document.querySelectorAll(".filter-btn");

  if (!grid) return;

  const render = (filter = "all") => {
    const filtered =
      filter === "all"
        ? PROJECTS
        : PROJECTS.filter((project) => project.category === filter);

    grid.innerHTML = filtered.map(createProjectCard).join("");
  };

  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      filterBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      render(btn.dataset.filter);
    });
  });

  render();
}