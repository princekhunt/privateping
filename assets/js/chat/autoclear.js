(function () {
  "use strict";

  const board = document.getElementById("board");
  const select = document.getElementById("autoclear-select");
  const bar = document.getElementById("idle-warning");
  const countdown = document.getElementById("idle-countdown");
  const stay = document.getElementById("idle-stay");
  const emptyState = document.getElementById("thread-empty");
  const jump = document.getElementById("jump-latest");
  if (!board || !select || !window.PPIdle) return;

  const KEY = "pp-autoclear";
  const DEFAULT = 600;
  const baseTitle = document.title;
  let period = DEFAULT;

  try {
    const saved = localStorage.getItem(KEY);
    if (saved !== null && select.querySelector('option[value="' + parseInt(saved, 10) + '"]')) period = parseInt(saved, 10);
  } catch (e) { }
  select.value = String(period);

  select.addEventListener("change", function () {
    period = parseInt(select.value, 10) || 0;
    try { localStorage.setItem(KEY, String(period)); } catch (e) { }
    hideWarning();
    Swal.fire({
      toast: true, position: "top-end", icon: "success", timer: 3000, showConfirmButton: false,
      title: period ? "Auto-clear after " + label(period) + " of inactivity" : "Auto-clear turned off",
    });
  });

  function label(s) {
    return s < 60 ? s + " seconds" : (s / 60) + (s === 60 ? " minute" : " minutes");
  }

  function warnWindow() {
    return Math.min(30, Math.floor(period / 2));
  }

  function hasMessages() {
    return !!board.querySelector(".ChatMessage");
  }

  function hideWarning() {
    if (bar) bar.hidden = true;
    document.title = baseTitle;
  }

  function clearNow(idleSeconds) {
    board.querySelectorAll(".ChatMessage, .pp-system, .pp-typing").forEach(function (el) { el.remove(); });
    if (jump) jump.hidden = true;
    hideWarning();
    const note = document.createElement("div");
    note.className = "pp-system";
    note.textContent = "Messages were cleared after " + label(period) + " of inactivity.";
    board.appendChild(note);
    if (emptyState) emptyState.hidden = true;
    document.dispatchEvent(new CustomEvent("pp:autocleared", { detail: idleSeconds }));
  }

  PPIdle.beforeActive(function (idleMs) {
    if (period && hasMessages() && idleMs >= period * 1000) clearNow(Math.round(idleMs / 1000));
  });
  PPIdle.onActive(hideWarning);

  if (stay) stay.addEventListener("click", hideWarning);

  setInterval(function () {
    if (!period || !hasMessages()) { hideWarning(); return; }
    const idle = PPIdle.idleFor() / 1000;
    const left = Math.ceil(period - idle);
    if (left <= 0) { clearNow(Math.round(idle)); return; }
    if (left <= warnWindow()) {
      if (bar) bar.hidden = false;
      const m = Math.floor(left / 60), s = left % 60;
      if (countdown) countdown.textContent = m + ":" + String(s).padStart(2, "0");
      document.title = (left % 2 ? "⚠ " : "") + "Clearing messages in " + left + "s";
    } else {
      hideWarning();
    }
  }, 1000);
})();
