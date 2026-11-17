(function () {
  "use strict";

  const partner = getUserName();
  const partnerName = PP.readJSON("pp-partner-name", partner);
  const presence = document.getElementById("partner-presence");
  const presenceText = presence && presence.querySelector(".pp-presence-text");
  const awayBanner = document.getElementById("away-banner");
  const socket = new WebSocket(PP.wsUrl("/ws/chat/status/"));
  let misses = 0;
  let here = false;
  let typing = false;

  function render() {
    if (!presence) return;
    let state = "unknown", text = "Waiting for " + partnerName + "…";
    if (typing) { state = "typing"; text = "typing…"; }
    else if (here) { state = "here"; text = "In this chat"; }
    else if (misses >= 2) { state = "away"; text = "Away"; }
    presence.dataset.state = state;
    presenceText.textContent = text;
    if (awayBanner) awayBanner.hidden = !(misses >= 4 && !here);
  }

  function check() {
    if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ check: "livestatus", for: partner }));
  }

  socket.addEventListener("open", check);
  setInterval(check, 3000);

  socket.addEventListener("message", function (e) {
    let data;
    try { data = JSON.parse(e.data); } catch (err) { return; }
    if (data.status === "offline") {
      misses++;
      if (misses >= 2) here = false;
    } else {
      misses = 0;
      here = true;
    }
    render();
  });

  document.addEventListener("pp:typing", function (e) {
    typing = !!e.detail;
    if (typing) { here = true; misses = 0; }
    render();
  });

  render();
})();
