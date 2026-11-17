function getUserName() {
  const partner = PP.readJSON("pp-partner", null);
  return typeof partner === "string" && partner ? partner : "NULL";
}

function destroyer(delay, element) {
  setTimeout(function () {
    if (!element || !element.parentNode) return;
    element.classList.add("pp-vanish");
    setTimeout(function () { element.remove(); }, 350);
  }, delay * 1000);
}

function markActiveFriend() {
  const partner = getUserName();
  document.querySelectorAll(".pp-friend").forEach(function (li) {
    li.classList.toggle("is-active", li.dataset.username === partner);
  });
}

(function () {
  "use strict";

  const me = PP.readJSON("pp-me", "");
  markActiveFriend();
  const USERNAME_RE = /^[A-Za-z0-9_]{1,20}$/;

  const input = document.getElementById("finduser");
  const button = document.getElementById("adduserbutton");
  const status = document.getElementById("finduser-status");
  const form = document.getElementById("adduserform");
  const note = document.getElementById("note");
  const noteCount = document.getElementById("note-count");

  function setStatus(text, ok) {
    status.textContent = text;
    status.className = "pp-field-status " + (ok ? "ok" : "bad");
    button.disabled = !ok;
  }

  if (input && button && form) {
    let timer = null;
    let seq = 0;
    input.addEventListener("input", function () {
      const username = input.value.trim();
      clearTimeout(timer);
      if (!username) { setStatus("", false); return; }
      if (username === me) { setStatus("That's you!", false); return; }
      if (!USERNAME_RE.test(username)) { setStatus("Usernames only contain letters, digits and _", false); return; }
      timer = setTimeout(function () {
        const mine = ++seq;
        $.getJSON("/api/check_username/", { username: username }).done(function (r) {
          if (mine !== seq) return;
          if (r.status !== "ok") { setStatus("Couldn't check right now, try again.", false); return; }
          if (r.exists && !r.self) setStatus("✓ User found", true);
          else if (r.self) setStatus("That's you!", false);
          else setStatus("No user with this username", false);
        }).fail(function () { setStatus("Couldn't check right now, try again.", false); });
      }, 250);
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (button.disabled) return;
      form.action = "/addfriend/" + encodeURIComponent(input.value.trim());
      button.disabled = true;
      form.submit();
    });
    $("#AddFriend").on("shown.bs.modal", function () { input.focus(); });
  }

  if (note && noteCount) {
    note.addEventListener("input", function () {
      if (note.value.length > 100) note.value = note.value.substring(0, 100);
      noteCount.textContent = note.value.length;
    });
  }

  document.addEventListener("click", function (e) {
      const el = e.target.closest(".pp-delete-friend");
      if (!el) return;
      e.preventDefault();
      e.stopPropagation();
      const friend = el.dataset.username;
      const row = el.closest(".pp-friend");
      const pending = row && !row.classList.contains("pp-friend-friends");
      Swal.fire({
        title: pending ? "Cancel request with " + friend + "?" : "Remove " + friend + "?",
        text: pending ? "The friend request will be withdrawn."
          : "They will be removed from your friend list. You can send a new request later.",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#d33",
        cancelButtonColor: "#3085d6",
        confirmButtonText: "Remove",
      }).then(function (result) {
        if (!result.isConfirmed) return;
        $.ajax({
          url: "/delete_friend",
          type: "POST",
          dataType: "json",
          headers: { "X-CSRFToken": PP.csrfToken() },
          data: { friend: friend },
        }).done(function (response) {
          if (response.status === true) {
            const onThisFriend = getUserName() === friend;
            window.location.href = onThisFriend ? "/dashboard" : window.location.href;
          } else {
            Swal.fire("Error", response.message || "Something went wrong. Please try again.", "error");
          }
        }).fail(function () {
          Swal.fire("Error", "Something went wrong. Please try again.", "error");
        });
      });
  });

  const friendsBox = document.getElementById("friends");
  let refreshing = null;

  function refreshFriends() {
    if (!friendsBox || refreshing) return refreshing;
    refreshing = fetch(friendsBox.dataset.url, { credentials: "same-origin", headers: { "Accept": "text/html" } })
      .then(function (r) { return r.ok ? r.text() : Promise.reject(r.status); })
      .then(function (html) {

        friendsBox.innerHTML = html;
        PP.paintAvatars(friendsBox);
        markActiveFriend();
        applySearch();

        const wasShowing = Array.from(showing);
        showing.clear();
        wasShowing.forEach(function (u) { setWaiting(u, true); });
      })
      .catch(function () {  })
      .then(function () { refreshing = null; });
    return refreshing;
  }

  const FRIEND_EVENTS = {
    request: { icon: "info", text: " sent you a friend request", action: "Review" },
    accepted: { icon: "success", text: " accepted your friend request", action: "Chat now" },
    rejected: { icon: "info", text: " declined your friend request", retry: "You can send a new request in " },
    removed: { icon: "info", text: " removed you from their friends" },
  };

  function onFriendsChanged(data) {
    refreshFriends();
    const info = FRIEND_EVENTS[data.event];
    const from = typeof data.from === "string" && USERNAME_RE.test(data.from) ? data.from : null;
    if (!info || !from) return;
    if (data.event === "removed" && getUserName() === from) {
      Swal.fire({ icon: "info", title: from + " removed you", text: "This chat is closed.",
        confirmButtonColor: "#003d89" }).then(function () { window.location.href = "/dashboard"; });
      return;
    }
    new Audio("/static/media/notification.mp3").play().catch(function () {});
    Swal.fire({
      toast: true,
      position: "top-end",
      icon: info.icon,
      title: from + info.text,
      text: info.retry && data.retry_text ? info.retry + data.retry_text + "." : undefined,
      showConfirmButton: !!info.action,
      confirmButtonText: info.action || "OK",
      confirmButtonColor: "#003d89",
      showCloseButton: true,
      timer: 10000,
      timerProgressBar: true,
    }).then(function (r) {
      if (!r.isConfirmed) return;
      window.location.href = data.event === "request"
        ? "/request?user=" + encodeURIComponent(from)
        : "/waiting-room?user=" + encodeURIComponent(from);
    });
  }

  function onChatDeclined(data) {
    const from = typeof data.from === "string" && USERNAME_RE.test(data.from) ? data.from : null;
    if (!from) return;
    const retry = data.retry_text ? "You can try again in " + data.retry_text + "." : "Please try again later.";
    new Audio("/static/media/notification.mp3").play().catch(function () {});
    if (getUserName() === from && document.getElementById("waiting_text")) {
      window.__ppDeclined = true;
      Swal.fire({
        icon: "info",
        title: from + " declined your chat request",
        text: retry + " The wait gets longer if requests keep getting declined.",
        confirmButtonText: "Back to dashboard",
        confirmButtonColor: "#003d89",
        allowOutsideClick: false,
      }).then(function () { window.location.href = "/dashboard"; });
    } else {
      Swal.fire({ toast: true, position: "top-end", icon: "info", timer: 8000, timerProgressBar: true,
        showConfirmButton: false, showCloseButton: true, title: from + " declined your chat request", text: retry });
    }
  }

  const search = document.getElementById("friend-search");
  function applySearch() {
    if (!friendsBox) return;
    const q = search ? search.value.trim().toLowerCase() : "";
    let any = false;
    friendsBox.querySelectorAll(".pp-friend").forEach(function (li) {
      const match = !q || (li.dataset.search || "").indexOf(q) !== -1;
      li.hidden = !match;
      if (match) any = true;
    });
    friendsBox.querySelectorAll(".pp-group").forEach(function (g) {
      g.hidden = !g.querySelector(".pp-friend:not([hidden])");
    });
    const none = document.getElementById("friend-nomatch");
    if (none) none.hidden = !q || any;
  }
  if (search) {
    search.addEventListener("input", applySearch);
    search.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { search.value = ""; applySearch(); }
      if (e.key === "Enter") {
        const first = friendsBox.querySelector(".pp-friend:not([hidden]) .pp-friend-link");
        if (first) first.click();
      }
    });
  }
  setInterval(function () { if (document.visibilityState === "visible") refreshFriends(); }, 30000);

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") refreshFriends();
  });

  const socket = new WebSocket(PP.wsUrl("/ws/notify/"));
  const ignored = new Set();
  const notified = new Set();
  const showing = new Set();

  function liveSlot(user) {
    return document.getElementById("live_notification_" + user);
  }

  function setWaiting(user, on) {
    const slot = liveSlot(user);
    if (!slot) return;
    const row = slot.closest(".pp-friend");
    if (on && !showing.has(user)) {
      slot.textContent = "Waiting";
      slot.title = user + " is waiting for you in the chat room";
      if (row) row.classList.add("is-waiting");
      showing.add(user);
    } else if (!on && showing.has(user)) {
      slot.textContent = "";
      if (row) row.classList.remove("is-waiting");
      showing.delete(user);
    }
  }

  socket.addEventListener("open", function () {
    socket.send(JSON.stringify({ available: "ping" }));
  });

  socket.addEventListener("message", function (e) {
    let data;
    try { data = JSON.parse(e.data); } catch (err) { return; }
    if (data.status === "friends") { onFriendsChanged(data); return; }
    if (data.status === "declined") { onChatDeclined(data); return; }
    let users = [];
    if (data.status === "notify") {
      try { users = JSON.parse(data.from); } catch (err) { users = []; }
      if (!Array.isArray(users)) users = [];
      users = users.filter(function (u) { return typeof u === "string" && USERNAME_RE.test(u) && u !== getUserName(); });
    }

    Array.from(showing).forEach(function (u) { if (users.indexOf(u) === -1) setWaiting(u, false); });

    users.forEach(function (user) {
      setWaiting(user, true);
      if (ignored.has(user) || notified.has(user)) return;
      notified.add(user);
      new Audio("/static/media/notification.mp3").play().catch(function () {});
      Swal.fire({
        title: user + " is waiting for you",
        text: "Join the secure chat room now?",
        icon: "info",
        position: "top-end",
        toast: true,
        showDenyButton: true,
        confirmButtonText: "Join now",
        denyButtonText: "Decline",
        confirmButtonColor: "#003d89",
        timer: 8000,
        timerProgressBar: true,
      }).then(function (result) {
        if (result.isConfirmed) {
          window.location.href = "/waiting-room?user=" + encodeURIComponent(user);
        } else if (result.isDenied) {
          ignored.add(user);
          setWaiting(user, false);
          $.ajax({
            url: "/api/decline_chat",
            type: "POST",
            dataType: "json",
            headers: { "X-CSRFToken": PP.csrfToken() },
            data: { user: user },
          }).done(function (r) {
            if (r.status) {
              Swal.fire({ toast: true, position: "top-end", icon: "success", timer: 3500,
                showConfirmButton: false, title: "Declined", text: user + " has been told you're not available." });
            }
          });
        }
      });
    });

    Array.from(notified).forEach(function (u) { if (users.indexOf(u) === -1) notified.delete(u); });
  });

  setInterval(function () {
    if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ available: "ping" }));
  }, 3000);
})();
