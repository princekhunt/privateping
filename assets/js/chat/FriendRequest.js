(function () {
  "use strict";
  const box = document.getElementById("friend-request");
  if (!box) return;

  function respond(action) {
    document.getElementById("accept-button").disabled = true;
    document.getElementById("reject-button").disabled = true;
    $.ajax({
      type: "POST",
      url: box.dataset.url,
      headers: { "X-CSRFToken": PP.csrfToken() },
      data: { request_from: box.dataset.from, action: action },
    }).always(function () {
      window.location.href = "/dashboard";
    });
  }

  document.getElementById("accept-button").addEventListener("click", function () { respond("accept"); });
  document.getElementById("reject-button").addEventListener("click", function () { respond("reject"); });
})();
