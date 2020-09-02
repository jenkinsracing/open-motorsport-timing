var $table = $('#table'),
    $mymodal = $('#myModal')


function initTable() {
    $table.bootstrapTable({
        height: getHeight(),
    });
}


$table.on('expand-row.bs.table', function (e, index, row, $detail) {
    var id = row.id;

    $detail.html('Loading...');

    $.get(pid + '/api/ios/' + id + '/logs/', function (res) {
        var menu = buildMenu(index, row);

        // always build the table even if we don't have any results so that it updates later
        buildTable($detail.html(menu + '<table id="logs' + index + '"></table>').find('table'), index, row, res);

    }).fail(function(err, status) {
        // something went wrong
        $detail.html('Error getting data');
        console.log('AJAX get failed');
    });
});


function rowStyle(row, index) {
    var classes = ['active', 'success', 'info', 'warning', 'danger'];

    if (row.status === 'Done') {
        return {
            classes: classes[1]
        };
    } else if (row.status === 'Repeat') {
        return {
            classes: classes[3]
        };
    } else if (row.status === 'Removed') {
        return {
            classes: classes[4]
        }
    }return {};
}


function haslogFormatter(value, row, index) {
    if (row.hasiolog){
        return '<i class="glyphicon glyphicon-pencil"></i>';
    } else {
        return '';
    }
}


function scontrolFormatter(value, row, index) {
    return [
        '<a class="done" href="javascript:void(0)" title="Done">',
        '<i class="glyphicon glyphicon-ok"></i>',
        '</a>       ',
        '<a class="repeat" href="javascript:void(0)" title="Repeat">',
        '<i class="glyphicon glyphicon-repeat"></i>',
        '</a>       ',
        '<a class="reset" href="javascript:void(0)" title="Reset">',
        '<i class="glyphicon glyphicon-retweet"></i>',
        '</a>&emsp;',
        '<a class="removed" href="javascript:void(0)" title="Removed">',
        '<i class="glyphicon glyphicon-remove"></i>',
        '</a>'
    ].join('');
}


window.scontrolEvents = {
    'click .done': function (e, value, row, index) {
        ioUpdate(e, value, row, index, 'Done');
    },
    'click .repeat': function (e, value, row, index) {
        ioUpdate(e, value, row, index, 'Repeat');
    },
    'click .reset': function (e, value, row, index) {
        ioUpdate(e, value, row, index, 'Reset');
    },
    'click .removed': function (e, value, row, index) {
        ioUpdate(e, value, row, index, 'Removed');
    }
};


function buildMenu(index, row) {
    return '<button type="button" class="btn btn-primary btn-default" onClick="openModal()" data-tindex="' + index + '" data-myid="' + row.id + '" data-mydev="' + row.device + '" >New Log Entry</button>'
}


function openModal() {
    var tindex = $(event.target).data('tindex');
    var myid = $(event.target).data('myid');
    var mydev = $(event.target).data('mydev');

    console.log('table index is: ' + tindex);

    $('#myModalLabel').text('Log Entry for ' + mydev);

    $mymodal.data('myid', myid);
    $mymodal.data('tindex', tindex);
    $mymodal.modal('show');
    console.log(myid);

    $('#tokenfield').tokenfield({
        autocomplete: {
            source: tags,
            delay: 100
        },
        showAutocompleteOnFocus: true

})

}

$( ".addresspicker" ).autocomplete( "option", "appendTo", ".eventInsForm" );

function buildTable($el, index, row, res) {
    var columns = [{
                    field: 'logmsg',
                    title: 'Message',
                }, {
                    field: 'user',
                    title: 'User',
                    sortable: true,
                }, {
                    field: 'tstamp',
                    title: 'Time',
                    sortable: true,
                }],
        data = res;

    $el.bootstrapTable({
        columns: columns,
        data: data
    });
}

// handle new IO item
function newIOItem(){
    //var el = document.getElementById("cont-area");
    $.ajax(pid + '/ios/new').done(function (res) {
            $('#cont-area').html(res);
    });
    };

function ioUpdate(e, value, row, index, status) {
    var id = row.id;
    var data = {
        status : status
        }

    console.log('IO Update: update pressed for id: ' + id);

    $.post(pid + '/api/ios/' + id + '/', data, function (res) {
        console.log(res)

        //refresh the table
        // FIXME refactor response so that timestamp and user also updates
        if (res === 'Success') {
            var value = status;
            if (value === 'Reset'){
            // FIXME conversion is also done on server, this transaction should be refactored to remove code duplication
                value = 'Untested';
            }

            $table.bootstrapTable('updateCellById', {id: id, field: "status", value: value})
                console.log('IO Update: Cell set to ' + value)

        } else {
            console.log('IO Update: Unexpected AJAX response')
        }

        //refresh chart
        chartIOsData();

    }).fail(function(err, status) {
        // something went wrong
        console.log('IO Update: AJAX post failed');
    });
    }


function logSave() {
    var tindex = $('#myModal').data('tindex');
    var id = $('#myModal').data('myid');
    var msg = $("#myModal #modalInput").val().trim();
    var tags = $('#tokenfield').tokenfield('getTokensList', ';', false);

    var data = {
        msg : msg,
        tags : tags
        }

    console.log('save pressed for id: ' + id);

    $.post(pid + '/api/ios/' + id + '/logs/', data, function (res) {
        console.log(res)
        // reset the modal and token input
        $('#modalInput').val("");
        $('#tokenfield').tokenfield('setTokens', []);

        //refresh the table
        $('#logs' + tindex).bootstrapTable('refresh', {url: pid + '/api/ios/' + id + '/logs/'});

    }).fail(function(err, status) {
        // something went wrong
        $('#modalInput').val("");
        console.log('AJAX post failed');
    });
    }


function getHeight() {
    return $(window).height() - $('h1').outerHeight(true);
}

$(document).ready(function () {

    initTable();

    // ************ CHART.JS*****************
    getIOsChart();
    // ************ CHART.JS*****************

    // for exporting
    $('#toolbar').find('select').change(function () {
        $table.bootstrapTable('destroy').bootstrapTable({
            exportDataType: $(this).val()
        });
    });
});

