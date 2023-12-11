const CURRENT_PAGE = '&page='+document.getElementById('cr-pg').textContent;
var page = parseInt(document.getElementById('cr-pg').textContent);
var total_lines = parseInt(document.getElementById('total_lines').textContent);
var emptyPage = false;
var blockRequest = false;

document.querySelector('.but-next-page')
                .addEventListener('click', function(c) {
    blockRequest = true;
    page += 1;
    fetch('?' + window.location.search.replace('?', '').replace(CURRENT_PAGE, '') + '&list_only=1&page=' + page)
    .then(response => response.text())
    .then(html => {
        if (html === '') {
            emptyPage = true;
        }
        else {
            var list = document.getElementById('list');
            list.insertAdjacentHTML('beforeEnd', html);
            document.getElementById('tot-lines-js').remove();
            total_lines += parseInt(document.getElementById('tot-lines-js').textContent);
            document.getElementById('total_lines').textContent = total_lines;

            $('*[data-href]').on('dblclick touchend', function() {
            window.location = $(this).data("href");
            });

            blockRequest = false;
        }
    })
    })
