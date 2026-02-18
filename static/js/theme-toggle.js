/**
 * Theme toggle: supports light / dark mode
 * - Default: follows system prefers-color-scheme (no data-theme set on <html>)
 * - After user manually toggles: saves preference to localStorage
 * - Utterances comment iframe theme is updated on switch
 */

(function () {
  const STORAGE_KEY = "color-theme";
  const DARK = "dark";
  const LIGHT = "light";

  function getSystemTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? DARK
      : LIGHT;
  }

  function getActiveTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === DARK || saved === LIGHT) return saved;
    return getSystemTheme();
  }

  function applyTheme(theme) {
    const html = document.documentElement;
    if (theme === DARK) {
      html.setAttribute("data-theme", DARK);
    } else {
      html.setAttribute("data-theme", LIGHT);
    }
    updateToggleUI(theme);
    updateUtterancesTheme(theme);
  }

  function updateToggleUI(theme) {
    document.querySelectorAll(".theme-toggle").forEach(function (btn) {
      if (theme === DARK) {
        btn.setAttribute("title", "切換為淺色模式");
        btn.innerHTML = '<span aria-hidden="true">☀️</span> <span class="theme-toggle-label">淺色</span>';
      } else {
        btn.setAttribute("title", "切換為深色模式");
        btn.innerHTML = '<span aria-hidden="true">🌙</span> <span class="theme-toggle-label">深色</span>';
      }
    });
  }

  function updateUtterancesTheme(theme) {
    const iframe = document.querySelector(".utterances-frame");
    if (!iframe) return;
    const utterancesTheme = theme === DARK ? "github-dark" : "github-light";
    iframe.contentWindow.postMessage(
      { type: "set-theme", theme: utterancesTheme },
      "https://utteranc.es"
    );
  }

  function toggleTheme() {
    const current = getActiveTheme();
    const next = current === DARK ? LIGHT : DARK;
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  }

  // Apply theme immediately on load (before DOMContentLoaded to avoid flash)
  applyTheme(getActiveTheme());

  document.addEventListener("DOMContentLoaded", function () {
    // Attach click to all toggle buttons (mobile topbar + desktop nav)
    document.querySelectorAll(".theme-toggle").forEach(function (btn) {
      btn.addEventListener("click", toggleTheme);
    });
    // Re-sync UI after DOM is ready
    updateToggleUI(getActiveTheme());

    // Listen for system preference changes (if user hasn't manually set a preference)
    window
      .matchMedia("(prefers-color-scheme: dark)")
      .addEventListener("change", function (e) {
        if (!localStorage.getItem(STORAGE_KEY)) {
          applyTheme(e.matches ? DARK : LIGHT);
        }
      });
  });
})();
