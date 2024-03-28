document.getElementById("Maincontent").style.display = "none";
document.getElementById("credits").style.display = "none";

// Hide the loader when the page is fully loaded
window.addEventListener("load", function () {
    $("#pageloader").fadeOut();
    $("#Maincontent").delay(500).fadeIn();
    $("#credits").delay(500).fadeIn();

});
parent.document.title = "PrivatePing: A secure messaging Application";