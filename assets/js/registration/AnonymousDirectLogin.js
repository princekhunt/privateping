(function () {
  "use strict";

  const form = document.getElementById("anonymous-direct-login-form");
  const button = document.getElementById("submit-button");
  const errorBox = document.getElementById("anon-error");
  const status = document.getElementById("pow-status");
  const bar = document.getElementById("pow-bar");
  const text = document.getElementById("pow-text");

  let challenge = PP.readJSON("pp-pow", null);
  let solution = null;
  let wantSubmit = false;
  let worker = null;

  function setText(msg) {
    text.textContent = "";
    const icon = document.createElement("i");
    icon.className = "fa-solid fa-shield-halved";
    icon.setAttribute("aria-hidden", "true");
    text.appendChild(icon);
    text.appendChild(document.createTextNode(" " + msg));
  }

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.hidden = false;
  }

  function setBusy(label) {
    button.disabled = true;
    button.textContent = "";
    const spin = document.createElement("span");
    spin.className = "pp-spinner";
    button.appendChild(spin);
    button.appendChild(document.createTextNode(label));
  }

  function resetButton() {
    button.disabled = false;
    button.textContent = "Start chatting anonymously";
  }

  function solve() {
    if (!window.Worker || !window.crypto || !crypto.subtle) {
      showError("Your browser is too old to continue anonymously. Please update it or create an account.");
      return;
    }
    solution = null;
    status.classList.remove("is-done");
    bar.style.width = "3%";
    if (worker) worker.terminate();
    worker = new Worker("/static/js/registration/pow-worker.js");
    const expected = Math.pow(2, challenge.bits);
    const started = performance.now();
    worker.onmessage = function (e) {
      if (!e.data.done) {
        bar.style.width = Math.min(95, 3 + (e.data.tried / expected) * 92) + "%";
        return;
      }
      solution = { challenge: challenge.challenge, nonce: e.data.nonce };
      bar.style.width = "100%";
      status.classList.add("is-done");
      const secs = ((performance.now() - started) / 1000).toFixed(1);
      setText("Verified on your device in " + secs + "s. Nothing was tracked.");
      worker.terminate();
      worker = null;
      if (wantSubmit) submit();
    };
    worker.onerror = function () { showError("Verification failed to start. Please reload the page."); };
    worker.postMessage({ challenge: challenge.challenge, bits: challenge.bits });
  }

  function submit() {
    if (!solution) {
      wantSubmit = true;
      setBusy("Verifying…");
      return;
    }
    wantSubmit = false;
    setBusy("Creating your account…");
    const data = new URLSearchParams();
    data.set("csrfmiddlewaretoken", PP.csrfToken());
    data.set("challenge", solution.challenge);
    data.set("nonce", solution.nonce);
    data.set("website", document.getElementById("website").value);
    fetch(window.location.pathname, {
      method: "POST",
      credentials: "same-origin",
      headers: { "X-CSRFToken": PP.csrfToken(), "Content-Type": "application/x-www-form-urlencoded" },
      body: data.toString(),
    }).then(function (r) {
      return r.json().catch(function () { return { status: "error" }; });
    }).then(function (r) {
      if (r.status === "ok") {
        button.lastChild.textContent = "Logging you in…";
        window.location.href = r.redirect;
        return;
      }
      if (r.retry) {

        return fetch("/api/anonymous_challenge/", { credentials: "same-origin" })
          .then(function (res) { return res.json(); })
          .then(function (c) { challenge = c; wantSubmit = true; solve(); });
      }
      resetButton();
      showError(r.message || "Something went wrong. Please try again.");
    }).catch(function () {
      resetButton();
      showError("Network error. Please check your connection and try again.");
    });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    errorBox.hidden = true;
    submit();
  });

  if (challenge) solve();
  else showError("Couldn't start verification. Please reload the page.");
})();
