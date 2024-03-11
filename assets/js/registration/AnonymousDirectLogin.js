//get cookie
function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

var requestSent = false; // Flag to track if request has been sent

function sendRequest() {
  if (!requestSent) {
    requestSent = true; // Set flag to true to indicate request has been sent
    $.ajax({
      type: "POST",
      url: "",
      data: {
        csrfmiddlewaretoken: getCookie("csrftoken"),
        action: "create",
      },
      success: function (data) {
        if (data.status == "ok") {
          $("#processing").html("Redirecting to Dashboard...");
          window.location = data.redirect;
        }
      },
    });
  }
}

var mouseMoved = false;

function mouseMoveFunction(e) {
  mouseMoved = true;
  $("#processing").html("Anonymously Logging you in...");
  document.removeEventListener("mousemove", mouseMoveFunction);
  setTimeout(sendRequest, 3000);
}

document.addEventListener("mousemove", mouseMoveFunction);

setTimeout(function () {
  if (mouseMoved && !requestSent) {
    sendRequest();
  }
}, 1000);
