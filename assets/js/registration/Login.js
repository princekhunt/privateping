document.getElementById("username").focus();
document
  .getElementById("username-button")
  .addEventListener("click", function (event) {
    event.preventDefault();
    const username = document.getElementById("username").value.trim();
    if (username == "") {
      document.getElementById("err_mssg").innerHTML = "username is required!";
      return false 
    }
    else {   
        document.getElementById("err_mssg").innerHTML = ""; 
        document.getElementById("username-form").style.transform =
          "translateX(-400%)";
        document.getElementById("username-form").style.transition =
          "transform 0.5s ease-in-out";
        setTimeout(function () {
          document.getElementById("username-form").style.display = "none";
          document.getElementById("password-field").style.display = "flex";
          document.getElementById("password-field").style.transform = "translateX(300%)";
          document.getElementById("password-field").style.transition = "transform 0.4s ease-in-out ";
            setTimeout(function () {
                document.getElementById("password-field").style.transform = "translateX(0%)";
                document.getElementById("password").focus();
              }, 200);
        }, 400);
  }});

//form submit

//make enter button as submit button
document.getElementById("password").addEventListener("keyup", function (event) {
  event.preventDefault();
  if (event.keyCode === 13) {
    document.getElementById("login-button").click();
  }
});


function FormProcessing() {
  event.preventDefault();
  document.getElementById("LoginForm").style.display = "none";
  document.getElementById("processing").innerHTML = "Logging you in...";

  document.getElementById("LoginForm").submit();
}

var login_button = document.getElementById("login-button");
login_button.addEventListener("click", FormProcessing);
login_button.addEventListener("submit", FormProcessing);


// Hide the loader when the page is fully loader
document.getElementById("Maincontent").style.display = "none";

window.addEventListener("load", function () {
  $("#pageloader").fadeOut();
  $("#Maincontent").delay(500).fadeIn();
});

//goback
function goback(){
  window.history.back();

}

parent.document.title = "PrivatePing - Login";