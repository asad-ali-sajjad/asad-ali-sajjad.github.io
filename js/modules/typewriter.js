import { ROLES } from "../data/portfolio-data.js";

export function initTypewriter() {
  const typedEl = document.getElementById("typed-role");
  if (!typedEl || ROLES.length === 0) return;

  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  if (prefersReducedMotion) {
    typedEl.textContent = ROLES[0];
    return;
  }

  let roleIdx = 0;
  let charIdx = 0;
  let isDeleting = false;

  function typeLoop() {
    const current = ROLES[roleIdx];
    typedEl.textContent = isDeleting
      ? current.substring(0, charIdx--)
      : current.substring(0, charIdx++);

    let speed = isDeleting ? 45 : 85;

    if (!isDeleting && charIdx === current.length + 1) {
      isDeleting = true;
      speed = 1600;
    } else if (isDeleting && charIdx === 0) {
      isDeleting = false;
      roleIdx = (roleIdx + 1) % ROLES.length;
      speed = 350;
    }

    setTimeout(typeLoop, speed);
  }

  typeLoop();
}