$(document).ready(function($) {
    $('*[data-href]').on('dblclick touchend', function() {
        window.location = $(this).data("href");
    });
});