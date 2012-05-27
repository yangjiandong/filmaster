$(document).ready(function() {
    $("body").trigger("recommend");
});

$("body").bind("recommend", function(e) {
    $(".odd").removeClass("odd");
    $("ul.recommended-films li:nth-child(2n), body.recommendations ul.movies li:nth-child(2n)").addClass("even");
    $("ul.recommended-films li:nth-child(2n+1), body.recommendations ul.movies li:nth-child(2n+1)").addClass("odd");
});
