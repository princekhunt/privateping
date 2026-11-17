(function (global) {
  "use strict";

  let last = Date.now();
  const beforeActive = [];
  const onActive = [];
  let lastMove = 0;

  function mark(e) {
    if (e && e.type === "mousemove") {
      const now = Date.now();
      if (now - lastMove < 1000) return;
      lastMove = now;
    }
    if (e && e.type === "visibilitychange" && document.visibilityState !== "visible") return;
    const idleFor = Date.now() - last;
    beforeActive.forEach(function (fn) { try { fn(idleFor); } catch (err) { console.error(err); } });
    last = Date.now();
    onActive.forEach(function (fn) { try { fn(); } catch (err) { console.error(err); } });
  }

  ["mousedown", "mousemove", "keydown", "wheel", "touchstart", "focus", "visibilitychange"].forEach(function (t) {
    (t === "focus" ? window : document).addEventListener(t, mark, { capture: true, passive: true });
  });

  global.PPIdle = {
    idleFor: function () { return Date.now() - last; },
    activeWithin: function (ms) { return Date.now() - last < ms; },
    beforeActive: function (fn) { beforeActive.push(fn); },
    onActive: function (fn) { onActive.push(fn); },
  };
})(window);
