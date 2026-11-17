(function () {
  "use strict";

  const partner = getUserName();
  if (partner === "NULL") return;

  let done = false;
  function check() {
    if (done || window.__ppDeclined) return;
    $.getJSON("/api/room", { user: partner }).done(function (r) {
      if (r.status === true && !done) {
        done = true;
        window.location.href = "/chat/" + encodeURIComponent(partner);
      }
    });
  }
  check();
  setInterval(check, 1500);

  const dots = document.getElementById("waiting-dots");
  let n = 0;
  if (dots) setInterval(function () { n = (n + 1) % 4; dots.textContent = ".".repeat(n); }, 500);
})();
