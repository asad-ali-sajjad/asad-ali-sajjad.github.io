import { initProjects } from "./modules/projects.js";
import { initTypewriter } from "./modules/typewriter.js";
import { initClipboard } from "./modules/clipboard.js";

document.addEventListener("DOMContentLoaded", () => {
  initProjects();
  initTypewriter();
  initClipboard();
});