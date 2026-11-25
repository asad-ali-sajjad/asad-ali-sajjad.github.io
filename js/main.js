import { initNavigation } from "./modules/navigation.js";
import { initProjects } from "./modules/projects.js";
import { initTypewriter } from "./modules/typewriter.js";
import { initClipboard } from "./modules/clipboard.js";
import { initAnimations } from "./modules/animations.js";

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initProjects();
  initTypewriter();
  initClipboard();
  initAnimations();
});