(function () {
  "use strict";

  const form = document.getElementById("auth-form");
  if (!form) return;
  const mode = form.dataset.mode;
  const submit = document.getElementById("submit-button");
  const USERNAME_RE = /^[A-Za-z0-9_]{5,20}$/;

  function field(id) { return document.getElementById("field-" + id); }
  function input(id) { return document.getElementById(id); }

  function setState(id, state, message) {
    const f = field(id);
    if (!f) return;
    f.classList.toggle("is-invalid", state === "invalid");
    f.classList.toggle("is-valid", state === "valid");
    const hint = f.querySelector(".pp-hint");
    if (hint && message !== undefined) hint.textContent = message;
  }

  document.querySelectorAll(".pp-reveal").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const target = input(btn.dataset.target);
      const show = target.type === "password";
      target.type = show ? "text" : "password";
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
      btn.innerHTML = show ? '<i class="fa-regular fa-eye-slash" aria-hidden="true"></i>'
        : '<i class="fa-regular fa-eye" aria-hidden="true"></i>';
      target.focus();
    });
  });

  function busy(label) {
    submit.disabled = true;
    submit.textContent = "";
    const spin = document.createElement("span");
    spin.className = "pp-spinner";
    submit.appendChild(spin);
    submit.appendChild(document.createTextNode(label));
  }

  if (mode === "login") {
    form.addEventListener("submit", function (e) {
      let ok = true;
      if (!input("username").value.trim()) { setState("username", "invalid", "Enter your username."); ok = false; }
      if (!input("password").value) { setState("password", "invalid", "Enter your password."); ok = false; }
      if (!ok) { e.preventDefault(); form.querySelector(".is-invalid input").focus(); return; }
      busy("Logging in…");
    });
    ["username", "password"].forEach(function (id) {
      input(id).addEventListener("input", function () { setState(id, null, ""); });
    });
    return;
  }

  const checks = { name: false, username: false, password1: false, password2: false };
  const defaults = {};
  ["name", "username", "password1"].forEach(function (id) {
    defaults[id] = field(id).querySelector(".pp-hint").textContent;
  });

  function checkName(show) {
    const v = input("name").value.trim();
    checks.name = v.length > 0;
    if (show || v) setState("name", checks.name ? null : "invalid", checks.name ? defaults.name : "Enter a display name.");
    return checks.name;
  }

  let seq = 0;
  let timer = null;
  function checkUsername() {
    const v = input("username").value;
    clearTimeout(timer);
    checks.username = false;
    if (!v) { setState("username", null, defaults.username); return; }
    if (!USERNAME_RE.test(v)) {
      setState("username", "invalid", v.length < 5 ? "At least 5 characters." :
        "Only letters, numbers and _ (max 20).");
      return;
    }
    setState("username", null, "Checking…");
    timer = setTimeout(function () {
      const mine = ++seq;
      $.getJSON("/api/check_username/", { username: v }).done(function (r) {
        if (mine !== seq) return;
        checks.username = !!r.available;
        setState("username", r.available ? "valid" : "invalid",
          r.available ? "✓ " + v + " is available" : "That username is taken.");
      }).fail(function () {
        if (mine !== seq) return;
        checks.username = true;
        setState("username", null, defaults.username);
      });
    }, 300);
  }

  function checkPassword(show) {
    const v = input("password1").value;
    let msg = "";
    if (v.length < 10) msg = "At least 10 characters (" + v.length + "/10).";
    else if (/^\d+$/.test(v)) msg = "Can't be only numbers.";
    else if (input("username").value && v.toLowerCase().indexOf(input("username").value.toLowerCase()) !== -1) {
      msg = "Shouldn't contain your username.";
    }
    checks.password1 = !msg;
    if (!v && !show) setState("password1", null, defaults.password1);
    else setState("password1", msg ? "invalid" : "valid", msg || "✓ Looks good");
    if (input("password2").value) checkConfirm(false);
    return checks.password1;
  }

  function checkConfirm(show) {
    const a = input("password1").value, b = input("password2").value;
    checks.password2 = b !== "" && a === b;
    if (!b && !show) setState("password2", null, "");
    else setState("password2", checks.password2 ? "valid" : "invalid",
      checks.password2 ? "✓ Passwords match" : "Passwords don't match.");
    return checks.password2;
  }

  input("name").addEventListener("blur", function () { checkName(false); });
  input("name").addEventListener("input", function () { if (field("name").classList.contains("is-invalid")) checkName(false); });
  input("username").addEventListener("input", checkUsername);
  input("password1").addEventListener("input", function () { checkPassword(false); });
  input("password2").addEventListener("input", function () { checkConfirm(false); });

  if (input("username").value) checkUsername();

  form.addEventListener("submit", function (e) {
    checkName(true);
    checkPassword(true);
    checkConfirm(true);
    if (!checks.username && USERNAME_RE.test(input("username").value) && !field("username").classList.contains("is-invalid")) {
      checks.username = true;
    }
    if (!input("username").value) setState("username", "invalid", "Choose a username.");
    const firstBad = ["name", "username", "password1", "password2"].find(function (k) { return !checks[k]; });
    if (firstBad) {
      e.preventDefault();
      input(firstBad).focus();
      return;
    }
    busy("Creating account…");
  });
})();
