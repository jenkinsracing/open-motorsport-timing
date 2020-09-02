var $table1 = $('#sitereportsTable');
var $table2 = $('#usersTable');

//handle uploading devices or ios file
function fileUpload(id){
    var data = new FormData();
    var input =  $('#' + id + 'File');
    var file = input[0].files[0];
    data.append("file", file);

    $.ajax({
       url : pid + '/' + id + 'upload/',
       type : 'POST',
       data : data,
       processData: false,  // tell jQuery not to process the data
       contentType: false,  // tell jQuery not to set contentType
       success : function(res) {
            $('#' + id + 'HelpBlock').text(res);  // not an object, plain text response
           console.log(res);

       },
       error: function (err, status) {
            $('#' + id + 'HelpBlock').text(err.responseText);
            console.log('AJAX post file failed');
       }
    });
    }

//handle project archiving
//see main.js

// handle site reports
function newSiteReport(){
    //var el = document.getElementById("cont-area");
    $.ajax(pid + '/sitereports/new').done(function (res) {
            $('#cont-area').html(res);
    });
    };

$table1.on('click-row.bs.table', function (e, field, row, $el) {
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

function scontrolFormatter(value, row, index) {
    if (row.current_role == 'Subscriber') {
        return '<i class="glyphicon glyphicon-remove text-muted"></i>'
    } else {
        return [
            '<a class="remove" href="javascript:void(0)" title="Remove">',
            '<i class="glyphicon glyphicon-remove"></i>',
            '</a>'
        ].join('');
        }
}

window.scontrolEvents = {
    'click .remove': function (e, value, row, index) {
        userRemoveRole(e, value, row, index);
    }
};

function userRemoveRole(e, value, row, index) {

    var data = {
        user_email : row.email
        }

    console.log('User Role Remove: remove pressed for email: ' + row.email);

    $.ajax({
           url : pid + '/api/users/',
           type : 'DELETE',
           data : data,
           success : function(res) {
            debugger;
               console.log(res);
                //refresh the table
                if (res === 'Success') {
                    $table2.bootstrapTable('remove', {field: 'email', values: [row.email]});
                    console.log('User Role Removed')

                } else {
                    console.log('User Role Remove: Unexpected AJAX response')
                }

           },
           error: function (err, status) {
                // something went wrong
                debugger;
                console.log('User Role Remove: AJAX delete failed');
           }
        });
    }

//handle adding users
$('#role-dropdown-menu > li').click(function(e){
  e.preventDefault();
  var selected = $(this).text();
  $('#role-dropdown-input').val(selected);
  $('#role-dropdown-display').text(selected);
});

$("#addUserForm").submit(function(e) {
    var data = $("#addUserForm").serialize();

    $.post(pid + '/api/users/', data, function (res) {
            console.log(res)
            // reset form
            clearUserForm();

            // refresh user table
            $('#usersTable').bootstrapTable('refresh')

            //feedback
            $('#addUserHelpBlock').text(res);


        }).fail(function(err, status) {
            // something went wrong
            // reset form
            // clearAddUserForm();

            //feedback
            $('#addUserHelpBlock').text(err.responseJSON);

            console.log('AJAX post to add user failed');
        });

    e.preventDefault(); // avoid to execute the actual submit of the form.
});

function clearUserForm(){
    $('#user-email-input').val("");
    $('#role-dropdown-display').text("Viewer");  // reset drop down
    $('#role-dropdown-input').val("Viewer");  // reset drop down
}

function initTable() {
    $table1.bootstrapTable();
    // TODO refactor this properly
    $table2.bootstrapTable();
}

// ************ CHART.JS*****************

window.chartColors = {
    red: 'rgb(255, 99, 132)',
    orange: 'rgb(255, 159, 64)',
    yellow: 'rgb(255, 205, 86)',
    green: 'rgb(75, 192, 192)',
    blue: 'rgb(54, 162, 235)',
    purple: 'rgb(153, 102, 255)',
    grey: 'rgb(201, 203, 207)'
};


function chartDevicesData() {
    $.get(pid + '/api/devices/stats/', function (res) {
            $devices_config.data.datasets[0].data = JSON.parse(res)
            window.myBar.update();
        });
    };

function chartDevicesActivityData() {
    $.get(pid + '/api/devices/stats/activity', function (res) {
            //myResponse = JSON.parse(res)
            $devices_activity_config.data.datasets[0].data = res[0]
            $devices_activity_config.data.datasets[1].data = res[1]
            $devices_activity_config.data.datasets[2].data = res[2]
            $devices_activity_config.data.datasets[3].data = res[3]
            $devices_activity_config.data.datasets[4].data = res[4]
            window.myBar3.update();
        });
    };

function chartIOsData() {
    $.get(pid + '/api/ios/stats/', function (res) {
            $ios_config.data.datasets[0].data = JSON.parse(res)
            window.myPie.update();
        });
    };

function chartIOsActivityData() {
    $.get(pid + '/api/ios/stats/activity', function (res) {
            //myResponse = JSON.parse(res)
            $ios_activity_config.data.datasets[0].data = res[0]
            $ios_activity_config.data.datasets[1].data = res[1]
            $ios_activity_config.data.datasets[2].data = res[2]
            window.myBar2.update();
        });
    };

var $devices_config = {
    type: 'bar',
    data: {
        datasets: [{
            data: [0,0,0,0,0],
            backgroundColor: window.chartColors.purple,
            label: 'Device Status'
        }],
        labels: [
            "Equipment",
            "Conduit",
            "Wires Pulled",
            "Field",
            "Panel"
        ]
    },
    options: {
        responsive: true,
        legend: {
            display: true,
            position: 'bottom'
        },
        scales: {
            yAxes: [{
                display: true,
                ticks: {
                    suggestedMin: 0,    // minimum will be 0, unless there is a lower value.
                    max: 100
                }
            }]
        }
    },

};

var $devices_activity_config = {
    type: 'bar',
    data: {
        datasets: [{
            label: 'Equipment',
            data: [0,0,0,0,0,0,0],
            backgroundColor: window.chartColors.grey
        },
        {
            label: 'Conduit',
            data: [0,0,0,0,0,0,0],
            backgroundColor: window.chartColors.blue
        },
        {
            label: 'Wire Pulled',
            data: [0,0,0,0,0,0,0],
            backgroundColor: window.chartColors.yellow
        },
        {
            label: 'Field Connected',
            data: [0,0,0,0,0,0,0],
            backgroundColor: window.chartColors.orange
        },
        {
            label: 'Panel Connected',
            data: [0,0,0,0,0,0,0],
            backgroundColor: window.chartColors.purple
        }],
        labels: [
            "6 days ago",
            "5 days ago",
            "4 days ago",
            "3 days ago",
            "2 days ago",
            "1 days ago",
            "Today"
        ]
    },
    options: {
        maintainAspectRatio: false,
        responsive: true,
        legend: {
            display: true,
            position: 'bottom'
        },
        scales: {
            yAxes: [{
                display: true,
                ticks: {
                    suggestedMax: 10,
                    suggestedMin: 0    // minimum will be 0, unless there is a lower value.
                    //stepSize: 1
                }
            }]
        }
    },

};

var $ios_config = {
    type: 'pie',
    data: {
        datasets: [{
            data: [0,0,0,0],
            backgroundColor: [
                window.chartColors.grey,
                window.chartColors.green,
                window.chartColors.orange,
                window.chartColors.red,
            ],
            label: 'IO Status'
        }],
        labels: [
            "Untested",
            "Done",
            "Repeat",
            "Removed"
        ]
    },
    options: {
        responsive: true,
        legend: {
            display: true,
            position: 'right'
        },
        tooltips: {
            callbacks: {
                label: function(tooltipItem, data) {
                    var allData = data.datasets[tooltipItem.datasetIndex].data;
                    var tooltipLabel = data.labels[tooltipItem.index];
                    var tooltipData = allData[tooltipItem.index];
                    var total = 0;
                    for (var i in allData) {
                        total += allData[i];
                    }
                    var tooltipPercentage = Math.round((tooltipData / total) * 100);
                    return tooltipLabel + ': ' + tooltipData + ' (' + tooltipPercentage + '%)';
                }
            }
        }
    }
};

var $ios_activity_config = {
    type: 'bar',
    data: {
        datasets: [{
            label: 'Set to Done',
            data: [0,0,0,0,0,0,0],
            backgroundColor: window.chartColors.green
        },
        {
            label: 'Set to Repeat',
            data: [0,0,0,0,0,0,0],
            backgroundColor: window.chartColors.orange
        },
        {
            label: 'Set to Removed',
            data: [0,0,0,0,0,0,0],
            backgroundColor: window.chartColors.red
        }],
        labels: [
            "6 days ago",
            "5 days ago",
            "4 days ago",
            "3 days ago",
            "2 days ago",
            "1 days ago",
            "Today"
        ]
    },
    options: {
        maintainAspectRatio: false,
        responsive: true,
        legend: {
            display: true,
            position: 'bottom'
        },
        scales: {
            yAxes: [{
                display: true,
                ticks: {
                    suggestedMax: 10,
                    suggestedMin: 0    // minimum will be 0, unless there is a lower value.
                    //stepSize: 1
                }
            }]
        }
    },

};

function getDeviceChart() {
    var ctx = document.getElementById("devices-chart-area").getContext("2d");
    window.myBar = new Chart(ctx, $devices_config);
    chartDevicesData();
};

function getDevicesActivityChart() {
    var ctx = document.getElementById("devices-activity-chart-area").getContext("2d");
    window.myBar3 = new Chart(ctx, $devices_activity_config);
    chartDevicesActivityData();
};

function getIOsChart() {
    var ctx = document.getElementById("ios-chart-area").getContext("2d");
    window.myPie = new Chart(ctx, $ios_config);
    chartIOsData();
};

function getIOsActivityChart() {
    var ctx = document.getElementById("ios-activity-chart-area").getContext("2d");
    window.myBar2 = new Chart(ctx, $ios_activity_config);
    chartIOsActivityData();
};

// ************ CHART.JS*****************

$(document).ready(function () {
    if (has_devices) {
        getDeviceChart();
        getDevicesActivityChart();
    }

    if (has_ios) {
        getIOsChart();
        getIOsActivityChart();
    }

    initTable();

    // control for file selector input fields
    $(':file').on('fileselect', function(event, numFiles, label) {
          var input = $(this).parents('.input-group').find(':text'),  // get a reference to the visible text field
              log = numFiles > 1 ? numFiles + ' files selected' : label;

          if( input.length ) {
              input.val(log);  // put the file name in the input field
          }
      });

});

// TODO MOVE THESE CHARTS INTO SEPARATE JS FILES FOR REUSE!!!!



