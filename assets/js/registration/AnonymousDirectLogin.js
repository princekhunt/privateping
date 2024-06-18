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

var RequestSent = false;
setInterval(() => {
            //convert to JSON
            var formData = $("#anonymous-direct-login-form").serializeArray().reduce(function(obj, item) {
              obj[item.name] = item.value;
              return obj;
            }, {});
            
            //check the length of h-captcha-response
            if(formData['h-captcha-response'].length < 1){
              return;
            }
            if(RequestSent){
              return;
            }
            RequestSent = true;
        $.ajax({
          type: "POST",
          url: $("#anonymous-direct-login-form").attr('action'),
          data: $("#anonymous-direct-login-form").serialize(),
          success: function(data) {
            if (data.status === "ok") {
              $('#processing').text('Anonymously logging you in...');
                window.location.href = data.redirect;
  
            }
          },
          error: function(xhr, status, error) {
            console.error("An error occurred:", error);
            alert("An error occurred. Please try again.");
          }
        });
}, 1000);


  parent.document.title = "PrivatePing - Anonymous Direct Login";
