// Get cookie
function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

$(document).ready(function() {
  var requestSent = false; // Flag to track if request has been sent

  function sendRequest() {
    if (!requestSent) {
      requestSent = true; // Set flag to true to indicate request has been sent
      $.ajax({
        type: "POST",
        url: $("#anonymous-direct-login-form").attr('action'),
        data: $("#anonymous-direct-login-form").serialize(),
        headers: {
          'X-CSRFToken': getCookie("csrftoken")
        },
        success: function(data) {
          if (data.status === "ok") {
            $("#processing").html("Redirecting to Dashboard...");
            window.location.href = data.redirect;
          }
        },
        error: function(xhr, status, error) {
          console.error("An error occurred:", error);
          alert("An error occurred. Please try again.");
        }
      });
    }
  }

  parent.document.title = "PrivatePing - Anonymous Direct Login";
});
