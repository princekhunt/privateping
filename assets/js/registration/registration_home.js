document.getElementById("Maincontent").style.display = "none";
document.getElementById("credits").style.display = "none";

document.querySelectorAll("[data-href]").forEach(function (el) {
  el.addEventListener("click", function () { window.location.href = el.dataset.href; });
});

window.addEventListener("load", function () {
  $("#pageloader").fadeOut();
  $("#Maincontent").delay(500).fadeIn();
  $("#credits").delay(500).fadeIn();
});
