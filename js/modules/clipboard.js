import { CONTACT_EMAIL } from "../data/portfolio-data.js";

export function initClipboard() {
  const copyBtn = document.getElementById("copy-btn");
  if (!copyBtn) return;

  const defaultLabel = copyBtn.textContent;

  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(CONTACT_EMAIL);
      copyBtn.textContent = "✅ Email Copied!";
      setTimeout(() => {
        copyBtn.textContent = defaultLabel;
      }, 2200);
    } catch {
      copyBtn.textContent = `✉️ ${CONTACT_EMAIL}`;
    }
  });
}