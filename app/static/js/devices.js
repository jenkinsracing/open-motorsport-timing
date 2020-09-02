var $table = $('#table'),
    $mymodal = $('#myModal')


function initTable() {
    $table.bootstrapTable({
        height: getHeight(),
    });
}


$table.on('click-cell.bs.table', function (e, field, value, row, $el) { //remove double click cell for mobile support
    var valid = $.inArray(field, ['equipmentchk', 'conduitchk', 'wirepullchk', 'fieldconnectchk', 'panelconnectchk']);
    if ( valid >= 0 ) {

        var id = row.id;

        var data = {
            id: id,
            field : field
            }

        console.log('Device Update: Cell pressed for id: ' + id);

        $.post(pid + '/api/devices/' + id + '/', data, function (res) {
            console.log(res)

            //refresh the table cell
            // FIXME refactor response so that timestamp and user also updates
            if (res === 'True') {
                $table.bootstrapTable('updateCellById', {id: id, field: field, value: true})
                console.log('Device Update: Cell set to true')
            } else {
                $table.bootstrapTable('updateCellById', {id: id, field: field, value: false})
                console.log('Device Update: Cell set to false')
            }

            //refresh chart
            chartDevicesData();


        }).fail(function(err, status) {
            // something went wrong
            console.log('Device Update: AJAX post failed');
        });
    }
});


$table.on('expand-row.bs.table', function (e, index, row, $detail) {
    var id = row.id;

    $detail.html('Loading...');

    $.get(pid + '/api/devices/' + id + '/logs/', function (res) {
        var menu = buildMenu(index, row);

        // always build the table even if we don't have any results so that it updates later
        buildTable($detail.html(menu + '<table id="logs' + index + '"></table>').find('table'), index, row, res);

    }).fail(function(err, status) {
        // something went wrong
        $detail.html('Error getting data');
        console.log('Device Logs: AJAX get failed');
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
        };
    }return {};
}


function haslogFormatter(value, row, index) {
    if (row.hasdevicelog){
        return '<i class="glyphicon glyphicon-pencil"></i>';
    } else {
        return '';
    }
}

function cellStyle(value, row, index) {
    if (value) {
        return {
            classes: 'success'
        };
    }
    return {};
}

function equipmentchkFormatter(value, row, index) {
    return getCheckGlyph(row.equipmentchk);
}

function conduitchkFormatter(value, row, index) {
    return getCheckGlyph(row.conduitchk);
}

function wirepullchkFormatter(value, row, index) {
    return getCheckGlyph(row.wirepullchk);
}

function fieldconnectchkFormatter(value, row, index) {
    return getCheckGlyph(row.fieldconnectchk);
}

function panelconnectchkFormatter(value, row, index) {
    return getCheckGlyph(row.panelconnectchk);
}


function getCheckGlyph(value) {
    if (value){
        return '<div style="text-align:center"><i class="glyphicon glyphicon-ok" style="margin:auto"></i></div>';
    } else {
        return '<div style="text-align:center"><i class="glyphicon glyphicon-minus" style="margin:auto"></i></div>';
    }
}

function buildMenu(index, row) {
    return '<button type="button" class="btn btn-primary btn-default" onClick="openModal()" data-tindex="' + index + '" data-myid="' + row.id + '" data-mydev="' + row.device + '" >New Log Entry</button>';
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


// handle new Device item
function newDeviceItem(){
    $.ajax(pid + '/devices/new').done(function (res) {
            $('#cont-area').html(res);
    });
    };


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

    $.post(pid + '/api/devices/' + id + '/logs/', data, function (res) {
        console.log(res)
        // reset the modal input and token input
        $('#modalInput').val("");
        $('#tokenfield').tokenfield('setTokens', []);

        //refresh the table
        $('#logs' + tindex).bootstrapTable('refresh', {url: pid + '/api/devices/' + id + '/logs/'});

    }).fail(function(err, status) {
        // something went wrong
        $('#modalInput').val("");
        console.log('AJAX post failed');
    });
    }


function getHeight() {
    // TODO needs improvement, doesn't always work on small devices (like iPhone 6s)
    var heightDefault = 300;  // minimum height to ensure table is displayed on small screens (mobile)
    var heightCalc = $(window).height() - $('h1').outerHeight(true);
    if (heightCalc > heightDefault) {
        return heightCalc;
    } else {
        return heightDefault;
    }
}


$(document).ready(function () {

    initTable();

    // ************ CHART.JS*****************
    getDeviceChart();
    // ************ CHART.JS*****************

    // for exporting
    $('#toolbar').find('select').change(function () {
        $table.bootstrapTable('destroy').bootstrapTable({
            exportDataType: $(this).val()
        });
    });
});