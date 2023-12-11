$('#table').dragtable({maxMovingRows:1, persistState: function(table) { 
    table.el.find('th').each(function(i) { 
    if(this.id != '') {
            table.sortOrder[this.id]=i;
            } 
    }); 
    table.sortOrder['table_name'] = window.location.pathname;
    $.ajax({type: 'POST',
            url: '/login/dragtable/', 
            data: table.sortOrder
            }); 
    } 
});
