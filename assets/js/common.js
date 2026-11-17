(function (global) {
  "use strict";

  function readJSON(id, fallback) {
    const el = document.getElementById(id);
    if (!el) return fallback;
    try { return JSON.parse(el.textContent); } catch (e) { return fallback; }
  }

  function csrfToken() {
    const input = document.querySelector("input[name=csrfmiddlewaretoken]");
    if (input) return input.value;
    const meta = document.querySelector("meta[name=csrf-token]");
    return meta ? meta.content : "";
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function wsUrl(path) {
    return (location.protocol === "https:" ? "wss" : "ws") + "://" + location.host + path;
  }

  function initFlash() {
    document.querySelectorAll(".pp-flash").forEach(function (el, i) {
      const close = el.querySelector(".pp-flash-close");
      const hide = function () {
        el.classList.add("pp-flash-hide");
        setTimeout(function () { el.remove(); }, 400);
      };
      if (close) close.addEventListener("click", hide);
      setTimeout(hide, 6000 + i * 800);
    });
  }

  function paintAvatars(root) {
    (root || document).querySelectorAll(".pp-avatar").forEach(function (el) {
      const seed = el.dataset.seed || "";
      let h = 0;
      for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
      el.style.backgroundColor = "hsl(" + (h % 360) + ", 55%, 48%)";
    });
  }

  function setTitle(title) {
    document.title = title;
    try {
      if (global.parent && global.parent !== global) global.parent.document.title = title;
    } catch (e) {  }
  }

  document.addEventListener("click", function (e) {
    const back = e.target.closest("[data-action=back]");
    if (back) {
      e.preventDefault();
      if (history.length > 1) history.back(); else location.href = "/";
    }
  });

  document.addEventListener("DOMContentLoaded", function () {
    initFlash();
    const title = document.body && document.body.dataset.title;
    if (title) setTitle(title);
  });

  global.PP = {
    readJSON: readJSON,
    csrfToken: csrfToken,
    escapeHtml: escapeHtml,
    wsUrl: wsUrl,
    setTitle: setTitle,
    paintAvatars: paintAvatars,
  };

  global.escapeHtml = escapeHtml;
})(window);
