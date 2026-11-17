(function () {
  "use strict";

  const status = document.getElementById("processing");
  const errorBox = document.getElementById("keys-error");
  const retry = document.getElementById("keys-retry");

  function fail(message) {
    status.textContent = "Couldn't secure your session";
    errorBox.textContent = message;
    errorBox.hidden = false;
    retry.hidden = false;
  }

  PPCrypto.generateIdentity().then(function (keys) {
    status.textContent = "Registering your public keys…";
    return $.ajax({
      type: "POST",
      url: window.location.pathname,
      headers: { "X-CSRFToken": PP.csrfToken() },
      dataType: "json",
      data: {
        public_key: JSON.stringify(keys.encPublic),
        signing_key: JSON.stringify(keys.sigPublic),
      },
    });
  }).then(function (data) {
    status.textContent = "All set!";
    window.location.href = data.redirect || "/dashboard";
  }).catch(function (err) {
    console.error(err);
    const msg = err && err.responseJSON && err.responseJSON.message;
    fail(msg || (err && err.message) ||
      "Your browser could not create encryption keys. Please use an up-to-date browser and don't use private mode.");
  });
})();
