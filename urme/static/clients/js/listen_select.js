function listen_select(value) {
    var date_select = document.querySelector('#per').children;
    date_select = Array.from(date_select);
    date_select.forEach( elem => {
        console.log(elem)
        if (elem.id == value) {
            elem.style.display = 'block';
        }
        else {
            elem.style.display = 'none';
        }
    });        
}