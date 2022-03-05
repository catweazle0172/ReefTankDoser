// Promisify setTimeout
const delay = (m) => new Promise((r) => setTimeout(r, m));

// Hide Alert after Time
const closePopup = async (time) => {
  await delay(time);
  $("#alert").slideUp("slow", function () {
    $("#alert").addClass("hidden");
  });
};

$(document).ready(function () {
  // Hamburgermenu
  $("#menu").click(function (event) {
    $("#nav").slideToggle("slow", function () {
      $("#nav").toggleClass("hidden");
    });
  });

  // Hide Alert
  $("#close").click(function (event) {
    $("#alert").slideUp("slow", function () {
      $("#alert").addClass("hidden");
    });
  });
});
