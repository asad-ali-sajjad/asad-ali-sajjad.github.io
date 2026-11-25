export function initNavigation() {
  const menuBtn = document.getElementById("mobile-menu-btn");
  const mobileMenu = document.getElementById("mobile-menu");
  const openIcon = document.getElementById("menu-icon-open");
  const closeIcon = document.getElementById("menu-icon-close");
  const mobileLinks = document.querySelectorAll("[data-mobile-link]");
  const navLinks = document.querySelectorAll("[data-nav-link]");
  const backToTopBtn = document.getElementById("back-to-top");

  const setMenuOpen = (isOpen) => {
    if (!menuBtn || !mobileMenu) return;
    mobileMenu.classList.toggle("hidden", !isOpen);
    menuBtn.setAttribute("aria-expanded", String(isOpen));
    openIcon?.classList.toggle("hidden", isOpen);
    closeIcon?.classList.toggle("hidden", !isOpen);
  };

  if (menuBtn && mobileMenu) {
    menuBtn.addEventListener("click", () => {
      const isCurrentlyOpen = menuBtn.getAttribute("aria-expanded") === "true";
      setMenuOpen(!isCurrentlyOpen);
    });

    mobileLinks.forEach((link) => {
      link.addEventListener("click", () => setMenuOpen(false));
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") setMenuOpen(false);
    });

    const header = menuBtn.closest("header");
    document.addEventListener("click", (event) => {
      const isCurrentlyOpen = menuBtn.getAttribute("aria-expanded") === "true";
      if (isCurrentlyOpen && header && !header.contains(event.target)) {
        setMenuOpen(false);
      }
    });
  }

  // Active Section Scroll-Spy
  const sections = document.querySelectorAll("section[id]");
  if (sections.length > 0 && navLinks.length > 0) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const targetId = `#${entry.target.id}`;
            navLinks.forEach((link) => {
              link.classList.toggle("active", link.getAttribute("href") === targetId);
            });
          }
        });
      },
      { rootMargin: "-35% 0px -55% 0px" }
    );

    sections.forEach((section) => observer.observe(section));
  }

  // Back-to-Top Visibility
  if (backToTopBtn) {
    window.addEventListener(
      "scroll",
      () => {
        backToTopBtn.classList.toggle("hidden", window.scrollY < 450);
      },
      { passive: true }
    );

    backToTopBtn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }
}