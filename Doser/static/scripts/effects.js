$(document).ready(function () {
  // Hamburgermenu
  $("#menu").click(function (event) {
    $( "#nav" ).toggleClass( "hidden" );
  });
  // Hide Alert
  $("#close").click(function (event) {
    $( "#alert" ).toggleClass( "hidden" );
  });
});
