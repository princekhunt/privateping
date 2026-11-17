(function () {
  "use strict";
  function leave() {
    try { sessionStorage.clear(); } catch (e) {  }
    try { localStorage.clear(); } catch (e) {  }
    (window.top || window).location.href = "/";
  }
  PPCrypto.wipe().then(leave, leave);
  setTimeout(leave, 3000);
})();
