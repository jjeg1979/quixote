$(document).ready(function() {
    $('#backtest-form').submit(function(event) {
    event.preventDefault();
    var form = $(this);
    var url = form.attr('action');
    var formData = new FormData(form[0]);
    var progressBar = $('.progress');
    progressBar.show();
    $.ajax({
        xhr: function() {
        var xhr = new window.XMLHttpRequest();
        xhr.upload.addEventListener('progress', function(evt) {
            if (evt.lengthComputable) {
            var percentComplete = evt.loaded / evt.total;
            percentComplete = parseInt(percentComplete * 100);
            var progressbar = $('.progress-bar');
            progressbar.width(percentComplete + '%');
            progressbar.attr('aria-valuenow', percentComplete);
            progressbar.text(percentComplete + '%');
            }
        }, false);
        return xhr;
        },
        type: 'POST',
        url: url,
        data: formData,
        processData: false,
        contentType: false,
        success: function(data) {
        var result = $('#result');
        var progressBar = $('.progress');
        progressBar.hide();
        result.show();
        },
        error: function() {
        alert('Ha ocurrido un error.');
        }
    });
    });
});


