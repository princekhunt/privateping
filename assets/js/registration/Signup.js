document.getElementById("name").focus();
document
  .getElementById("name-button")
  .addEventListener("click", function (event) {
    event.preventDefault();

    document.getElementById("name-field").style.transform = "translateX(-400%)";
    document.getElementById("name-field").style.transition =
      "transform 0.5s ease";
    //wait
    setTimeout(function () {
      document.getElementById("name-field").style.display = "none";
      document.getElementById("username-field").style.display = "block";
      document.getElementById("username-field").style.transform =
        "translateX(300%)";
      document.getElementById("username-field").style.transition =
        "transform 0.4s ease";
      setTimeout(function () {
        document.getElementById("username-field").style.transform =
          "translateX(0%)";
        document.getElementById("username").focus();
      }, 200);
    }, 400);
  });

document.getElementById("username-field").focus();
document
  .getElementById("username-button")
  .addEventListener("click", function (event) {
    event.preventDefault();

    document.getElementById("username-field").style.transform =
      "translateX(-400%)";
    document.getElementById("username-field").style.transition =
      "transform 0.5s ease-in-out";
    //wait
    setTimeout(function () {
      document.getElementById("username-field").style.display = "none";
      document.getElementById("password-field-1").style.display = "block";
      document.getElementById("password-field-1").style.transform =
        "translateX(300%)";
      document.getElementById("password-field-1").style.transition =
        "transform 0.4s ease-in-out ";
      setTimeout(function () {
        document.getElementById("password-field-1").style.transform =
          "translateX(0%)";
        document.getElementById("password-1").focus();
        //append text into password-text
        setTimeout(function () {
          $("#password-text").html(
            "Your password must be 8-20 characters long,<br>contain letters and numbers, and must not<br>contain spaces, special characters, or emoji."
          );
        }, 1000);
      }, 200);
    }, 400);
  });

document.getElementById("password-field-1").focus();
document
  .getElementById("password-1-button")
  .addEventListener("click", function (event) {
    event.preventDefault();

    document.getElementById("password-field-1").style.transform =
      "translateX(-400%)";
    document.getElementById("password-field-1").style.transition =
      "transform 0.5s ease-in-out";
    //wait
    setTimeout(function () {
      document.getElementById("password-field-1").style.display = "none";
      document.getElementById("password-field-2").style.display = "block";
      document.getElementById("password-field-2").style.transform =
        "translateX(300%)";
      document.getElementById("password-field-2").style.transition =
        "transform 0.4s ease-in-out ";
      setTimeout(function () {
        document.getElementById("password-field-2").style.transform =
          "translateX(0%)";
        document.getElementById("password-2").focus();
      }, 200);
    }, 400);
  });
//make enter button as submit button
document
  .getElementById("password-field-2")
  .addEventListener("keyup", function (event) {
    event.preventDefault();
    if (event.keyCode === 13) {
      document.getElementById("login-button").click();
    }
  });
document
  .getElementById("login-button")
  .addEventListener("click", function (event) {
    event.preventDefault();
    document.getElementById("LoginForm").style.display = "none";
    $("#processing").html("Hang tight!");

    document.getElementById("LoginForm").submit();
  });

//disable enter and return key
document.addEventListener("keydown", function (event) {
  if (event.keyCode === 13) {
    event.preventDefault();
  }
});

//make ajax request to check username before move
$(document).ready(function () {
  $("#username").keyup(function () {
    var username = $(this).val();
    $.ajax({
      url: "/api/check_username/",
      data: {
        username: username,
      },
      dataType: "json",
      success: function (data) {
        if (data.status == "ok") {
          if (data.available) {
            $("#username").css("border", "2px solid green");
            $("#username-button").css("background-color", "#007bff");
            $("#username-button").css("cursor", "pointer");
            $("#username-button").prop("disabled", false);
            $("#username-error-field").text("");
          } else {
            $("#username").css("border", "2px solid red");
            $("#username-button").css("background-color", "red");
            $("#username-button").css("cursor", "not-allowed");
            $("#username-button").prop("disabled", true);
            $("#username-error-field").text("Username already taken!");
          }
        } else {
          alert("Something went wrong!");
        }
      },
    });
  });
});

//check if password match
$("#password-2").keyup(function () {
  var password_1 = $("#password-1").val();
  var password_2 = $("#password-2").val();
  if (password_1 == password_2) {
    $("#password-2").css("border", "2px solid green");
    $("#login-button").css("background-color", "#007bff");
    $("#login-button").css("cursor", "pointer");
    $("#login-button").prop("disabled", false);
  } else {
    $("#password-2").css("border", "2px solid red");
    $("#login-button").css("background-color", "red");
    $("#login-button").css("cursor", "not-allowed");
    $("#login-button").prop("disabled", true);
  }
});

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

parent.document.title = "PrivatePing - Signup";