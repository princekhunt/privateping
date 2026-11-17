(function () {
  "use strict";

  const me = PP.readJSON("pp-me", "");

  PP.paintAvatars(document);

  ["profile-link", "profile-link-side"].forEach(function (id) {
    const profileLink = document.getElementById(id);
    if (!profileLink) return;
    profileLink.addEventListener("click", function () {
      const url = location.origin + "/addfriend/" + encodeURIComponent(me);
      const done = function () {
        Swal.fire({ toast: true, position: "top-end", icon: "success", timer: 3000, showConfirmButton: false,
          title: "Profile link copied", text: "Anyone who opens it can send you a friend request." });
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(done, function () {
          Swal.fire({ title: "Your profile link", input: "text", inputValue: url, confirmButtonColor: "#003d89" });
        });
      } else {
        Swal.fire({ title: "Your profile link", input: "text", inputValue: url, confirmButtonColor: "#003d89" });
      }
    });
  });

  if (document.getElementById("anonymous_info")) {
    let shown = false;
    try { shown = sessionStorage.getItem("pp-anon-info") === "1"; } catch (e) {  }
    if (!shown) {
      setTimeout(function () { $("#anonymous_info").modal("show"); }, 600);
      try { sessionStorage.setItem("pp-anon-info", "1"); } catch (e) {  }
    }
  }

  const logoutForm = document.getElementById("logout-form");
  if (logoutForm) {
    logoutForm.addEventListener("submit", function (e) {
      const button = document.getElementById("logout-button");
      const anonymous = button && button.dataset.anonymous === "true";
      e.preventDefault();
      Swal.fire({
        title: anonymous ? "Delete temporary account?" : "Log out?",
        text: anonymous
          ? "Your temporary account and all its friends will be deleted permanently."
          : "Your encryption keys on this browser will be erased. New keys are created when you log in again.",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#003d89",
        cancelButtonColor: "#d33",
        confirmButtonText: anonymous ? "Yes, delete it" : "Log out",
      }).then(function (result) {
        if (result.isConfirmed) logoutForm.submit();
      });
    });
  }

  const content = document.getElementById("ChatScreen");
  if (content) {
    let locked = false;
    const blur = function () { content.classList.add("blurred"); };
    const unblur = function () { if (!locked) content.classList.remove("blurred"); };
    window.addEventListener("blur", blur);
    window.addEventListener("focus", unblur);
    content.addEventListener("click", unblur);

    const screenshotWarning = function () {
      locked = true;
      blur();
      try { navigator.clipboard.writeText(""); } catch (e) {  }
      Swal.fire({
        title: "Attention!",
        text: "Screenshots are not allowed!",
        icon: "warning",
        confirmButtonColor: "#003d89",
        confirmButtonText: "Okay",
        allowOutsideClick: false,
      }).then(function () { locked = false; unblur(); });
    };

    document.addEventListener("keyup", function (e) {
      if (e.key === "PrintScreen") { e.preventDefault(); screenshotWarning(); }
    });

    document.addEventListener("keydown", function (e) {
      if (e.metaKey && e.shiftKey && ["3", "4", "5"].indexOf(e.key) !== -1) blur();
    });
  }
})();
