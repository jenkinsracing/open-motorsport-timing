var $table = $('#sitereportsTable');


function initTable() {
    $table.bootstrapTable({
        height: getHeight(),
    });
}

// handle site reports
function newSiteReport(){
    //var el = document.getElementById("cont-area");
    $.ajax(pid + '/sitereports/new').done(function (res) {
            $('#cont-area').html(res);
    });
    };


$table.on('click-row.bs.table', function (e, field, row, $el) {
        var id = field.id;
        console.log('report pressed for id: ' + id);

        $.get(pid + '/sitereports/' + id + '/', function (res) {
            console.log(res)

            // replace the view with the selected site report
            $('#cont-area').html(res);


        }).fail(function(err, status) {
            // something went wrong
            console.log('AJAX post failed');
        });

});

function getHeight() {
    return $(window).height() - $('h1').outerHeight(true);
}


$(document).ready(function () {

    initTable();

});