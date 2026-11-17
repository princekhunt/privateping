(function () {
  "use strict";

  const me = PP.readJSON("pp-me", "");
  const partner = getUserName();
  const board = document.getElementById("board");
  const form = document.getElementById("chat-box");
  const field = document.getElementById("msg_field");
  const sendBtn = document.getElementById("send_btn");
  const destroySelect = document.getElementById("MessageDestroy");
  const liveText = document.getElementById("live-notification-text");
  const liveDot = document.getElementById("live-notification-dot");
  const charCount = document.getElementById("char-count");
  const isChat = !!(board && form && field && partner !== "NULL");
  const MAX_CHARS = 2000;
  const ALLOWED_DESTROY = [0, 5, 10, 30, 60, 300, 600, 3600];
  const RETRY_DELAYS = [3000, 6000, 12000, 24000];
  const RESEAL_AFTER_MS = 5 * 60 * 1000;

  let identity = null;
  let peer = null;
  let ready = false;

  const emptyState = document.getElementById("thread-empty");
  const jump = document.getElementById("jump-latest");

  function nearBottom() {
    return !board || board.scrollHeight - board.scrollTop - board.clientHeight < 80;
  }

  function scrollToEnd() {
    if (!board) return;
    board.scrollTop = board.scrollHeight;
    if (jump) jump.hidden = true;
  }

  function appendToThread(el, forceScroll) {
    const stick = forceScroll || nearBottom();
    if (emptyState) emptyState.hidden = true;
    const typing = document.getElementById("fromloader");
    if (typing && el !== typing) board.insertBefore(el, typing); else board.appendChild(el);
    if (stick) scrollToEnd();
    else if (jump && !el.classList.contains("pp-typing")) jump.hidden = false;
  }

  if (board && jump) {
    jump.addEventListener("click", scrollToEnd);
    board.addEventListener("scroll", function () { if (nearBottom()) jump.hidden = true; });
  }

  function timeLabel() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function formatDuration(s) {
    if (s < 60) return s + "s";
    if (s < 3600) return Math.round(s / 60) + " min";
    return Math.round(s / 3600) + " h";
  }

  function systemNote(text, bad) {
    if (!board) return;
    const el = document.createElement("div");
    el.className = "pp-system" + (bad ? " bad" : "");
    el.textContent = text;
    appendToThread(el, false);
  }

  function lastBubble() {
    const items = board.querySelectorAll(".pp-bubble, .pp-system");
    return items.length ? items[items.length - 1] : null;
  }

  function renderMessage(text, mine, destroy) {
    const side = mine ? "pp-out" : "pp-in";
    const box = document.createElement("div");
    box.className = "ChatMessage pp-msg pp-bubble " + side;
    const prev = lastBubble();
    if (prev && prev.classList.contains(side)) {
      box.classList.add("pp-grouped");
      prev.classList.add("pp-grouped-next");
    }
    const h5 = document.createElement("h5");
    h5.textContent = text;
    const meta = document.createElement("small");
    meta.className = "pp-msg-meta";
    if (destroy) {
      const t = document.createElement("span");
      t.className = "pp-timer-badge";
      t.title = "Disappears " + formatDuration(destroy) + " after it was " + (mine ? "sent" : "received");
      const i = document.createElement("i");
      i.className = "fa-solid fa-stopwatch";
      i.setAttribute("aria-hidden", "true");
      t.appendChild(i);
      t.appendChild(document.createTextNode(" " + formatDuration(destroy)));
      meta.appendChild(t);
    }
    const time = document.createElement("span");
    time.textContent = timeLabel();
    time.title = new Date().toLocaleString();
    meta.appendChild(time);
    box.appendChild(h5);
    box.appendChild(meta);
    appendToThread(box, mine);
    if (destroy) destroyer(destroy, box);
    return box;
  }

  const e2ee = document.getElementById("e2ee-state");
  const COLOR_STATE = { green: "ok", orange: "warn", red: "bad" };
  function setLive(text, color) {
    if (liveText) liveText.textContent = text;
    if (e2ee) e2ee.dataset.state = COLOR_STATE[color] || "";
    else if (liveDot) liveDot.style.color = color;
  }

  function updateSendState() {
    if (!isChat) return;
    const len = field.value.length;
    if (charCount) {
      charCount.textContent = len + " / " + MAX_CHARS;
      charCount.hidden = len < MAX_CHARS - 400;
      charCount.classList.toggle("bad", len > MAX_CHARS);
    }
    sendBtn.disabled = !ready || field.value.trim() === "" || len > MAX_CHARS;
  }

  function play(name) {
    new Audio("/static/media/" + name + ".mp3").play().catch(function () {});
  }

  function pageIsSeen() {
    return document.visibilityState === "visible" && document.hasFocus() &&
      (!window.PPIdle || PPIdle.activeWithin(120000));
  }

  let socket1 = null;
  let reconnectDelay = 1000;

  function sendFrame(obj) {
    if (socket1 && socket1.readyState === WebSocket.OPEN) {
      socket1.send(JSON.stringify(obj));
      return true;
    }
    return false;
  }

  function connect() {
    socket1 = new WebSocket(PP.wsUrl("/ws/chat/"));

    socket1.addEventListener("open", function () {
      reconnectDelay = 1000;
      sendFrame({ message: "ping", to: partner === "NULL" ? me : partner, destroy: 0 });
      if (isChat && ready) {
        setLive("End-to-end encrypted", "green");
        announce(true);
        flushOutbox(false);
      }
    });

    socket1.addEventListener("close", function () {
      if (isChat) setLive("Reconnecting…", "orange");
      setTimeout(connect, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 2, 15000);
    });

    socket1.addEventListener("message", onFrame);
  }

  function onFrame(event) {
    let obj;
    try { obj = JSON.parse(event.data); } catch (e) { return; }
    if (!obj || obj.message === "pong") return;

    if (obj.status === "accepted") { markState(obj.mid, "sent"); return; }
    if (obj.status === "error") {
      if (obj.mid && outbox.has(obj.mid)) markFailed(outbox.get(obj.mid), obj.message);
      else if (isChat) systemNote(String(obj.message || "Message could not be delivered."), true);
      return;
    }
    if (!isChat || !identity || !peer) return;

    if (typeof obj.from !== "string" || obj.from !== partner) return;

    if (obj.status === "ready") { onPartnerReady(obj.reply); return; }
    if (obj.status === "receipt") { onReceipt(obj.receipt); return; }
    if (obj.status === "received" && typeof obj.message === "string") onIncoming(obj);
  }

  const readIds = new Set();
  const unreadIds = new Set();
  const receiptQueue = { delivered: new Set(), read: new Set() };
  let receiptTimer = null;

  function queueReceipt(state, id) {
    receiptQueue[state].add(id);
    if (!receiptTimer) receiptTimer = setTimeout(flushReceipts, 120);
  }

  function flushReceipts() {
    receiptTimer = null;
    ["read", "delivered"].forEach(function (state) {
      const ids = Array.from(receiptQueue[state]);
      receiptQueue[state].clear();
      for (let i = 0; i < ids.length; i += 50) {
        const chunk = ids.slice(i, i + 50);
        PPCrypto.signReceipt(state, chunk, me, partner, identity).then(function (receipt) {
          if (!sendFrame({ receipt: receipt, to: partner })) {

          }
        });
      }
    });
  }

  function markSeen() {
    if (!pageIsSeen() || unreadIds.size === 0) return;
    unreadIds.forEach(function (id) { readIds.add(id); queueReceipt("read", id); });
    unreadIds.clear();
  }

  function onIncoming(obj) {
    PPCrypto.open(obj.message, me, partner, peer, identity, obj.mid).then(function (envelope) {
      if (envelope.duplicate) {

        queueReceipt(readIds.has(envelope.id) ? "read" : "delivered", envelope.id);
        return;
      }
      let destroy = parseInt(obj.destroy, 10) || 0;
      if (ALLOWED_DESTROY.indexOf(destroy) === -1) destroy = 0;
      removeTyping();
      renderMessage(envelope.body, false, destroy);
      play("received");
      if (pageIsSeen()) {
        readIds.add(envelope.id);
        queueReceipt("read", envelope.id);
      } else {
        unreadIds.add(envelope.id);
        queueReceipt("delivered", envelope.id);
      }
    }).catch(function (err) {
      console.warn("Rejected message:", err && err.message);
      systemNote("⚠ A message failed verification and was discarded.", true);
    });
  }

  if (isChat) {
    window.addEventListener("focus", markSeen);
    document.addEventListener("visibilitychange", markSeen);
    document.addEventListener("click", markSeen);
    if (window.PPIdle) PPIdle.onActive(markSeen);
  }

  const ORDER = { sending: 0, sent: 1, delivered: 2, read: 3 };
  const outbox = new Map();

  const STATUS_UI = {
    sending: { icon: "fa-regular fa-clock", label: "Sending…", title: "Encrypting and sending" },
    sent: { icon: "fa-solid fa-check", label: "Sent", title: "Accepted by the server - not yet received by your friend" },
    delivered: { icon: "fa-solid fa-check-double", label: "Delivered", title: "Received and verified by your friend's browser" },
    read: { icon: "fa-solid fa-check-double", label: "Read", title: "Your friend has seen this message" },
    failed: { icon: "fa-solid fa-circle-exclamation", label: "Not delivered", title: "Your friend's browser never confirmed this message" },
  };

  function renderStatus(msg) {
    if (!msg.statusEl) return;
    const ui = STATUS_UI[msg.state];
    msg.statusEl.className = "pp-status pp-status-" + msg.state;
    msg.statusEl.title = ui.title;
    msg.statusEl.textContent = "";
    const icon = document.createElement("i");
    icon.className = ui.icon;
    icon.setAttribute("aria-hidden", "true");
    msg.statusEl.appendChild(icon);
    msg.statusEl.appendChild(document.createTextNode(" " + ui.label));
    if (msg.state === "failed") {
      const retry = document.createElement("button");
      retry.type = "button";
      retry.className = "pp-retry";
      retry.textContent = "Retry";
      retry.addEventListener("click", function () { resend(msg, true); });
      msg.statusEl.appendChild(document.createTextNode(" · "));
      msg.statusEl.appendChild(retry);
    }
  }

  function setState(msg, state) {
    msg.state = state;
    renderStatus(msg);
    const bubble = msg.statusEl && msg.statusEl.closest(".pp-bubble");
    if (bubble) bubble.classList.toggle("pp-failed", state === "failed");
    if (ORDER[state] >= ORDER.delivered) {
      clearTimeout(msg.timer);

    }
  }

  function markState(mid, state) {
    const msg = outbox.get(mid);
    if (!msg) return;
    if (state === "sent" && msg.state === "failed") return;
    if (msg.state !== "failed" && ORDER[state] <= ORDER[msg.state]) return;
    setState(msg, state);
  }

  function markFailed(msg, reason) {
    if (ORDER[msg.state] >= ORDER.delivered) return;
    clearTimeout(msg.timer);
    setState(msg, "failed");
    if (reason) msg.statusEl.title = reason;
  }

  function transmit(msg) {
    clearTimeout(msg.timer);
    const sent = sendFrame({ message: msg.wire, to: partner, destroy: msg.destroy, mid: msg.mid });
    if (sent) msg.attempts++;
    const delay = RETRY_DELAYS[Math.min(msg.attempts, RETRY_DELAYS.length) - 1] || RETRY_DELAYS[0];
    msg.timer = setTimeout(function () {
      if (ORDER[msg.state] >= ORDER.delivered || msg.state === "failed") return;
      if (msg.attempts >= RETRY_DELAYS.length + 1) markFailed(msg);
      else resend(msg, false);
    }, delay);
  }

  function resend(msg, manual) {
    if (ORDER[msg.state] >= ORDER.delivered) return;
    if (manual) {
      msg.attempts = 0;
      setState(msg, "sending");
    }
    if (Date.now() - msg.sealedAt > RESEAL_AFTER_MS) {

      PPCrypto.seal(msg.text, me, partner, peer, identity, msg.mid).then(function (wire) {
        msg.wire = wire;
        msg.sealedAt = Date.now();
        transmit(msg);
      });
    } else {
      transmit(msg);
    }
  }

  function flushOutbox(includeFailed) {
    outbox.forEach(function (msg) {
      if (ORDER[msg.state] >= ORDER.delivered) return;
      if (msg.state === "failed") {
        if (!includeFailed) return;
        msg.attempts = 0;
        setState(msg, "sending");
      }
      resend(msg, false);
    });
  }

  function onReceipt(wire) {
    PPCrypto.verifyReceipt(wire, me, partner, peer).then(function (r) {
      r.ids.forEach(function (id) {
        const msg = outbox.get(id);
        if (!msg) return;
        if (msg.state === "failed") msg.state = "sent";
        markState(id, r.state);
      });
    }).catch(function (err) {
      console.warn("Ignored receipt:", err && err.message);
    });
  }

  function announce(first) {

    sendFrame({ ready: first, to: partner });
  }

  function onPartnerReady(isReply) {
    if (!isReply) announce(false);

    flushOutbox(true);
  }

  const socket2 = new WebSocket(PP.wsUrl("/ws/chat/currentstatus/"));
  let typingSent = false;

  function sendStatus(status) {
    if (socket2.readyState === WebSocket.OPEN) socket2.send(JSON.stringify({ status: status, for: partner }));
  }

  function removeTyping() {
    const loader = document.getElementById("fromloader");
    if (loader) loader.remove();
    document.dispatchEvent(new CustomEvent("pp:typing", { detail: false }));
  }

  socket2.addEventListener("open", function () { sendStatus("online"); });

  socket2.addEventListener("message", function (event) {
    if (!isChat) return;
    let obj;
    try { obj = JSON.parse(event.data); } catch (e) { return; }
    if (obj.from && obj.from !== partner) return;
    if (obj.status === "typing" && !document.getElementById("fromloader")) {
      const loader = document.createElement("div");
      loader.id = "fromloader";
      loader.className = "pp-typing";
      loader.setAttribute("aria-label", partner + " is typing");
      for (let i = 0; i < 3; i++) loader.appendChild(document.createElement("span"));
      appendToThread(loader, false);
      document.dispatchEvent(new CustomEvent("pp:typing", { detail: true }));
    } else if (obj.status === "online") {
      removeTyping();
    }
  });

  connect();
  if (!isChat) return;

  function stopTyping() {
    if (typingSent) { sendStatus("online"); typingSent = false; }
  }

  function autoGrow() {
    field.style.height = "auto";
    field.style.height = Math.min(field.scrollHeight, 160) + "px";
  }
  const timerPill = destroySelect.closest(".pp-timer");
  destroySelect.addEventListener("change", function () {
    if (timerPill) timerPill.classList.toggle("is-on", destroySelect.value !== "0");
    field.focus();
  });

  field.addEventListener("input", function () {
    autoGrow();
    updateSendState();
    if (field.value === "") stopTyping();
    else if (!typingSent) { sendStatus("typing"); typingSent = true; }
  });
  field.addEventListener("blur", stopTyping);
  field.addEventListener("keydown", function (e) {

    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      if (!sendBtn.disabled) form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event("submit"));
    }
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    const text = field.value;
    if (!ready || text.trim() === "" || text.length > MAX_CHARS) return;
    let destroy = parseInt(destroySelect.value, 10) || 0;
    if (ALLOWED_DESTROY.indexOf(destroy) === -1) destroy = 0;

    const mid = PPCrypto.newId();
    const box = renderMessage(text, true, destroy);
    const statusEl = document.createElement("span");
    box.querySelector(".pp-msg-meta").appendChild(statusEl);
    const msg = { mid: mid, text: text, destroy: destroy, wire: null, sealedAt: 0, state: "sending",
      attempts: 0, timer: null, statusEl: statusEl };
    outbox.set(mid, msg);
    renderStatus(msg);
    play("sent");
    field.value = "";
    autoGrow();
    stopTyping();
    updateSendState();
    field.focus();

    PPCrypto.seal(text, me, partner, peer, identity, mid).then(function (wire) {
      msg.wire = wire;
      msg.sealedAt = Date.now();
      transmit(msg);
    }).catch(function (err) {
      console.error(err);
      markFailed(msg, "Encryption failed");
    });
  });

  window.addEventListener("beforeunload", function (e) {
    const pending = Array.from(outbox.values()).some(function (m) { return ORDER[m.state] < ORDER.delivered; });
    if (pending) { e.preventDefault(); e.returnValue = ""; }
  });

  const trash = document.getElementById("trash-messages");
  if (trash) {
    trash.addEventListener("click", function () {
      play("delete");
      board.querySelectorAll(".ChatMessage, .pp-system").forEach(function (el) { el.remove(); });
      if (emptyState) emptyState.hidden = false;
      if (jump) jump.hidden = true;
    });
  }

  const friendKeys = PP.readJSON("pp-friend-keys", null);
  const myServerKeys = PP.readJSON("pp-my-keys", null);
  const banner = document.getElementById("key-banner");

  function showBanner() {
    if (banner) banner.hidden = false;
    setLive("Encryption keys missing on this browser", "red");
  }

  setLive("Setting up encryption…", "orange");
  updateSendState();

  Promise.all([PPCrypto.loadIdentity(), PPCrypto.importPeer(friendKeys)]).then(function (r) {
    identity = r[0];
    peer = r[1];
    if (!identity || !identity.encPrivate || !identity.sigPrivate) { showBanner(); return; }
    const mine = { enc: identity.encPublic, sig: identity.sigPublic };
    if (myServerKeys && !PPCrypto.sameKeys(mine, myServerKeys)) { showBanner(); return; }
    ready = true;
    setLive("End-to-end encrypted", "green");
    updateSendState();
    field.focus();
    announce(true);

    const verify = document.getElementById("verify-button");
    if (verify) {
      verify.addEventListener("click", function () {
        PPCrypto.safetyCode(me, mine, partner, friendKeys).then(function (code) {
          const wrap = document.createElement("div");
          const p1 = document.createElement("p");
          p1.textContent = "Compare this code with " + partner + " in person or over a call. " +
            "If it matches on both screens, nobody - not even the server - can read or fake your messages.";
          const codeEl = document.createElement("div");
          codeEl.className = "pp-safety-code";
          code.split(" ").forEach(function (g) {
            const s = document.createElement("span");
            s.textContent = g;
            codeEl.appendChild(s);
          });
          const p2 = document.createElement("small");
          p2.textContent = "The code changes whenever either of you logs in again (new keys are created).";
          wrap.appendChild(p1);
          wrap.appendChild(codeEl);
          wrap.appendChild(p2);
          Swal.fire({ title: "Verify encryption", html: wrap, icon: "info", confirmButtonColor: "#003d89", width: 560 });
        });
      });
    }
  }).catch(function (err) {
    console.error(err);
    showBanner();
  });
})();
